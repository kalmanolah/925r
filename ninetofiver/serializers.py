"""ninetofiver serializers."""
from django.contrib.auth import models as auth_models
from rest_framework import serializers
from ninetofiver import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.User
        fields = ('id', 'username', 'email', 'groups', 'first_name', 'last_name')
        read_only_fields = ('id',)


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = auth_models.Group
        fields = ('id', 'name')
        read_only_fields = ('id',)


class BaseSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = ('id', 'created_at', 'updated_at', 'type')
        read_only_fields = ('id', 'created_at', 'updated_at', 'type')

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


class CompanySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Company
        fields = BaseSerializer.Meta.fields + ('name', 'country', 'vat_identification_number', 'internal', 'address')


class EmploymentContractSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.EmploymentContract
        fields = BaseSerializer.Meta.fields + ('user', 'company', 'work_schedule', 'started_at', 'ended_at')


class WorkScheduleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.WorkSchedule
        fields = BaseSerializer.Meta.fields + ('label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                                               'saturday', 'sunday')


class UserRelativeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.UserRelative
        fields = BaseSerializer.Meta.fields + ('name', 'relation', 'birth_date', 'gender', 'user')


class HolidaySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Holiday
        fields = BaseSerializer.Meta.fields + ('name', 'country', 'date')


class LeaveTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.LeaveType
        fields = BaseSerializer.Meta.fields + ('label',)


class LeaveSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Leave
        fields = BaseSerializer.Meta.fields + ('user', 'leave_type', 'status', 'description')


class LeaveDateSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.LeaveDate
        fields = BaseSerializer.Meta.fields + ('leave', 'starts_at', 'ends_at')


class PerformanceTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.PerformanceType
        fields = BaseSerializer.Meta.fields + ('label', 'description', 'multiplier')


class ContractSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Contract
        fields = BaseSerializer.Meta.fields + ('label', 'description', 'company', 'customer', 'performance_types',
                                               'active')


class ContractRoleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractRole
        fields = BaseSerializer.Meta.fields + ('label', 'description')


class ContractUserSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractUser
        fields = BaseSerializer.Meta.fields + ('user', 'contract', 'contract_role')
