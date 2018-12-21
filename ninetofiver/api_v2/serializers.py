"""925r API v2 serializers."""
from django.contrib.auth import models as auth_models
from django_countries.serializers import CountryFieldMixin
from django.utils.translation import ugettext_lazy as _
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from decimal import Decimal
import dateutil
import copy
import datetime

from rest_framework import serializers
from ninetofiver import models, settings


class BaseSerializer(serializers.ModelSerializer):
    """Base serializer."""

    type = serializers.SerializerMethodField()
    display_label = serializers.SerializerMethodField()

    class Meta:
        model = None
        fields = (
            'id',
            'type',
            'display_label',
        )
        read_only_fields = (
            'id',
            'type',
            'display_label',
        )

    def get_type(self, obj):
        return obj.__class__.__name__

    def get_display_label(self, obj):
        return str(obj)

    def populate_validated_data_from_context(self, validated_data):
        pass

    def create(self, validated_data):
        self.populate_validated_data_from_context(validated_data)
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        self.populate_validated_data_from_context(validated_data)
        return super().update(instance, validated_data)


class MinimalSerializer(BaseSerializer):
    """Minimal serializer."""

    def to_internal_value(self, data):
        return (serializers.PrimaryKeyRelatedField(queryset=self.__class__.Meta.model.objects.all()).to_internal_value(data))


class BasicSerializer(BaseSerializer):
    """Basic serializer."""

    class Meta(BaseSerializer.Meta):
        fields = BaseSerializer.Meta.fields + (
            'created_at',
            'updated_at',
        )
        read_only_fields = BaseSerializer.Meta.read_only_fields + (
            'created_at',
            'updated_at',
        )


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
            raise serializers.ValidationError({'type': _('This field is required')})

        try:
            serializer = self.get_serializer_map()[type_str]
        except KeyError:
            raise serializers.ValidationError({'type': serializers.ValidationError(_('Serializer for "%(type)s" does not exist'),
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


class MinimalGroupSerializer(MinimalSerializer):
    """Minimal group serializer."""

    class Meta(MinimalSerializer.Meta):
        model = auth_models.Group


class MinimalPerformanceTypeSerializer(MinimalSerializer):
    """Minimal performance type serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.PerformanceType


class MinimalLocationSerializer(MinimalSerializer):
    """Minimal location serializer."""

    class Meta(MinimalSerializer.Meta):
        model = models.Location


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


class UserInfoSerializer(CountryFieldMixin, BaseSerializer):
    join_date = serializers.SerializerMethodField()

    class Meta(BaseSerializer.Meta):
        model = models.UserInfo
        fields = BaseSerializer.Meta.fields + (
            'birth_date',
            'gender',
            'country',
            'join_date',
            'phone_number',
        )

    def get_join_date(self, obj):
        return obj.get_join_date()


class UserSerializer(BaseSerializer):
    """User serializer."""

    userinfo = UserInfoSerializer()

    class Meta(BaseSerializer.Meta):
        model = auth_models.User
        fields = BaseSerializer.Meta.fields + (
            'username',
            'email',
            'first_name',
            'last_name',
            'is_active',
            'userinfo',
        )


class MeSerializer(UserSerializer):
    """Me serializer."""

    groups = MinimalGroupSerializer(many=True)

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + (
            'is_staff',
            'is_superuser',
            'groups',
        )


class LeaveTypeSerializer(BaseSerializer):
    """Leave type serializer."""

    class Meta(BaseSerializer.Meta):
        model = models.LeaveType
        fields = BaseSerializer.Meta.fields + (
            'name',
        )


class ContractRoleSerializer(BaseSerializer):
    """Contract role serializer."""

    class Meta(BaseSerializer.Meta):
        model = models.ContractRole
        fields = BaseSerializer.Meta.fields + (
            'name',
        )


class PerformanceTypeSerializer(BaseSerializer):
    """Performance type serializer."""

    class Meta(BaseSerializer.Meta):
        model = models.PerformanceType
        fields = BaseSerializer.Meta.fields + (
            'name',
            'multiplier',
        )


class LocationSerializer(BaseSerializer):
    """Location serializer."""

    class Meta(BaseSerializer.Meta):
        model = models.Location
        fields = BaseSerializer.Meta.fields + (
            'name',
        )


class HolidaySerializer(BaseSerializer):
    """Holiday serializer."""

    class Meta(BaseSerializer.Meta):
        model = models.Holiday
        fields = BaseSerializer.Meta.fields + (
            'name',
            'country',
            'date',
        )


class TimesheetSerializer(BasicSerializer):
    """Timesheet serializer."""

    def populate_validated_data_from_context(self, validated_data):
        super().populate_validated_data_from_context(validated_data)
        validated_data['user'] = self.context['request'].user

    def update(self, instance, validated_data):
        if instance.status != models.STATUS_ACTIVE:
            # If the timesheet is updated when it is finalized, only allow adding of attachments
            if ((len(validated_data) > 1) or ('attachments' not in validated_data) or
                (list(set(instance.attachments.all()) - set(validated_data['attachments'])))):
                raise serializers.ValidationError({'status': _('You can only add attachments to finalized timesheets.')})

        return super().update(instance, validated_data)

    class Meta(BasicSerializer.Meta):
        model = models.Timesheet
        fields = BasicSerializer.Meta.fields + (
            'year',
            'month',
            'status',
            'attachments',
        )


class LeaveDateSerializer(BasicSerializer):
    """Leave date serializer."""

    class Meta(BasicSerializer.Meta):
        model = models.LeaveDate
        fields = BasicSerializer.Meta.fields + (
            'starts_at',
            'ends_at',
        )


class LeaveSerializer(BasicSerializer):
    """Leave serializer."""

    status = serializers.ChoiceField(choices=(models.STATUS_DRAFT, models.STATUS_PENDING))
    leavedate_set = LeaveDateSerializer(many=True, read_only=True)
    leave_type = MinimalLeaveTypeSerializer()
    starts_at = serializers.CharField(write_only=True)
    ends_at = serializers.CharField(write_only=True)
    full_day = serializers.BooleanField(write_only=True)

    def populate_validated_data_from_context(self, validated_data):
        super().populate_validated_data_from_context(validated_data)
        validated_data['user'] = self.context['request'].user

    def create(self, validated_data):
        leave = None
        with transaction.atomic():
            starts_at = validated_data.pop('starts_at', None)
            ends_at = validated_data.pop('ends_at', None)
            full_day = validated_data.pop('full_day', None)

            leave = super().create(validated_data)
            self.apply_date_range_to_leave(leave, starts_at, ends_at, full_day)
        return leave

    def update(self, instance, validated_data):
        if instance.status not in [models.STATUS_DRAFT, models.STATUS_PENDING]:
            # If the leave is updated when it is finalized, only allow adding of attachments
            if ((len(validated_data) > 1) or ('attachments' not in validated_data) or
                (list(set(instance.attachments.all()) - set(validated_data['attachments'])))):
                raise serializers.ValidationError({'status': _('You can only add attachments to finalized leave.')})

        leave = None
        with transaction.atomic():
            starts_at = validated_data.pop('starts_at', None)
            ends_at = validated_data.pop('ends_at', None)
            full_day = validated_data.pop('full_day', None)
            leave = super().update(instance, validated_data)

            if starts_at and ends_at:
                self.apply_date_range_to_leave(leave, starts_at, ends_at, full_day)
        return leave
    
    def apply_date_range_to_leave(self, leave, starts_at, ends_at, full_day):
        starts_at = dateutil.parser.parse(starts_at)
        starts_at = timezone.make_aware(starts_at) if not timezone.is_aware(starts_at) else starts_at
        starts_at = starts_at.replace(second=1)
        ends_at = dateutil.parser.parse(ends_at)
        ends_at = timezone.make_aware(ends_at) if not timezone.is_aware(ends_at) else ends_at
        ends_at = ends_at.replace(second=0)

        # If the leave isn't pending/draft, NOPE
        if leave.status not in [models.STATUS_PENDING, models.STATUS_DRAFT]:
            raise serializers.ValidationError(_('Leave status should be draft/pending before it can be updated.'))

        # If the end date comes before the start date, NOPE
        if ends_at < starts_at:
            raise serializers.ValidationError(_('The end date should come after the start date.'))

        # Clear all leave dates
        [x.delete() for x in leave.leavedate_set.all()]

        # Set leave to draft no matter what
        leave.status = models.STATUS_DRAFT

        # Determine leave dates to create
        leave_dates = []

        # If this isn't a full day request, we have a single pair
        if not full_day:
            leave_dates.append([starts_at, ends_at])

        # If this is a full day request, determine leave date pairs using work schedule
        else:
            # Determine amount of days we are going to create leaves for, so we can
            # iterate over the dates
            leave_date_count = (ends_at - starts_at).days + 1

            work_schedule = None
            employment_contract = None

            for i in range(leave_date_count):
                # Determine date for this day
                current_dt = copy.deepcopy(starts_at) + datetime.timedelta(days=i)
                current_date = current_dt.date()

                # For the given date, determine the active work schedule
                if ((not employment_contract) or (employment_contract.started_at > current_date) or
                        (employment_contract.ended_at and (employment_contract.ended_at < current_date))):
                    employment_contract = models.EmploymentContract.objects.filter(
                        Q(user=leave.user, started_at__lte=current_date) &
                        (Q(ended_at__isnull=True) | Q(ended_at__gte=current_date))
                    ).first()
                    work_schedule = employment_contract.work_schedule if employment_contract else None

                # Determine amount of hours to work on this day based on work schedule
                work_hours = 0.00
                if work_schedule:
                    work_hours = float(getattr(work_schedule, current_date.strftime('%A').lower(), Decimal(0.00)))

                # Determine existence of holidays on this day based on work schedule
                holiday = None
                if employment_contract:
                    holiday = models.Holiday.objects.filter(date=current_date,
                                                            country=employment_contract.company.country).first()

                # If we have to work a certain amount of hours on this day, and there is no holiday on that day,
                # add a leave date pair for that amount of hours
                if (work_hours > 0.0) and (not holiday):
                    # Ensure the leave starts when the working day does
                    pair_starts_at = current_dt.replace(hour=settings.DEFAULT_WORKING_DAY_STARTING_HOUR, minute=0,
                                                        second=1)
                    # Add work hours to pair start to obtain pair end
                    pair_ends_at = pair_starts_at.replace(hour=int(pair_starts_at.hour + work_hours),
                                                          minute=int((work_hours % 1) * 60), second=0)
                    # Log pair
                    leave_dates.append([pair_starts_at, pair_ends_at])

        # If no leave date pairs are available, no leave should be created
        if not leave_dates:
            raise serializers.ValidationError(_('No leave dates are available for this period.'))

        # Create leave dates for leave date pairs
        timesheet = None
        for pair in leave_dates:
            # Determine timesheet to use
            if (not timesheet) or ((timesheet.year != pair[0].year) or (timesheet.month != pair[0].month)):
                timesheet = models.Timesheet.objects.get_or_create(user=leave.user, year=pair[0].year,
                                                                   month=pair[0].month)[0]

            models.LeaveDate.objects.create(leave=leave, timesheet=timesheet, starts_at=pair[0],
                                            ends_at=pair[1])

        # Mark leave as Pending
        leave.status = models.STATUS_PENDING
        leave.save()

    class Meta(BasicSerializer.Meta):
        model = models.Leave
        fields = BasicSerializer.Meta.fields + (
            'status',
            'leavedate_set',
            'leave_type',
            'ends_at',
            'starts_at',
            'full_day',
            'attachments',
            'description',
        )


class BasicContractSerializer(BasicSerializer):
    """Basic contract serializer."""

    performance_types = MinimalPerformanceTypeSerializer(many=True)
    customer = MinimalCompanySerializer()
    company = MinimalCompanySerializer()

    class Meta(BasicSerializer.Meta):
        model = models.Contract
        fields = BasicSerializer.Meta.fields + (
            'name',
            'description',
            'company',
            'customer',
            'performance_types',
            'active',
            'starts_at',
            'ends_at',
        )


class ProjectContractSerializer(BasicContractSerializer):
    """Project contract serializer."""

    class Meta(BasicContractSerializer.Meta):
        model = models.ProjectContract


class ConsultancyContractSerializer(BasicContractSerializer):
    """Consultancy contract serializer."""

    class Meta(BasicContractSerializer.Meta):
        model = models.ConsultancyContract
        fields = BasicContractSerializer.Meta.fields + (
            'duration',
        )


class SupportContractSerializer(BasicContractSerializer):
    """Support contract serializer."""

    class Meta(BasicContractSerializer.Meta):
        model = models.SupportContract


class ContractSerializer(BasePolymorphicSerializer):
    """Contract serializer."""

    def get_serializer_map(self):
        return {
            models.SupportContract.__name__: SupportContractSerializer,
            models.ProjectContract.__name__: ProjectContractSerializer,
            models.ConsultancyContract.__name__: ConsultancyContractSerializer,
        }


class ContractUserSerializer(BasicSerializer):
    """Contract user serializer."""

    contract = MinimalContractSerializer()
    contract_role = MinimalContractRoleSerializer()

    class Meta(BasicSerializer.Meta):
        model = models.ContractUser
        fields = BasicSerializer.Meta.fields + (
            'contract',
            'contract_role',
        )


class WhereaboutSerializer(BasicSerializer):
    """Whereabout serializer."""

    location = MinimalLocationSerializer()

    def populate_validated_data_from_context(self, validated_data):
        super().populate_validated_data_from_context(validated_data)
        validated_data['timesheet'] = (models.Timesheet.objects
                                       .get_or_create(user=self.context['request'].user,
                                                      year=validated_data['starts_at'].year,
                                                      month=validated_data['starts_at'].month)[0])

    class Meta(BasicSerializer.Meta):
        model = models.Whereabout
        fields = BasicSerializer.Meta.fields + (
            'location',
            'description',
            'starts_at',
            'ends_at',
        )


class BasicPerformanceSerializer(BasicSerializer):
    """Basic performance serializer."""

    contract = MinimalContractSerializer()

    def populate_validated_data_from_context(self, validated_data):
        super().populate_validated_data_from_context(validated_data)
        validated_data['timesheet'] = (models.Timesheet.objects
                                       .get_or_create(user=self.context['request'].user,
                                                      year=validated_data['date'].year,
                                                      month=validated_data['date'].month)[0])

    class Meta(BasicSerializer.Meta):
        model = models.Performance
        fields = BasicSerializer.Meta.fields + (
            'contract',
            'date',
        )


class ActivityPerformanceSerializer(BasicPerformanceSerializer):
    """Activity performance serializer."""

    performance_type = MinimalPerformanceTypeSerializer()
    contract_role = MinimalContractRoleSerializer()

    class Meta(BasicPerformanceSerializer.Meta):
        model = models.ActivityPerformance
        fields = BasicPerformanceSerializer.Meta.fields + (
            'duration',
            'description',
            'performance_type',
            'contract_role',
            'redmine_id',
        )


class StandbyPerformanceSerializer(BasicPerformanceSerializer):
    """Standby performance serializer."""

    class Meta(BasicPerformanceSerializer.Meta):
        model = models.StandbyPerformance


class PerformanceSerializer(BasePolymorphicSerializer):
    """Performance serializer."""

    def get_serializer_map(self):
        return {
            models.ActivityPerformance.__name__: ActivityPerformanceSerializer,
            models.StandbyPerformance.__name__: StandbyPerformanceSerializer,
        }


class AttachmentSerializer(BasicSerializer):
    """Attachment serializer."""

    file_url = serializers.SerializerMethodField(read_only=True)

    def populate_validated_data_from_context(self, validated_data):
        super().populate_validated_data_from_context(validated_data)
        validated_data['user'] = self.context['request'].user

    def get_file_url(self, obj):
        return obj.get_file_url()

    def update(self, instance, validated_data):
        # Don't allow updating of attachment if the attached leave/timesheet is already closed/approved/rejected
        if (models.Timesheet.objects.filter(~Q(status=models.STATUS_ACTIVE), attachments=instance).count() or
            models.Leave.objects.filter(Q(status=models.STATUS_APPROVED) | Q(status=models.STATUS_REJECTED), attachments=instance)):
            raise serializers.ValidationError(_('Attachments linked to finalized timesheets or leaves cannot be updated.'))

        return super().update(instance, validated_data)

    class Meta(BasicSerializer.Meta):
        model = models.Attachment
        fields = BasicSerializer.Meta.fields + (
            'name',
            'description',
            'file',
            'slug',
            'file_url',
        )