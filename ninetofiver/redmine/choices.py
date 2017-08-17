import logging

from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY 
from redminelib import Redmine
from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)

def get_redmine_project_choices():
    if REDMINE_URL and REDMINE_API_KEY: 
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            projects = redmine.project.all()
            REDMINE_PROJECT_CHOICES = ((project['id'], project['name']) for project in projects)
            return REDMINE_PROJECT_CHOICES
        except ConnectionError:
            logger.debug('Tried to connect to redmine but failed.')
        except Exception as e:
            logger.debug('Something went wrong when trying to connect to redmine: ')
            logger.debug(e)
    return [('None', 'None')]

def get_redmine_user_choices():
    if REDMINE_URL and REDMINE_API_KEY: 
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            users = redmine.user.all()
            REDMINE_USER_CHOICES = ((user['id'], user['login']) for user in users)
            return REDMINE_USER_CHOICES
        except ConnectionError:
            logger.debug('Tried to connect to redmine but failed.')
        except Exception as e:
            logger.debug('Something went wrong when trying to connect to redmine: ')
            logger.debug(e)
    return [('None', 'None')]