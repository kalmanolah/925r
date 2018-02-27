"""Send staff a reminder about pending leaves."""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models
from ninetofiver.utils import send_mail


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send staff a reminder about pending leaves."""

    args = ''
    help = 'Send staff a reminder about pending leaves'

    def handle(self, *args, **options):
        """Send staff a reminder about pending leaves."""
        pending_leaves = models.Leave.objects.filter(status=models.STATUS_PENDING)
        pending_leave_count = pending_leaves.count()
        log.info('%s pending leave(s) found' % pending_leave_count)

        if pending_leave_count:
            staff = auth_models.User.objects.filter(is_staff=True, email__isnull=False)

            for user in staff:
                log.info('Sending reminder to %s' % user.email)

                send_mail(
                    user.email,
                    _('Pending leaves awaiting your approval'),
                    'ninetofiver/emails/pending_leave_reminder.txt',
                    context={
                        'user': user,
                        'pending_leave_count': pending_leave_count,
                    }
                )
