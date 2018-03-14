"""Redmine integration."""
import logging
import datetime
from redminelib import Redmine
from ninetofiver import models, settings


logger = logging.getLogger(__name__)


def get_redmine_connector():
    """Get a redmine connector."""
    url = settings.REDMINE_URL
    api_key = settings.REDMINE_API_KEY

    if url and api_key:
        return Redmine(url, key=api_key)

    return None


def get_redmine_project_choices():
    """Get redmine project choices."""
    choices = [[None, '-----------']]
    redmine = get_redmine_connector()

    if redmine:
        res = redmine.project.all()
        choices += [[x.id, x.name] for x in res]

    return choices


def get_user_redmine_id(user):
    """Get redmine user ID for the given user."""
    user_id = None

    if user.userinfo and user.userinfo.redmine_id:
        user_id = user.userinfo.redmine_id

    if (not user_id) and user.email:
        redmine = get_redmine_connector()

        if redmine:
            res = list(redmine.user.filter(name=user.username, limit=2))
            if len(res) == 1:
                user_id = res[0].id

    return user_id


def get_user_redmine_performances(user, from_date=None, to_date=None):
    """Get available Redmine performances for the given user."""
    data = []

    url = settings.REDMINE_URL
    redmine = get_redmine_connector()
    if not redmine:
        logger.debug('No base URL and API key provided for connecting to Redmine')
        return data

    user_id = get_user_redmine_id(user)
    if not user_id:
        logger.debug('No Redmine user ID found for user %s' % user.id)
        return data

    if not from_date:
        from_date = datetime.date.today()

    if not to_date:
        to_date = datetime.date.today()

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

        description = '_See [#%s](%s/issues/%s)._' % (entry.issue.id, url, entry.issue.id)
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
