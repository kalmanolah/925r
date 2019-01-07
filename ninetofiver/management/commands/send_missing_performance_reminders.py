"""Send a reminder about working days with missing performance."""
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
from ninetofiver.calculation import get_range_info


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """Send a reminder about working days with missing performance."""

    args = ''
    help = 'Send a reminder about working days with missing performance'

    def handle(self, *args, **options):
        """Send a reminder about working days with missing performance."""
        # Fetch all active users
        users = (auth_models.User.objects
                 .filter(is_active=True))
         
        # Get range info for all users for yesterday
        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        range_info = get_range_info(users, yesterday, yesterday)

        for user in users:
            user_range_info = range_info[user.id]

            if (not user_range_info['work_hours']) or (user_range_info['remaining_hours'] != user_range_info['work_hours']):
                log.info('User %s skipped because they were not required to log performance yesterday' % user)
                continue

            log.info('Sending reminder to %s' % user.email)

            if settings.MATTERMOST_INCOMING_WEBHOOK_URL and settings.MATTERMOST_PERFORMANCE_REMINDER_NOTIFICATION_ENABLED:
                try:
                    requests.post(settings.MATTERMOST_INCOMING_WEBHOOK_URL, json={
                        'channel': '@%s' % user.username,
                        'text': _('Hi there! It looks like you didn\'t log any performance yesterday. Did you forget to add something? Maybe you should take a look!'),
                    })
                except:
                    log.error('Could not send mattermost notification!', exc_info=True)

            if settings.ROCKETCHAT_INCOMING_WEBHOOK_URL and settings.ROCKETCHAT_PERFORMANCE_REMINDER_NOTIFICATION_ENABLED:
                try:
                    requests.post(settings.ROCKETCHAT_INCOMING_WEBHOOK_URL, json={
                        'channel': '@%s' % user.username,
                        'text': _('Hi there! It looks like you didn\'t log any performance yesterday. Did you forget to add something? Maybe you should take a look!'),
                    })
                except:
                    log.error('Could not send rocketchat notification!', exc_info=True)