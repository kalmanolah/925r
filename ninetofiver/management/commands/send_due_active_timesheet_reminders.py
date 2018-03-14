"""Send a reminder about due active timesheets."""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from django.db.models import Q
import calendar
import datetime
from dateutil.relativedelta import relativedelta
from ninetofiver import models
from ninetofiver.utils import send_mail

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send a reminder about due active timesheets."""

    args = ''
    help = 'Send a reminder about due active timesheets'

    def handle(self, *args, **options):
        """Send a reminder about due active timesheets."""
        # Determine month and year to use when looking for due timesheets
        date = datetime.date.today()

        # If today is not yet on or past the last weekday of the month, subtract 1 month
        last_weekday = date.replace(day=calendar.monthrange(date.year, date.month)[1])
        weekday_offset = last_weekday.weekday() - 4
        last_weekday -= datetime.timedelta(days=weekday_offset if weekday_offset > 0 else 0)

        if date < last_weekday:
            date -= relativedelta(months=1)

        due_active_timesheets = (models.Timesheet.objects
                                 .filter(Q(year__lte=date.year - 1) | Q(year=date.year, month__lte=date.month),
                                         status=models.STATUS_ACTIVE)
                                 .exclude(user__email__isnull=True)
                                 .exclude(user__email__exact=''))
        due_active_timesheet_count = due_active_timesheets.count()
        log.info('%s due active timesheet(s) found' % due_active_timesheet_count)

        if due_active_timesheet_count:
            user_timesheets = {}
            users = {}

            for timesheet in due_active_timesheets:
                users[timesheet.user.id] = timesheet.user
                user_timesheets.setdefault(timesheet.user.id, []).append(timesheet)

            for user in users.values():
                log.info('Sending reminder to %s' % user.email)
                timesheets = user_timesheets[user.id]

                send_mail(
                    user.email,
                    _('Your timesheet is due for submission'),
                    'ninetofiver/emails/due_active_timesheet_reminder.pug',
                    context={
                        'user': user,
                        'timesheets': timesheets,
                        'timesheet_count': len(timesheets),
                    }
                )
