"""Notifications."""
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models
from ninetofiver.utils import get_users_with_permission, send_mail



def send_attachments_modified_notification(attachments, action='added', timesheets=None, leaves=None):
    if not (timesheets or leaves):
        raise ValueError('Timesheets or leaves should be provided!')

    users = get_users_with_permission(models.PERMISSION_RECEIVE_MODIFIED_ATTACHMENT_NOTIFICATION)

    for user in users:
        if user.email:
            send_mail(
                user.email,
                _('Attachments modified'),
                'ninetofiver/emails/attachments_modified.pug',
                context={
                    'user': user,
                    'leaves': leaves,
                    'timesheets': timesheets,
                    'attachments': attachments,
                    'action': action,
                }
            )