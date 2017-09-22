import logging

from redminelib import Redmine
from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY
from django.contrib.auth import models as auth_models
from ninetofiver.models import Performance, Timesheet
from datetime import datetime
from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)

def get_redmine_user_time_entries(user_id, params):
    if REDMINE_URL and REDMINE_API_KEY:
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            redmine_time_entries = redmine.time_entry.filter(user_id=user_id)
            today = datetime.now()
            # Filter out time entries not in the current month.
            redmine_time_entries = list(filter(lambda x: x['spent_on'].month == int(today.month) or x['spent_on'].month == int(today.month - 1), redmine_time_entries))
            # Filter out time entries that are already imported.
            if params['filter_imported'] == 'true':
                redmine_time_entries = list(filter(lambda x: not Performance.objects.filter(redmine_id=x.id).first(), redmine_time_entries))
            return redmine_time_entries
        except ConnectionError:
            logger.debug('Tried to connect to redmine but failed.')
        except Exception as e:
            logger.debug('Something went wrong when trying to connect to redmine: ')
            logger.debug(e)
            raise Exception(e)
    return []
