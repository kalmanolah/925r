from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY
from redminelib import Redmine

REDMINE = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
projects = REDMINE.project.all()
users = REDMINE.user.all()

REDMINE_PROJECT_CHOICES = ((project['id'], project['name']) for project in projects)
REDMINE_USER_CHOICES = ((user['id'], user['login']) for user in users)
