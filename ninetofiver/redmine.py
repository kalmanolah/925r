"""Redmine integration."""
import logging
import datetime
from redminelib import Redmine
from ninetofiver import models, settings


logger = logging.getLogger(__name__)


def get_user_redmine_performances(user, from_date=None, to_date=None):
    """Get available Redmine performances for the given user."""
    data = []

    url = settings.REDMINE_URL
    api_key = settings.REDMINE_API_KEY
    if not (url and api_key):
        logger.debug('No base URL and API key provided for connecting to Redmine')
        return data

    user_id = user.userinfo.redmine_id if user.userinfo else None
    if not user_id:
        logger.debug('No Redmine user ID found for user %s' % user.id)
        return data

    if not from_date:
        from_date = datetime.date.today()

    if not to_date:
        to_date = datetime.date.today()

    redmine = Redmine(url, key=api_key)
    time_entries = redmine.time_entry.filter(from_date=from_date, to_date=to_date, user_id=user_id)

    # Construct a dict mapping redmine project IDs to a user's contract IDs
    contracts = models.Contract.objects.filter(contractuser__user=user, redmine_id__isnull=False)
    contracts = {str(x.redmine_id): x.id for x in contracts}

    # Construct a dict mapping redmine time entry IDs to a user's performance IDs
    time_entry_ids = [x.id for x in time_entries]
    performances = models.Performance.objects.filter(timesheet__user=user, redmine_id__in=time_entry_ids)
    performances = {str(x.redmine_id): x.id for x in performances}

    for entry in time_entries:
        performance_id = performances.get(str(entry.id), None)
        contract_id = contracts.get(str(entry.project.id), None)

        if not contract_id:
            logger.debug('No contract with Redmine project ID %s found' % entry.project.id)
            continue

        description = '###### _Imported from Redmine:_ %s/issues/%s.' % (url, entry.issue.id)
        if entry.comments:
            description = '%s\n%s' % (entry.comments, description)

        perf = {
            'id': performance_id,
            'contract': contract_id,
            'redmine_id': entry.id,
            'duration': entry.hours,
            'description': description,
            'date': entry.spent_on,
        }

        data.append(perf)

    return data
