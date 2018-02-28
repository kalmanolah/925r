"""Create timesheets."""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from ninetofiver import models


class Command(BaseCommand):
    """Create a new timesheet for the current month for each user."""

    args = ''
    help = 'Create a new Timesheet for every active user'

    def handle(self, *args, **options):
        """Create a new timesheet for the current month for each user."""
        month = datetime.datetime.now().month
        year = datetime.datetime.now().year
        users = auth_models.User.objects.filter(is_active=True)

        for user in users:
            models.Timesheet.objects.get_or_create(
                user=user,
                month=month,
                year=year
            )
