"""Signals."""
from django_auth_ldap.backend import populate_user
from django.contrib.auth import models as auth_models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, m2m_changed, pre_delete
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models, notifications
from ninetofiver.utils import send_mail, get_users_with_permission


@receiver(populate_user)
def on_populate_user(sender, **kwargs):
    """Process population of a user."""
    user = kwargs.get('user', None)
    ldap_user = kwargs.get('ldap_user', None)

    if not (user and ldap_user):
        return

    # If the user has a zimbra status and it's not enabled,
    # disable the account
    try:
        zimbra_status = ldap_user.attrs['zimbramailstatus'][0]
    except (KeyError, AttributeError, IndexError):
        zimbra_status = None

    if zimbra_status is not None:
        user.is_active = zimbra_status == 'enabled'

    # Since we're populating from LDAP, disable regular password
    user.set_unusable_password()


@receiver(post_save, sender=auth_models.User)
def on_user_post_save(sender, instance, created=False, **kwargs):
    """Process post-save event for a user."""
    if created:
        user_info = models.UserInfo(user=instance)
        user_info.save()


@receiver(pre_save, sender=models.Leave)
def on_leave_pre_save(sender, instance, created=False, **kwargs):
    """Process pre-save event for a leave."""
    if (not created) and instance.is_dirty():
        dirty = instance.get_dirty_fields()

        old_status = dirty.get('status', None)
        new_status = instance.status
        statuses = [models.STATUS_APPROVED, models.STATUS_REJECTED]

        if (old_status != new_status) and (new_status in statuses):
            if instance.user.email:
                send_mail(
                    instance.user.email,
                    _('Leave status updated: %(status)s') % {'status': instance.status},
                    'ninetofiver/emails/leave_status_updated.pug',
                    context={
                        'user': instance.user,
                        'leave': instance,
                    }
                )


@receiver(pre_save, sender=models.Timesheet)
def on_timesheet_pre_save(sender, instance, created=False, **kwargs):
    """Process pre-save event for a timesheet."""
    if (not created) and instance.is_dirty():
        dirty = instance.get_dirty_fields()

        old_status = dirty.get('status', None)
        new_status = instance.status
        old_statuses = [models.STATUS_PENDING]
        new_statuses = [models.STATUS_ACTIVE]

        if (old_status != new_status) and (old_status in old_statuses) and (new_status in new_statuses):
            if instance.user.email:
                send_mail(
                    instance.user.email,
                    _('Timesheet status updated: %(status)s') % {'status': instance.status},
                    'ninetofiver/emails/timesheet_status_updated.pug',
                    context={
                        'user': instance.user,
                        'timesheet': instance,
                    }
                )


@receiver(pre_save, sender=models.ContractUserGroup)
def on_contract_user_group_pre_save(sender, instance, created=False, **kwargs):
    """Process pre-save event for a contract user group."""
    # If this contract user group is being updated and the group has changed, delete all old contract users
    group = instance.group
    contract_role = instance.contract_role

    old_group = None
    old_contract_role = None

    if (not created) and instance.is_dirty(check_relationship=True):
        dirty = instance.get_dirty_fields(check_relationship=True)
        old_group = auth_models.Group.objects.get(pk=dirty['group']) if dirty.get('group', None) else None
        old_contract_role = (models.ContractRole.objects.get(pk=dirty['contract_role'])
                             if dirty.get('contract_role', None) else None)

    # If the group or the role has changed, delete all old contract users
    if ((old_group) and (group != old_group)) or ((old_contract_role) and (contract_role != old_contract_role)):
        [x.delete() for x in instance.contractuser_set.all()]

        # If we deleted contract users we may need to add other ones from other contract user groups again,
        # so trigger a save event for all other contract user groups
        other_contract_user_groups = instance.contract.contractusergroup_set.all()
        if instance.pk:
            other_contract_user_groups = other_contract_user_groups.exclude(pk=instance.pk)
        for contract_user_group in other_contract_user_groups:
            contract_user_group.save()


@receiver(pre_delete, sender=models.ContractUserGroup)
def on_contract_user_group_pre_delete(sender, instance, **kwargs):
    """Process pre-delete event for a contract user group."""
    # If we deleted contract users we may need to add other ones from other contract user groups again,
    # so trigger a save event for all other contract user groups
    other_contract_user_groups = instance.contract.contractusergroup_set.all().exclude(pk=instance.pk)
    for contract_user_group in other_contract_user_groups:
        contract_user_group.save()


@receiver(post_save, sender=models.ContractUserGroup)
def on_contract_user_group_post_save(sender, instance, created=False, **kwargs):
    # Create/update contract users for all users in the group with the given role for the given contract
    for user in instance.group.user_set.all():
        contract_user, created = models.ContractUser.objects.get_or_create(contract=instance.contract,
                                                                           contract_role=instance.contract_role,
                                                                           user=user)
        contract_user.contract_user_group = instance
        contract_user.save()


@receiver(m2m_changed, sender=auth_models.User.groups.through)
def on_user_groups_m2m_changed(sender, instance, action, **kwargs):
    # Determine users/groups
    users = ([instance] if instance.__class__ == auth_models.User
             else auth_models.User.objects.filter(id__in=kwargs['pk_set']))
    groups = ([instance] if instance.__class__ == auth_models.Group
              else auth_models.Group.objects.filter(id__in=kwargs['pk_set']))

    # Determine contract user groups for these groups
    contract_user_groups = models.ContractUserGroup.objects.filter(group__in=groups)

    # If users were removed from groups, delete contract users
    if action == 'pre_remove':
        contract_users = models.ContractUser.objects.filter(contract_user_group__in=contract_user_groups,
                                                            user__in=users)
        [x.delete() for x in contract_users]

    # If users were added to groups, create contract users
    elif action == 'pre_add':
        for user in users:
            for contract_user_group in contract_user_groups:
                contract_user, created = (models.ContractUser.objects
                                          .get_or_create(contract=contract_user_group.contract,
                                                         contract_role=contract_user_group.contract_role,
                                                         user=user))
                contract_user.contract_user_group = contract_user_group
                contract_user.save()


@receiver(m2m_changed, sender=models.Timesheet.attachments.through)
def on_timesheet_attachments_m2m_changed(sender, instance, action, **kwargs):
    timesheets = ([instance] if instance.__class__ == models.Timesheet
                  else models.Timesheet.objects.filter(id__in=kwargs['pk_set']))
    attachments = ([instance] if instance.__class__ == models.Attachment
                   else models.Attachment.objects.filter(id__in=kwargs['pk_set']))

    if len(attachments):
        if action in ['pre_remove', 'pre_add']:
            action = ('added' if (action == 'pre_add') else 'removed')
            notifications.send_attachments_modified_notification(attachments=attachments, action=action,
                                                                 timesheets=timesheets)


@receiver(m2m_changed, sender=models.Leave.attachments.through)
def on_leave_attachments_m2m_changed(sender, instance, action, **kwargs):
    leaves = ([instance] if instance.__class__ == models.Leave
              else models.Leave.objects.filter(id__in=kwargs['pk_set']))
    attachments = ([instance] if instance.__class__ == models.Attachment
                   else models.Attachment.objects.filter(id__in=kwargs['pk_set']))

    if len(attachments):
        if action in ['pre_remove', 'pre_add']:
            action = ('added' if (action == 'pre_add') else 'removed')
            notifications.send_attachments_modified_notification(attachments=attachments, action=action,
                                                                 leaves=leaves)


@receiver(pre_delete, sender=models.Attachment)
def on_attachment_pre_delete(sender, instance, **kwargs):
    """Process pre-delete event for an attachment."""
    timesheets = list(instance.timesheet_set.all())
    leaves = list(instance.leave_set.all())

    if timesheets or leaves:
        notifications.send_attachments_modified_notification(attachments=[instance], action='removed',
                                                             timesheets=timesheets, leaves=leaves)