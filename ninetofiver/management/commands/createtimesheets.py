from django.core.management.base import BaseCommand, CommandError
from django.core import management
from django.conf import settings


class Command(BaseCommand):

    """Create a new Timesheet for every active user"""

    args = ''
    help = 'Create a new Timesheet for every active user'

    def handle(self, *args, **options):
      """Create a new timesheet for the current month for each user."""
      from ninetofiver import models
      from django.contrib.auth import models as auth_models
      from datetime import datetime
      month = datetime.now().month
      year = datetime.now().year
      users = auth_models.User.objects.filter(is_active=True)
      for user in users:
          models.Timesheet.objects.get_or_create(
              user=user,
              month=month,
              year=year
          )
