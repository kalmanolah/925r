from django.core.management.base import BaseCommand, CommandError
import django.core.management.commands.test
from django.core import management
from django.conf import settings


class Command(django.core.management.commands.test.Command):

    """Taken from https://stackoverflow.com/a/22786635."""

    args = ''
    help = 'Test all of NINETOFIVER_APPS'

    def handle(self, *args, **options):
        super().handle(*(tuple(settings.NINETOFIVER_APPS) + args), **options)
