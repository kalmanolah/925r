"""ninetofiver serializers."""
from django.contrib.auth import models as auth_models
from ninetofiver import models
from rest_framework import serializers
import logging
from collections import OrderedDict

from rest_framework.fields import SkipField


class UserSerializer(serializers.ModelSerializer):
    display_label = serializers.SerializerMethodField()

    country = serializers.CharField(source='userinfo.country')
    gender = serializers.CharField(source='userinfo.gender')
    birth_date = serializers.CharField(source='userinfo.birth_date')
    join_date = serializers.CharField(source='userinfo.join_date')
    redmine_id = serializers.CharField(source='userinfo.redmine_id')
    
    class Meta:
        model = auth_models.User
        fields = ('id', 'username', 'email', 'groups', 'first_name', 'last_name', 'display_label', 'is_active', 'country', 'gender', 'birth_date', 'join_date', 'redmine_id')
        read_only_fields = ('id', 'username', 'email', 'groups', 'first_name', 'last_name', 'display_label', 'is_active', 'country', 'gender', 'birth_date', 'join_date', 'redmine_id')

    def get_display_label(self, obj):
        return str(obj)


class GroupSerializer(serializers.ModelSerializer):
    display_label = serializers.SerializerMethodField()

    class Meta:
        model = auth_models.Group
        fields = ('id', 'name', 'display_label')
        read_only_fields = ('id',)

    def get_display_label(self, obj):
        return str(obj)


class BaseSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    display_label = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = ('id', 'created_at', 'updated_at', 'type', 'display_label')
        read_only_fields = ('id', 'created_at', 'updated_at', 'type', 'display_label')

    def validate(self, data):
        super().validate(data)
        self.Meta.model.perform_additional_validation(data, instance=self.instance)

        return data

    def get_type(self, obj):
        return obj.__class__.__name__

    def get_display_label(self, obj):
        return str(obj)


# class RelatedSerializableField(serializers.RelatedField):
#     def to_representation(self, value):
#         serializer = value.get_default_serializer()
#         return serializer(value, context={'request': None}).data


class LeaveRequestSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.LeaveDate
        fields = BaseSerializer.Meta.fields + ('leave', 'starts_at', 'ends_at')
        
    def validate(self, data):
        """ Does nothing (rip) because validation is handled before this gets called
        The view handles a .full_clean() to force validation BEFORE save, instead of after
        Save after (here) would generate ridiculous duplicate-errors """
        return data

    def get_type(self, obj):
        """ Object is an ordered list, only way to get the class name 'relatively clean' """
        return self.Meta.model.__name__

    def get_display_label(self, obj):
        """ Repeats the __str__ method from models.LeaveDate, because the obj is an orderedlist & can't reach it """
        return '%s - %s' % (dict(obj)['starts_at'].strftime('%Y-%m-%d %H:%M:%S'), dict(obj)['ends_at'].strftime('%Y-%m-%d %H:%M:%S'))


class CompanySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Company
        fields = BaseSerializer.Meta.fields + ('vat_identification_number', 'name', 'address', 'country', 'internal', )


class EmploymentContractTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.EmploymentContractType
        fields = BaseSerializer.Meta.fields + ('label',)


class EmploymentContractSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.EmploymentContract
        fields = BaseSerializer.Meta.fields + ('user', 'company', 'employment_contract_type', 'work_schedule',
                                               'started_at', 'ended_at')


class WorkScheduleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.WorkSchedule
        fields = BaseSerializer.Meta.fields + ('label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                                               'saturday', 'sunday')


class UserRelativeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.UserRelative
        fields = BaseSerializer.Meta.fields + ('name', 'relation', 'birth_date', 'gender', 'user')


class UserInfoSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.UserInfo
        fields = BaseSerializer.Meta.fields + ('birth_date', 'gender', 'country', 'user', 'join_date')


class AttachmentSerializer(BaseSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.Attachment
        fields = BaseSerializer.Meta.fields + ('label', 'description', 'file', 'slug', 'user', 'file_url')
        read_only_fields = BaseSerializer.Meta.read_only_fields + ('file_url',)

    def get_file_url(self, obj):
        return obj.get_file_url()


class HolidaySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Holiday
        fields = BaseSerializer.Meta.fields + ('name', 'country', 'date')


class LeaveTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.LeaveType
        fields = BaseSerializer.Meta.fields + ('label',)


class LeaveDateSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.LeaveDate
        fields = BaseSerializer.Meta.fields + ('leave', 'timesheet', 'starts_at', 'ends_at')


class LeaveSerializer(BaseSerializer):
    leavedate_set = LeaveDateSerializer(many=True, read_only=True)

    class Meta(BaseSerializer.Meta):
        model = models.Leave
        fields = BaseSerializer.Meta.fields + ('user', 'leave_type', 'leavedate_set', 'status', 'attachments',
                                               'description')


class PerformanceTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.PerformanceType
        fields = BaseSerializer.Meta.fields + ('label', 'description', 'multiplier')


class ContractSerializer(BaseSerializer):
    hours_spent = serializers.SerializerMethodField()

    def get_hours_spent(self, obj):
        total = 0
        for hours in models.ActivityPerformance.objects.filter(contract=obj.id):
            total += hours.duration
        return total

    class Meta(BaseSerializer.Meta):
        model = models.Contract
        fields = BaseSerializer.Meta.fields + ('label', 'description', 'company', 'customer', 'performance_types',
                                               'active', 'contract_groups', 'hours_spent', 'attachments')


class ProjectContractSerializer(ContractSerializer):
    hours_estimated = serializers.SerializerMethodField()

    def get_hours_estimated(self, obj):
        return obj.projectestimate_set.values_list('hours_estimated', 'role_id',)


    class Meta(ContractSerializer.Meta):
        model = models.ProjectContract
        fields = ContractSerializer.Meta.fields + ('redmine_id', 'starts_at', 'ends_at', 'fixed_fee', 'hours_estimated',)
        

class ConsultancyContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        model = models.ConsultancyContract
        fields = ContractSerializer.Meta.fields + ('starts_at', 'ends_at', 'day_rate', 'duration')


class SupportContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        model = models.SupportContract
        fields = ContractSerializer.Meta.fields + ('starts_at', 'ends_at', 'day_rate', 'fixed_fee', 'fixed_fee_period')


class ContractRoleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractRole
        fields = BaseSerializer.Meta.fields + ('label', 'description')


class ContractUserSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractUser
        fields = BaseSerializer.Meta.fields + ('user', 'contract', 'contract_role')


class ContractGroupSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractGroup
        fields = BaseSerializer.Meta.fields + ('label', )


class ProjectEstimateSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ProjectEstimate
        fields = BaseSerializer.Meta.fields + ('role', 'project', 'hours_estimated')


class TimesheetSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Timesheet
        fields = BaseSerializer.Meta.fields + ('user', 'year', 'month', 'status')


class WhereaboutSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Whereabout
        fields = BaseSerializer.Meta.fields + ('timesheet', 'day', 'location')

class PerformanceSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Performance
        fields = BaseSerializer.Meta.fields + ('timesheet', 'day', 'redmine_id')


class ActivityPerformanceSerializer(PerformanceSerializer):
    class Meta(PerformanceSerializer.Meta):
        model = models.ActivityPerformance
        fields = PerformanceSerializer.Meta.fields + ('duration', 'description', 'performance_type', 'contract', 'contract_role')


class StandbyPerformanceSerializer(PerformanceSerializer):
    class Meta(PerformanceSerializer.Meta):
        model = models.StandbyPerformance
        fields = PerformanceSerializer.Meta.fields


class MyUserSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_staff', 'is_superuser', 'user_permissions')
        depth = 2


class MyLeaveSerializer(LeaveSerializer):
    status = serializers.ChoiceField(choices=(models.Leave.STATUS.DRAFT, models.Leave.STATUS.PENDING))

    class Meta(LeaveSerializer.Meta):
        read_only_fields = LeaveSerializer.Meta.read_only_fields + ('user',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MyLeaveDateSerializer(LeaveDateSerializer):
    def validate_leave(self, value):
        if value.status != models.Leave.STATUS.DRAFT:
            raise serializers.ValidationError('You can only manipulate leave dates attached to draft leaves')

        if value.user != self.context['request'].user:
            raise serializers.ValidationError('You can only manipulate leave dates attached to your own leaves')

        return value


class MyTimesheetSerializer(TimesheetSerializer):
    class Meta(TimesheetSerializer.Meta):
        read_only_fields = TimesheetSerializer.Meta.read_only_fields + ('user', )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MyContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        read_only_fields = ContractSerializer.Meta.read_only_fields + ('user', )


class MyPerformanceSerializer(PerformanceSerializer):
    def validate_timesheet(self, value):
        if value.user != self.context['request'].user:
            raise serializers.ValidationError('You can only manipulate performances attached to your own timesheets')

        return value


class MyActivityPerformanceSerializer(MyPerformanceSerializer, ActivityPerformanceSerializer):
    class Meta(ActivityPerformanceSerializer.Meta):
        pass


class MyStandbyPerformanceSerializer(MyPerformanceSerializer, StandbyPerformanceSerializer):
    class Meta(StandbyPerformanceSerializer.Meta):
        pass


class MyAttachmentSerializer(AttachmentSerializer):
    class Meta(AttachmentSerializer.Meta):
        read_only_fields = AttachmentSerializer.Meta.read_only_fields + ('user',)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MyWorkScheduleSerializer(WorkScheduleSerializer):
    class Meta(WorkScheduleSerializer.Meta):
        read_only_fields = WorkScheduleSerializer.Meta.read_only_fields + ('user',)


class MonthInfoSerializer(serializers.Serializer):
    # user_id = serializers.CharField(max_length=255)
    hours_performed = serializers.DecimalField(max_digits=255, decimal_places=2)
    hours_required = serializers.DecimalField(max_digits=255, decimal_places=2)
    # leaves = serializers.CharField(max_length=255)
    # holidays = serializers.CharField(max_length=255)
