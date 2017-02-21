import django_filters

from datetime import datetime

from django_filters import BooleanFilter
from django_filters import CharFilter

from collections import Counter
from django.db.models import Func
from django_filters.rest_framework import FilterSet
from ninetofiver import models
from ninetofiver.utils import merge_dicts
from rest_framework import generics

from django.contrib.auth import models as auth_models


# Custom filter to see if user is active currently
def filter_active_user(queryset, name, value):
    if value:
        return queryset.filter(employmentcontract__ended_at__gt = datetime.today())
    else:
        return queryset.filter(employmentcontract__ended_at__lte = datetime.today())


# Custom filter to see if user is active on specific day
def filter_active_day(queryset, name, value):
    fl = 'gt' if value else 'lte'

    lookup = '__'.join(['employmentcontract', 'work_schedule', name, fl])
    return queryset.filter(**{lookup: 0})


class IsNull(Func):
    template = '%(expressions)s IS NULL'


class NullLastOrderingFilter(django_filters.OrderingFilter):

    """An ordering filter which places records with fields containing null values last."""

    def filter(self, qs, value):
        """Execute the filter."""
        if value in django_filters.filters.EMPTY_VALUES:
            return qs

        ordering = []
        for param in value:
            if param[0] == '-':
                cleaned_param = param.lstrip('-')
                order = self.param_map[cleaned_param]

                if type(order) is dict:
                    order['order'] = '-%s' % order['order']
                    ordering.append(order)
                    continue

            ordering.append(self.get_ordering_value(param))

        # ordering = [self.get_ordering_value(param) for param in value]
        final_ordering = []

        for order in ordering:
            if type(order) is dict:
                if order.get('annotate', None):
                    qs = qs.annotate(**order['annotate'])

                if order.get('order', None):
                    order = order['order']
                else:
                    continue

            # field = order.lstrip('-')
            # null_field = '%s_isnull' % field
            # params = {null_field: IsNull(field)}
            # qs = qs.annotate(**params)
            #
            # final_ordering.append(null_field)
            final_ordering.append(order)

        qs = qs.order_by(*final_ordering)

        return qs


class UserFilter(FilterSet):

    active_user = BooleanFilter(name='active_user', method=filter_active_user)
    active_monday = BooleanFilter(name='monday', method=filter_active_day)
    active_tuesday = BooleanFilter(name='tuesday', method=filter_active_day)
    active_wednesday = BooleanFilter(name='wednesday', method=filter_active_day)
    active_thursday = BooleanFilter(name='thursday', method=filter_active_day)
    active_friday = BooleanFilter(name='friday', method=filter_active_day)
    active_saturday = BooleanFilter(name='saturday', method=filter_active_day)
    active_sunday = BooleanFilter(name='sunday', method=filter_active_day)

    order_fields = ('username', 'first_name')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:

        model = auth_models.User
        
        fields = {

            # Basic user fields
            'username': ['exact', ],
            'email': ['exact', ],
            'first_name': ['exact', 'contains', 'icontains', ],
            'last_name': ['exact', 'contains', 'icontains', ],

            # AuthGroups fields
            'groups': ['exact', 'contains', 'icontains', ],

            # Userrelative fields
            'userrelative__name': ['exact', 'contains', 'icontains', ],

            # Userinfo fields
            'userinfo__gender': ['iexact', ],
            'userinfo__country': ['iexact', ],
            'userinfo__birth_date': ['exact', 'year__gt', 'year__gte', 'year__lt', 'year__lte', ],

            # Employmentcontract fields
            'employmentcontract__started_at': ['exact', 'year__gt', 'year__gte', 'year__lt', 'year__lte', ],
            'employmentcontract__ended_at': ['exact', 'year__gt', 'year__gte', 'year__lt', 'year__lte'],
            'employmentcontract__company__name': ['exact', 'contains', 'icontains', ],

            # Workschedule fields
            'employmentcontract__work_schedule__label': ['exact', 'contains', 'icontains', ],


            # Customer & Company fields, linked through contract
            'contractuser__contract__customer__name': ['exact', 'contains', 'icontains', ],
            'contractuser__contract__company__name': ['exact', 'contains', 'icontains', ],
            'contractuser__contract__customer__internal': ['exact', ],
            'contractuser__contract__company__internal': ['exact', ],
            'contractuser__contract__customer__country': ['exact', ],
            'contractuser__contract__company__country': ['exact', ],

            # EmploymentContract Type fields
            'employmentcontract__employment_contract_type__label': ['exact', ],

            # Check if user is on leave
            'leave__leavedate__starts_at': ['range']
        }


class CompanyFilter(FilterSet):
    order_fields = ('name', 'country', 'vat_identification_number', 'address', 'internal')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Company
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'country': ['exact'],
            'vat_identification_number': ['exact', 'contains', 'icontains'],
            'address': ['exact', 'contains', 'icontains'],
            'internal': ['exact'],
        }


class EmploymentContractTypeFilter(FilterSet):
    order_fields = ('label',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.EmploymentContractType
        fields = {
            'label': ['exact', 'contains', 'icontains'],
        }


class EmploymentContractFilter(FilterSet):
    order_fields = ('started_at', 'ended_at')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.EmploymentContract
        fields = {
            'started_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ended_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class WorkScheduleFilter(FilterSet):
    order_fields = ('label',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.WorkSchedule
        fields = {
            'label': ['exact', 'contains', 'icontains'],
        }


class UserRelativeFilter(FilterSet):
    order_fields = ('name', 'relation', 'birth_date', 'gender')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.UserRelative
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'relation': ['exact', 'contains', 'icontains'],
            'birth_date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'gender': ['exact'],
            'user__username': ['exact', ],
            'user__first_name': ['exact', 'contains', 'icontains', ],
            'user__last_name': ['exact', 'contains', 'icontains', ],
        }


class AttachmentFilter(FilterSet):
    order_fields = ('label', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Attachment
        fields = {
            'label': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
        }


class HolidayFilter(FilterSet):
    order_fields = ('name', 'date', 'country')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Holiday
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'country': ['exact'],
        }


class LeaveTypeFilter(FilterSet):
    order_fields = ('label',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.LeaveType
        fields = {
            'label': ['exact', 'contains', 'icontains'],
        }


class LeaveFilter(FilterSet):
    order_fields = ('status', 'description', 'leavedate__starts_at', 'leavedate__ends_at')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Leave
        fields = {
            'status': ['exact'],
            'description': ['exact', 'contains', 'icontains'],
        }


class LeaveDateFilter(FilterSet):
    order_fields = ('starts_at', 'ends_at')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.LeaveDate
        fields = {
            'starts_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ends_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class PerformanceTypeFilter(FilterSet):
    order_fields = ('label', 'description', 'multiplier')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.PerformanceType
        fields = {
            'label': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
            'multiplier': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class ContractFilter(FilterSet):
    order_fields = ('label', 'description', 'active')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Contract
        fields = {
            'label': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
            'active': ['exact'],

        }


class ProjectContractFilter(ContractFilter):
    class Meta(ContractFilter.Meta):
        model = models.ProjectContract
        fields = ContractFilter.Meta.fields


class ConsultancyContractFilter(ContractFilter):
    order_fields = ContractFilter.order_fields + ('day_rate', 'starts_at', 'ends_at', 'duration')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta(ContractFilter.Meta):
        model = models.ConsultancyContract
        fields = merge_dicts(ContractFilter.Meta.fields, {
            'day_rate': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'starts_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ends_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'duration': ['exact', 'gt', 'gte', 'lt', 'lte'],
        })


class SupportContractFilter(ContractFilter):
    order_fields = ContractFilter.order_fields + ('day_rate', 'starts_at', 'ends_at', 'fixed_fee', 'fixed_fee_period')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta(ContractFilter.Meta):
        model = models.SupportContract
        fields = merge_dicts(ContractFilter.Meta.fields, {
            'day_rate': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'starts_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ends_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'fixed_fee': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'fixed_fee_period': ['exact'],
        })


class ContractRoleFilter(FilterSet):
    order_fields = ('label', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.ContractRole
        fields = {
            'label': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
        }


class ContractUserFilter(FilterSet):
    class Meta:
        model = models.ContractUser
        fields = {
        }


class TimesheetFilter(FilterSet):
    order_fields = ('year', 'month', 'closed')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Timesheet
        fields = {
            'year': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'month': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'closed': ['exact'],
        }


class PerformanceFilter(FilterSet):
    order_fields = ('day',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Performance
        fields = {
            'day': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class ActivityPerformanceFilter(PerformanceFilter):
    order_fields = PerformanceFilter.order_fields + ('duration', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta(PerformanceFilter.Meta):
        model = models.ActivityPerformance
        fields = merge_dicts(PerformanceFilter.Meta.fields, {
            'duration': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'description': ['exact', 'contains', 'icontains'],
        })


class StandbyPerformanceFilter(PerformanceFilter):
    order_fields = PerformanceFilter.order_fields
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta(PerformanceFilter.Meta):
        model = models.StandbyPerformance
        fields = PerformanceFilter.Meta.fields