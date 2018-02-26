"""ninetofiver serializers."""
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_countries.serializers import CountryFieldMixin
from django.db.models import Q
from rest_framework import serializers
import logging
import datetime
from ninetofiver import models


logger = logging.getLogger(__name__)


class BaseSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    display_label = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = (
            'id',
            'created_at',
            'updated_at',
            'type',
            'display_label',
        )
        read_only_fields = (
            'id',
            'created_at',
            'updated_at',
            'type',
            'display_label',
        )

    def get_type(self, obj):
        return obj.__class__.__name__

    def get_display_label(self, obj):
        return str(obj)


class BasePolymorphicSerializer(serializers.Serializer):

    """Serializer to handle polymorphic child model serialization."""

    def get_serializer_map(self):
        """
        Return a dict to map class names to their respective serializer classes.

        To be implemented by all BasePolymorphicSerializer subclasses.

        """
        raise NotImplementedError()

    def to_representation(self, obj):
        """
        Translate object to internal data representation

        Override to allow polymorphism.

        """
        type_str = obj.__class__.__name__

        try:
            serializer = self.get_serializer_map()[type_str]
        except KeyError:
            raise ValueError(
                'Serializer for "{}" does not exist'.format(type_str),
            )

        data = serializer(obj, context=self.context).to_representation(obj)
        data['type'] = type_str

        return data

    def to_internal_value(self, data):
        """
        Validate data and initialize primitive types.

        Override to allow polymorphism.

        """
        try:
            type_str = data['type']
        except KeyError:
            raise ValidationError({'type': _('This field is required')})

        try:
            serializer = self.get_serializer_map()[type_str]
        except KeyError:
            raise ValidationError({'type': ValidationError(_('Serializer for "%(type)s" does not exist'),
                                  params={'type': type_str})})

        validated_data = serializer(context=self.context).to_internal_value(data)
        validated_data['type'] = type_str

        return validated_data

    def create(self, validated_data):
        """
        Translate validated data representation to object.

        Override to allow polymorphism.

        """
        serializer = self.get_serializer_map()[validated_data.pop('type')]
        return serializer(context=self.context).create(validated_data)

    def update(self, instance, validated_data):
        """
        Translate validated data representation to object.

        Override to allow polymorphism.

        """
        serializer = self.get_serializer_map()[instance.__class__.__name__]
        return serializer(context=self.context).update(instance, validated_data)


class MinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer."""

    display_label = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'display_label',
            'type',
            'id',
        )
        read_only_fields = (
            'display_label',
            'type',
            'id',
        )

    def get_display_label(self, obj):
        return str(obj)

    def get_type(self, obj):
        return obj.__class__.__name__

    def to_internal_value(self, data):
        return (serializers.PrimaryKeyRelatedField(queryset=self.__class__.Meta.model.objects.all())
                .to_internal_value(data))


class MinimalUserSerializer(MinimalSerializer):

    """Minimal user serializer."""

    class Meta(MinimalSerializer.Meta):
        model = auth_models.User


class MinimalLeaveTypeSerializer(MinimalSerializer):

    """Minimal leave type serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.LeaveType


class MinimalCompanySerializer(MinimalSerializer):

    """Minimal company serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.Company


class MinimalContractSerializer(MinimalSerializer):

    """Minimal contract serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.Contract


class MinimalContractRoleSerializer(MinimalSerializer):

    """Minimal contract role serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.ContractRole


class MinimalPerformanceTypeSerializer(MinimalSerializer):

    """Minimal performance type serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.PerformanceType


class CompanySerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Company
        fields = BaseSerializer.Meta.fields + ('vat_identification_number', 'name', 'address', 'country', 'internal',)


class EmploymentContractTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.EmploymentContractType
        fields = BaseSerializer.Meta.fields + ('name',)


class EmploymentContractSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.EmploymentContract
        fields = BaseSerializer.Meta.fields + ('user', 'company', 'employment_contract_type', 'work_schedule',
                                               'started_at', 'ended_at')


class WorkScheduleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.WorkSchedule
        fields = BaseSerializer.Meta.fields + ('name', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
                                               'saturday', 'sunday')


class UserRelativeSerializer(BaseSerializer):

    class Meta(BaseSerializer.Meta):
        model = models.UserRelative
        fields = BaseSerializer.Meta.fields + ('name', 'relation', 'birth_date', 'gender', 'user')


class UserInfoSerializer(CountryFieldMixin, BaseSerializer):
    join_date = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.UserInfo
        fields = BaseSerializer.Meta.fields + ('user', 'birth_date', 'gender', 'country', 'join_date', 'redmine_id')

    def get_join_date(self, obj):
        return obj.get_join_date()


class GroupSerializer(serializers.ModelSerializer):
    display_label = serializers.SerializerMethodField()

    class Meta:
        model = auth_models.Group
        fields = ('id', 'name', 'display_label')
        read_only_fields = ('id',)

    def get_display_label(self, obj):
        return str(obj)


class UserSerializer(serializers.ModelSerializer):
    display_label = serializers.SerializerMethodField()

    userinfo = UserInfoSerializer()
    groups = GroupSerializer(many=True)

    class Meta:
        model = auth_models.User
        fields = ('id', 'username', 'email', 'groups', 'first_name', 'last_name', 'display_label', 'is_active', 'userinfo')
        read_only_fields = ('id', 'username', 'email', 'groups', 'first_name', 'last_name', 'display_label', 'is_active', 'userinfo' )

    def get_display_label(self, obj):
        return str(obj)


class AttachmentSerializer(BaseSerializer):
    file_url = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.Attachment
        fields = BaseSerializer.Meta.fields + ('name', 'description', 'file', 'slug', 'user', 'file_url')
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
        fields = BaseSerializer.Meta.fields + ('name', 'description',)


class LeaveDateSerializer(BaseSerializer):
    full_day = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.LeaveDate
        fields = BaseSerializer.Meta.fields + ('leave', 'timesheet', 'full_day', 'starts_at', 'ends_at')

    def get_full_day(self, obj):
        """Calculates whether leaveduration > workschedule"""
        ec = models.EmploymentContract.objects.filter(
            Q(user = obj.leave.user),
            Q(ended_at__isnull = True)  | Q(ended_at__gte = datetime.datetime.now())
        )
        ws = models.WorkSchedule.objects.get(employmentcontract = ec).__dict__

        start_time = float(str(obj.starts_at.hour) + '.' + str(obj.starts_at.minute))
        end_time = float(str(obj.ends_at.hour) + '.' + str(obj.ends_at.minute))

        weekday = obj.starts_at.strftime('%A').lower()

        return (end_time - start_time) >= ws[weekday]


class LeaveSerializer(BaseSerializer):
    leavedate_set = LeaveDateSerializer(many=True, read_only=True)
    leave_type = MinimalLeaveTypeSerializer()
    user = MinimalUserSerializer()

    class Meta(BaseSerializer.Meta):
        model = models.Leave
        fields = BaseSerializer.Meta.fields + ('user', 'leave_type', 'leavedate_set', 'status', 'attachments',
                                               'description')


class PerformanceTypeSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.PerformanceType
        fields = BaseSerializer.Meta.fields + ('name', 'description', 'multiplier')


class ContractSerializer(BaseSerializer):
    performance_types = MinimalPerformanceTypeSerializer(many=True, required=False)
    customer = MinimalCompanySerializer()
    company = MinimalCompanySerializer()
    hours_spent = serializers.SerializerMethodField()

    def get_hours_spent(self, obj):
        total = 0
        for hours in models.ActivityPerformance.objects.filter(contract=obj.id):
            total += hours.duration
        return total

    class Meta(BaseSerializer.Meta):
        model = models.Contract
        fields = BaseSerializer.Meta.fields + ('name', 'description', 'company', 'customer', 'performance_types',
                                               'active', 'contract_groups', 'hours_spent', 'starts_at', 'ends_at',
                                               'attachments', 'redmine_id', 'external_only', )


class AdminProjectContractSerializer(ContractSerializer):
    # Serializer that shows classified information.
    hours_estimated = serializers.SerializerMethodField()

    def get_hours_estimated(self, obj):
        return obj.projectestimate_set.values_list('hours_estimated', 'role_id',)


    class Meta(ContractSerializer.Meta):
        model = models.ProjectContract
        fields = ContractSerializer.Meta.fields + ('redmine_id', 'starts_at', 'ends_at', 'fixed_fee', 'hours_estimated',)


class ProjectContractSerializer(ContractSerializer):
    hours_estimated = serializers.SerializerMethodField()

    def get_hours_estimated(self, obj):
        return obj.projectestimate_set.values_list('hours_estimated', 'role_id',)


    class Meta(ContractSerializer.Meta):
        model = models.ProjectContract
        fields = ContractSerializer.Meta.fields + ('redmine_id', 'starts_at', 'ends_at', 'hours_estimated',)


class AdminConsultancyContractSerializer(ContractSerializer):
    # Serializer that shows classified information.
    class Meta(ContractSerializer.Meta):
        model = models.ConsultancyContract
        fields = ContractSerializer.Meta.fields + ('starts_at', 'ends_at', 'day_rate', 'duration')


class ConsultancyContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        model = models.ConsultancyContract
        fields = ContractSerializer.Meta.fields + ('duration',)


class AdminSupportContractSerializer(ContractSerializer):
    # Serializer that shows classified information.
    class Meta(ContractSerializer.Meta):
        model = models.SupportContract
        fields = ContractSerializer.Meta.fields + ('day_rate', 'fixed_fee', 'fixed_fee_period')


class SupportContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        model = models.SupportContract
        fields = ContractSerializer.Meta.fields


class ContractRoleSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractRole
        fields = BaseSerializer.Meta.fields + ('name', 'description')


class ContractUserSerializer(BaseSerializer):
    contract = MinimalContractSerializer()
    contract_role = MinimalContractRoleSerializer()
    user = MinimalUserSerializer()

    class Meta(BaseSerializer.Meta):
        model = models.ContractUser
        fields = BaseSerializer.Meta.fields + (
            'user',
            'contract',
            'contract_role',
        )


class ContractGroupSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ContractGroup
        fields = BaseSerializer.Meta.fields + ('name', )


class ProjectEstimateSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.ProjectEstimate
        fields = BaseSerializer.Meta.fields + ('role', 'project', 'hours_estimated')


class TimesheetSerializer(BaseSerializer):
    user = MinimalUserSerializer()

    class Meta(BaseSerializer.Meta):
        model = models.Timesheet
        fields = BaseSerializer.Meta.fields + ('user', 'year', 'month', 'status')


class WhereaboutSerializer(BaseSerializer):
    class Meta(BaseSerializer.Meta):
        model = models.Whereabout
        fields = BaseSerializer.Meta.fields + ('timesheet', 'day', 'location')


class PerformanceSerializer(BaseSerializer):
    contract = MinimalContractSerializer()

    class Meta(BaseSerializer.Meta):
        model = models.Performance
        fields = BaseSerializer.Meta.fields + ('timesheet', 'day', 'redmine_id', 'contract')

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if not user.is_staff and not user.is_superuser:
            if instance.timesheet.user != user.id:
                raise serializers.ValidationError('Only admins are allowed to update performances from other users.')
            if instance.timesheet.status == models.STATUS_PENDING:
                raise serializers.ValidationError('Only admins are allowed to update performances attached to pending timesheets.')
        return super().update(instance, validated_data)

    def partial_update(self, instance, validated_data):
        user = self.context['request'].user
        if not user.is_staff and not user.is_superuser:
            if instance.timesheet.user != user.id:
                raise serializers.ValidationError('Only admins are allowed to update performances from other users.')
            if instance.timesheet.status == models.STATUS_PENDING:
                raise serializers.ValidationError('Only admins are allowed to update performances attached to pending timesheets.')
        return super().partial_update(instance, validated_data)


class ActivityPerformanceSerializer(PerformanceSerializer):
    performance_type = MinimalPerformanceTypeSerializer()

    class Meta(PerformanceSerializer.Meta):
        model = models.ActivityPerformance
        fields = PerformanceSerializer.Meta.fields + ('duration', 'description', 'performance_type', 'contract_role')


class StandbyPerformanceSerializer(PerformanceSerializer):
    class Meta(PerformanceSerializer.Meta):
        model = models.StandbyPerformance
        fields = PerformanceSerializer.Meta.fields


class MyUserSerializer(UserSerializer):
    userinfo = UserInfoSerializer()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('is_staff', 'is_superuser', 'user_permissions', 'userinfo',)
        depth = 1


class MyLeaveSerializer(LeaveSerializer):
    status = serializers.ChoiceField(choices=(models.STATUS_DRAFT, models.STATUS_PENDING))
    user = MinimalUserSerializer(read_only=True)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().update(instance, validated_data)


class MyLeaveDateSerializer(LeaveDateSerializer):
    def validate_leave(self, value):
        if value.status != models.STATUS_DRAFT:
            raise serializers.ValidationError('You can only manipulate leave dates attached to draft leaves')

        if value.user != self.context['request'].user:
            raise serializers.ValidationError('You can only manipulate leave dates attached to your own leaves')

        return value


class MyTimesheetSerializer(TimesheetSerializer):
    user = MinimalUserSerializer(read_only=True)
    class Meta(TimesheetSerializer.Meta):
        read_only_fields = TimesheetSerializer.Meta.read_only_fields + ('user', )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if not user.is_staff and not user.is_superuser:
            if instance.status == models.STATUS_PENDING and validated_data['status'] == models.STATUS_ACTIVE:
                raise serializers.ValidationError('DA MAG NIE HE MENNEKE')
        return super().update(instance, validated_data)


class MyContractSerializer(ContractSerializer):
    class Meta(ContractSerializer.Meta):
        read_only_fields = ContractSerializer.Meta.read_only_fields + ('user', )


class MyContractUserSerializer(ContractUserSerializer):
    class Meta(ContractUserSerializer.Meta):
        read_only_fields = ContractUserSerializer.Meta.read_only_fields + ('user', )


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


class LeaveRequestSerializer(serializers.Serializer):
    starts_at = serializers.DateTimeField()
    ends_at = serializers.DateTimeField()
    full_day = serializers.BooleanField(required=True)

    def validate_starts_at(self, val):
        """
        Check that the start is a datetime.
        """
        if type(val) is not datetime.datetime:
            return serializers.ValidationError("Starts_at is not a datetime object.")
        return val

    def validate_ends_at(self, val):
        """
        Check that the end is a datetime.
        """
        if type(val) is not datetime.datetime:
            return serializers.ValidationError("Ends_at is not a datetime object.")
        return val

    def validate_full_day(self, val):
        """
        Check that the full_day is a bool.
        """
        if type(val) is not bool:
            return serializers.ValidationError("Full day is not a bool.")
        return val


class LeaveRequestCreateSerializer(LeaveRequestSerializer):
    description = serializers.CharField(max_length=255)
    leave_type = serializers.IntegerField()

    def validate_description(self, val):
        """
        Check that the description is indeed a string.
        """
        if type(val) is not str:
            raise serializers.ValidationError("Description is not a string.")
        return val

    def validate_leave_type(self, val):
        """
        Check that the description is indeed a string.
        """
        if models.LeaveType.objects.filter(pk=val)[0] is None:
            raise serializers.ValidationError("LeaveType is not valid.")
        return val

class LeaveRequestUpdateSerializer(LeaveRequestSerializer):
    leave_id = serializers.IntegerField()

    def validate_leave_id(self, val):
        """
        Check that the description is indeed a string.
        """
        if type(val) is not int or type(val) is not None:
            raise serializers.ValidationError("Leave id is not integer.")
        return val
