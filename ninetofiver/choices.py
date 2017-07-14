from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY
from redminelib import Redmine
from requests.exceptions import ConnectionError


def get_redmine_project_choices():
    if REDMINE_URL is not '' and REDMINE_API_KEY is not '': 
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            projects = redmine.project.all()
            REDMINE_PROJECT_CHOICES = ((project['id'], project['name']) for project in projects)
            return REDMINE_PROJECT_CHOICES
        except ConnectionError:
            print('Tried to connect to redmine but failed.')
            return []
        except Exception as e:
            print('Somethiig went wrong when trying to connect to redmine: ')
            print(e)
            return []
    else:
        return []

def get_redmine_user_choices():
    if REDMINE_URL is not '' and REDMINE_API_KEY is not '':
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            users = redmine.user.all()
            REDMINE_USER_CHOICES = ((user['id'], user['login']) for user in users)
            return REDMINE_USER_CHOICES
        except ConnectionError:
            print('Tried to connect to redmine but failed.')
            return []
        except Exception as e:
            print('Something went wrong when trying to connect to redmine: ')
            print(e)
            return []
    else:
        return []