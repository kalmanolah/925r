"""Signals."""
from django_auth_ldap.backend import populate_user
from django.contrib.auth import models as auth_models
from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models
from ninetofiver.utils import send_mail


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

    # Since we're populating from LDAP, disable regular regular password
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
                    'ninetofiver/emails/leave_status_updated.txt',
                    context={
                        'user': instance.user,
                        'leave': instance,
                    }
                )
