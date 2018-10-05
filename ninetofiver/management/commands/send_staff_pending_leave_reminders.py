"""Send staff a reminder about pending leaves."""
import logging
from django.db.models import Q
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models
from ninetofiver.utils import send_mail, get_users_with_permission


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send staff a reminder about pending leave."""

    args = ''
    help = 'Send staff a reminder about pending leave'

    def handle(self, *args, **options):
        """Send staff a reminder about pending leave."""
        pending_leaves = models.Leave.objects.filter(status=models.STATUS_PENDING)
        pending_leave_count = pending_leaves.count()
        log.info('%s pending leave(s) found' % pending_leave_count)

        if pending_leave_count:
            users = get_users_with_permission(models.PERMISSION_RECEIVE_PENDING_LEAVE_REMINDER)

            for user in users:
                if user.email:
                    log.info('Sending reminder to %s' % user.email)

                    send_mail(
                        user.email,
                        _('Pending leave awaiting your approval'),
                        'ninetofiver/emails/pending_leave_reminder.pug',
                        context={
                            'user': user,
                            'leaves': pending_leaves,
                            'leave_ids': ','.join([str(x.id) for x in pending_leaves]),
                            'leave_count': pending_leave_count,
                        }
                    )
