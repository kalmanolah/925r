from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from aiohttp import web
from aiohttp_wsgi import WSGIHandler
from ninetofiver.wsgi import application


class Command(BaseCommand):
    help = 'Runs a production server using asyncio'

    # def add_arguments(self, parser):
    #     parser.add_argument('poll_id', nargs='+', type=int)

    def add_arguments(self, parser):
        parser.add_argument(
            'port', nargs='?',
            default=8000,
            help='Optional port number, or ipaddr:port'
        )

        parser.add_argument(
            'host', nargs='?',
            default='127.0.0.1',
            help='Optional port number, or ipaddr:port'
        )

    def handle(self, *args, **options):
        wsgi_handler = WSGIHandler(application)
        app = web.Application()
        app.router.add_static(settings.STATIC_URL, settings.STATIC_ROOT)
        app.router.add_route("*", "/{path_info:.*}", wsgi_handler)
        web.run_app(app, host=options['host'], port=options['port'])
