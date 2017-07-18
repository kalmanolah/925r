import logging

from redminelib import Redmine
from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY 
from ninetofiver.redmine import serializers
from rest_framework import viewsets, permissions, response
from requests.exceptions import ConnectionError

logger = logging.getLogger(__name__)


def get_redmine_time_entries():
    logging.info('in get redmine time entries')
    logging.info(REDMINE_URL)
    if REDMINE_URL and REDMINE_API_KEY:
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            return redmine.time_entry.all()
        except ConnectionError:
            logger.info('Tried to connect to redmine but failed.')
            return []
        except Exception as e:
            logger.info('Something went wrong when trying to connect to redmine: ')
            logger.info(e)
            return []
    else:
        return []

def get_redmine_user_time_entries(user_id):
    if REDMINE_URL and REDMINE_API_KEY:
        try:
            redmine = Redmine(REDMINE_URL, key=REDMINE_API_KEY)
            return redmine.time_entry.filter(user_id=user_id)
        except ConnectionError:
            print('Tried to connect to redmine but failed.')
            return []
        except Exception as e:
            print('Something went wrong when trying to connect to redmine: ')
            print(e)
            return []
    else:
        return []

class RedmineTimeEntryViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows redmine time entries to be viewed or edited
    """
    queryset = get_redmine_time_entries()
    serializer_class = serializers.RedmineTimeEntrySerializer
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request):
        time_entries = get_redmine_time_entries() 
        user_id = self.request.query_params.get('user_id', None)
        month = self.request.query_params.get('month', None)
        if user_id is not None and month is not None:
            # time_entries = REDMINE.time_entry.filter(user_id=user_id)
            time_entries = get_redmine_user_time_entries(user_id=user_id)
            # Only return the time entries of this month
            time_entries = list(filter(lambda x: x['spent_on'].month == int(month), time_entries))

        serializer = serializers.RedmineTimeEntrySerializer(
            instance=time_entries, many=True)
        return response.Response(serializer.data)