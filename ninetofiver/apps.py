from django.apps import AppConfig


class NineToFiverConfig(AppConfig):
    name = 'ninetofiver'

    def ready(self):
        import ninetofiver.signals # noqa


class RedmineConfig(AppConfig):
    name = 'redmine'
