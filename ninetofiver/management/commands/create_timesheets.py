"""Create timesheets."""
import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import models as auth_models
from dateutil.relativedelta import relativedelta
from ninetofiver import models


class Command(BaseCommand):
    """Create a new timesheet for the current month for each user."""

    args = ''
    help = 'Create a new Timesheet for every active user'

    def handle(self, *args, **options):
        """Create a new timesheet for the current month for each user."""
        today = datetime.date.today()
        next_month = datetime.date.today() + relativedelta(months=1)
        users = auth_models.User.objects.filter(is_active=True)

        for user in users:
            # Ensure timesheet for this month exists
            models.Timesheet.objects.get_or_create(
                user=user,
                month=today.month,
                year=today.year
            )

            # Ensure timesheet for next month exists
            models.Timesheet.objects.get_or_create(
                user=user,
                month=next_month.month,
                year=next_month.year
            )
