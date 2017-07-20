from rest_framework import serializers
from rest_framework.fields import SkipField
from collections import OrderedDict
import timestring

class RedmineAttributeSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    name = serializers.CharField(max_length=255)

class RedmineTimeEntryIssueSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)


class RedmineTimeEntrySerializer(serializers.Serializer):
    id = serializers.CharField(max_length=255)
    issue = serializers.CharField(max_length=255)
    user = RedmineAttributeSerializer()
    activity = RedmineAttributeSerializer()
    project = RedmineAttributeSerializer()
    issue = RedmineTimeEntryIssueSerializer()
    hours = serializers.CharField(max_length=255)
    spent_on = serializers.CharField(max_length=255)
    created_on = serializers.CharField(max_length=255)
    updated_on = serializers.CharField(max_length=255)
    comments = serializers.CharField(max_length=255 )

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = [field for field in self.fields.values() if not field.write_only]

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
                # attribute = getattr(instance, field, None)
            except SkipField:
                continue
            except Exception:
                continue


            if attribute is not None:
                representation = field.to_representation(attribute)
                if representation is None or representation is '':
                    # Do not seralize empty objects
                    representation = ''
                if isinstance(representation, list) and not representation:
                   # Do not serialize empty lists
                    continue
                ret[field.field_name] = representation
            else:
                continue
        # ret = {
        #     'day': timestring.Date(ret['spent_on']).day,
        #     'duration': ret['hours'],
        #     'description': ret['comments'],
        #     'id': int(ret['id']),
        #     'source': 'redmine',
        #     'project_id': int(ret['project']['id']),
        #     'activity': ret['activity']['name'],
        # }
        return ret