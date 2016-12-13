"""ninetofiver serializers."""
from django.contrib.auth import models as auth_models
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.User
        fields = ('id', 'url', 'username', 'email', 'groups', 'first_name', 'last_name')
        read_only_fields = ('id', 'url')


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.Group
        fields = ('id', 'url', 'name')
        read_only_fields = ('id', 'url')


class BaseSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = ('id', 'url', 'created_at', 'updated_at', 'type')
        read_only_fields = ('id', 'url', 'created_at', 'updated_at', 'type')

    def validate(self, data):
        super().validate(data)
        self.Meta.model.perform_additional_validation(data, instance=self.instance)

        return data

    def get_type(self, obj):
        return obj.__class__.__name__


class RelatedSerializableField(serializers.RelatedField):
    def to_representation(self, value):
        serializer = value.get_default_serializer()
        return serializer(value, context={'request': None}).data
