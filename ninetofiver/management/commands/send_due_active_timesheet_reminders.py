"""Send a reminder about due active timesheets."""
import logging
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext as _
from django.db.models import Q
import calendar
import datetime
import requests
from dateutil.relativedelta import relativedelta
from ninetofiver import models, settings
from ninetofiver.utils import send_mail


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send a reminder about due active timesheets."""

    args = ''
    help = 'Send a reminder about due active timesheets'

    def handle(self, *args, **options):
        """Send a reminder about due active timesheets."""
        # Determine month and year to use when looking for due timesheets
        today = datetime.date.today()
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
                # Skip user if they don't have an active employment contract
                employment_contract = (models.EmploymentContract.objects
                                       .filter(Q(ended_at__isnull=True) | Q(ended_at__gte=today), user=user,
                                               started_at__lte=today)
                                       .first())
                if not employment_contract:
                    log.info('User %s skipped because they have no active employment contract' % user)
                    continue

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

                if settings.MATTERMOST_INCOMING_WEBHOOK_URL and settings.MATTERMOST_TIMESHEET_REMINDER_NOTIFICATION_ENABLED:
                    try:
                        requests.post(settings.MATTERMOST_INCOMING_WEBHOOK_URL, json={
                            'channel': '@%s' % user.username,
                            'text': _('Hey there! Did you know you have %(timesheet_count)s active timesheet(s) due for submission? Please review and submit them soon!') % {'timesheet_count': len(timesheets)},
                        })
                    except:
                        log.error('Could not send mattermost notification!', exc_info=True)


                if settings.ROCKETCHAT_INCOMING_WEBHOOK_URL and settings.ROCKETCHAT_TIMESHEET_REMINDER_NOTIFICATION_ENABLED:
                    try:
                        requests.post(settings.ROCKETCHAT_INCOMING_WEBHOOK_URL, json={
                            'channel': '@%s' % user.username,
                            'text': _('Hey there! Did you know you have %(timesheet_count)s active timesheet(s) due for submission? Please review and submit them soon!') % {'timesheet_count': len(timesheets)},
                        })
                    except:
                        log.error('Could not send rocketchat notification!', exc_info=True)