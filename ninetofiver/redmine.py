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


def get_redmine_user_choices():
    """Get redmine project choices."""
    choices = [[None, '-----------']]
    redmine = get_redmine_connector()

    if redmine:
        res = redmine.user.all()
        choices += sorted([[x.id, '%s %s [%s, %s]' % (x.firstname, x.lastname, x.login, x.mail)] for x in res],
                          key=lambda x: x[1].lower())

    return choices


def get_redmine_project_choices():
    """Get redmine project choices."""
    choices = [[None, '-----------']]
    redmine = get_redmine_connector()

    if redmine:
        res = redmine.project.all()
        choices += sorted([[x.id, x.name] for x in res], key=lambda x: x[1].lower())

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

    contract_field = settings.REDMINE_ISSUE_CONTRACT_FIELD
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

    time_entries = list(redmine.time_entry.filter(from_date=from_date, to_date=to_date, user_id=user_id))
    # If we have no time entries, return early
    if not time_entries:
        return data

    # Fetch a list of redmine project IDs and contract ID for the user
    contracts = (models.Contract.objects
                 .filter(contractuser__user=user)
                 .values('redmine_id', 'id'))
    contract_ids = [x['id'] for x in contracts]
    # Contract a dict mapping redmine project IDs to a user's contract IDs
    redmine_contracts = {str(x['redmine_id']): x['id'] for x in contracts}

    # Construct a dict mapping redmine time entry IDs to a user's performance IDs
    time_entry_ids = [x.id for x in time_entries]
    redmine_performances = (models.Performance.objects
                            .filter(timesheet__user=user, redmine_id__in=time_entry_ids)
                            .values('redmine_id', 'id'))
    redmine_performances = {str(x['redmine_id']): x['id'] for x in redmine_performances}

    for entry in time_entries:
        performance_id = redmine_performances.get(str(entry.id), None)

        # The contract ID for the given time entry is determined by:
        # * Looking for a custom field value which is part of the user's contract list
        # * Looking for a redmine project ID which maps to one of the user's contracts
        contract_id = None
        if getattr(entry, 'issue', None):
            issue = redmine.issue.get(entry.issue.id)
            for custom_field in getattr(issue, 'custom_fields', []):
                if (custom_field.name == contract_field):
                    if (custom_field.value):
                        custom_field_value = custom_field.value.split('|')[0]
                        contract_id = int(custom_field_value)
                    break

        if not contract_id:
            contract_id = redmine_contracts.get(str(entry.project.id), None)

        if (not contract_id) or (contract_id not in contract_ids):
            logger.debug('No contract found for Redmine time entry with ID %s' % entry.id)
            continue

        if getattr(entry, 'issue', None):
            description = '_See [#%s](%s/issues/%s)._' % (entry.issue.id, url, entry.issue.id)
        else:
            description = '_No issue linked._'
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
