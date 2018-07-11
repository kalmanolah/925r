"""Filters."""
import datetime
import dateutil
import logging
import django_filters
import rest_framework_filters as filters
from django_filters.rest_framework import FilterSet
from django.db.models import Q, Func
from django.contrib.admin import widgets as admin_widgets
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from ninetofiver import models
from ninetofiver.utils import merge_dicts


logger = logging.getLogger(__name__)


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
    order_fields = ('username', 'email', 'first_name', 'last_name', 'groups',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = auth_models.User
        fields = {
            'username': ['exact', 'icontains'],
            'email': ['exact', 'icontains'],
            'first_name': ['exact', 'icontains', ],
            'last_name': ['exact', 'icontains', ],
            'is_active': ['exact', ],
            'userinfo__birth_date': ['exact', 'month__exact', 'day__exact'],
            'groups': ['exact', ],
            'groups__name': ['exact', 'icontains'],
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
    order_fields = ('name',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.EmploymentContractType
        fields = {
            'name': ['exact', 'contains', 'icontains'],
        }


class EmploymentContractFilter(FilterSet):
    def is_empl_contr_active(self, queryset, name, value):
        """Checks if the enddate is either null or gte now."""

        if value is True:
            return queryset.filter(
                Q(ended_at__isnull=True) | Q(ended_at__gt=datetime.datetime.now())
            ).distinct()
        elif value is False:
            return queryset.filter(
                Q(ended_at__isnull=False) & Q(ended_at__lte=datetime.datetime.now())
            ).distinct()
        else:
            return queryset

    is_active = django_filters.BooleanFilter(method='is_empl_contr_active')

    order_fields = ('started_at', 'ended_at')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.EmploymentContract
        fields = {
            'started_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ended_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'user': ['exact'],
        }


class WorkScheduleFilter(FilterSet):
    order_fields = ('name',)
    order_by = NullLastOrderingFilter(fields=order_fields)
    current = django_filters.BooleanFilter(method='current_filter')

    def current_filter(self, queryset, name, value):
        if value is True:
            return queryset.filter(Q(employmentcontract__started_at__lte=datetime.datetime.now()),
                                   Q(employmentcontract__ended_at__isnull=True) |
                                   Q(employmentcontract__ended_at__gte=datetime.datetime.now()))

        return queryset

    class Meta:
        model = models.WorkSchedule
        fields = {
            'name': ['exact', 'contains', 'icontains'],
        }


class UserInfoFilter(FilterSet):
    order_fields = ('user', 'gender', 'birth_date', 'country', )
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.UserInfo
        fields = {
            'redmine_id': ['exact'],
            'birth_date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'gender': ['exact'],
            'country': ['iexact', ],
            'user__username': ['exact', ],
            'user__first_name': ['exact', 'contains', 'icontains', ],
            'user__last_name': ['exact', 'contains', 'icontains', ],
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
    order_fields = ('name', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Attachment
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
            'timesheet': ['exact'],
            'leave': ['exact'],
            'contract': ['exact'],
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
    order_fields = ('name',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.LeaveType
        fields = {
            'name': ['exact', 'contains', 'icontains'],
        }


class LeaveFilter(filters.FilterSet):
    """Leave filter."""

    def leavedate_range_distinct(self, queryset, name, value):
        """Filters distinct leavedates between a given range."""
        try:
            values = value.split(',')
            start_date = dateutil.parser.parse(values[0])
            end_date = dateutil.parser.parse(values[1])
        except Exception:
            raise ValidationError('Datetimes have to be in the correct \'YYYY-MM-DDTHH:mm:ss\' format.')

        return queryset.filter(leavedate__starts_at__range=(start_date, end_date)).distinct()

    def leavedate_upcoming_distinct(self, queryset, name, value):
        """Filters distinct leavedates happening after provided date."""
        try:
            base_date = dateutil.parser.parse(value)
        except Exception:
            raise ValidationError('Datetime has to be in the correct \'YYYY-MM-DDTHH:mm:ss\' format.')

        return queryset.filter(leavedate__starts_at__gte=base_date).distinct()

    order_fields = ('status', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    leavedate__range = django_filters.CharFilter(method='leavedate_range_distinct')
    leavedate__gte = django_filters.CharFilter(method='leavedate_upcoming_distinct')

    class Meta:
        model = models.Leave
        fields = {
            'status': ['exact'],
            'description': ['exact', 'contains', 'icontains'],
            'user': ['exact'],
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
    order_fields = ('name', 'description', 'multiplier')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.PerformanceType
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
            'multiplier': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class ContractFilter(FilterSet):

    def contract_range_distinct(self, queryset, name, value):
        """Filters distinct contracts between a given range."""

        # Validate input.
        try:
            # Split value.
            values = value.split(',')
            start_date = datetime.datetime.strptime(values[0], "%Y-%m-%d")
            end_date = datetime.datetime.strptime(values[1], "%Y-%m-%d")
        except:
            # Raise validation error.
            raise ValidationError('Datetimes have to be in the correct \'YYYY-MM-DD\' format.')

        # Filter distinct using range.
        # return queryset.filter(consultancycontract__starts_at__range=(start_date, end_date))
        return queryset.filter(
            Q(consultancycontract__starts_at__range=(start_date, end_date))
            | Q(projectcontract__starts_at__range=(start_date, end_date))
            | Q(supportcontract__starts_at__range=(start_date, end_date))
        )

    def contract_user_id_distinct(self, queryset, name, value):
        """Filters distinct contracts linked to the provided userid."""
        return queryset.filter(contractuser__user__id__iexact=value).distinct()

    contractuser__user__id = django_filters.NumberFilter(method='contract_user_id_distinct')
    contract__ends_at__range = django_filters.CharFilter(method='contract_range_distinct')
    order_fields = ('name', 'description', 'active', 'contractuser__user__username', 'contractuser__user__first_name',
        'contractuser__user__last_name', 'contractuser__user__groups', 'company__vat_identification_number', 'customer__vat_identification_number',
        'company__name', 'customer__name', 'company__country', 'customer_country', 'company__internal', 'customer__internal',
        'contract_groups__name', 'performance_types__name')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:

        model = models.Contract
        fields = {

            # Basic contract fields
            'name': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
            'active': ['exact', ],

            # User related fields
            'contractuser__user__username': ['exact', 'contains', 'icontains', ],
            'contractuser__user__first_name': ['exact', 'contains', 'icontains', ],
            'contractuser__user__last_name': ['exact', 'contains', 'icontains', ],
            'contractuser__user__groups': ['exact', 'contains', 'icontains', ],

            # Companies & Customer fields
            'company__vat_identification_number': ['exact', ],
            'customer__vat_identification_number': ['exact', ],
            'company__name': ['exact', 'contains', 'icontains', ],
            'company': ['exact', ],
            'customer__name': ['exact', 'contains', 'icontains', ],
            'company__country': ['exact', ],
            'customer__country': ['exact', ],
            'company__internal': ['exact', ],
            'customer__internal': ['exact', ],

            # Contractgroup fields
            'contract_groups__name': ['exact', 'contains', 'icontains', ],

            # Performancetype fields
            'performance_types__name': ['exact', 'contains', 'icontains', ],
            'performance_types__id': ['exact', ],
        }


class ProjectContractFilter(ContractFilter):
    order_fields = ContractFilter.order_fields + ('fixed_fee', 'starts_at', 'ends_at')
    order_by = NullLastOrderingFilter(fields = order_fields)

    class Meta(ContractFilter.Meta):
        model = models.ProjectContract
        fields = merge_dicts(ContractFilter.Meta.fields, {

            # Basic ProjectContract fields
            'fixed_fee': ['exact', 'contains', ],
            'starts_at': ['exact', 'gt', 'gte', 'lt', 'lte', ],
            'ends_at': ['exact', 'gt', 'gte', 'lt', 'lte', ],
        })


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


class ContractGroupFilter(FilterSet):
    order_fields = ('name', )
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.ContractGroup
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'contract__name': ['exact', 'contains', 'icontains', ],
        }


class ContractRoleFilter(FilterSet):
    order_fields = ('name', 'description')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.ContractRole
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'description': ['exact', 'contains', 'icontains'],
        }


class ContractUserFilter(FilterSet):
    order_fields = ('contract')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.ContractUser
        fields = {
            'contract': ['exact'],
            'user': ['exact'],
            'user__is_active': ['exact']
        }


class TimesheetFilter(filters.FilterSet):
    order_fields = ('year', 'month', 'status', 'user')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Timesheet
        fields = {
            'year': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'month': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'status': ['exact'],
            'user__id': ['exact'],
        }


class PerformanceFilter(FilterSet):
    order_fields = ('day', 'timesheet__month', 'timesheet__year', 'contract', )
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Performance
        fields = {
            'day': ['exact', 'gt', 'gte', 'lt', 'lte', ],
            'timesheet': ['exact', ],
            'timesheet__month': ['exact', 'gte', 'lte', ],
            'timesheet__year': ['exact', 'gte', 'lte', ],
            'timesheet__user_id': ['exact'],
            'contract': ['exact'],
        }


class ActivityPerformanceFilter(PerformanceFilter):
    order_fields = PerformanceFilter.order_fields + ('duration', 'description', )
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


class LocationFilter(FilterSet):
    order_fields = ('name',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Location
        fields = {
            'name': ['exact', 'contains', 'icontains'],
        }


class WhereaboutFilter(filters.FilterSet):
    """Whereabout filter."""

    order_fields = ('starts_at',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Whereabout
        fields = {
            'location': ['exact'],
            'description': ['exact', 'contains', 'icontains'],
            'timesheet__user': ['exact'],
            'timesheet': ['exact'],
            'starts_at': ['range'],
        }


# Filters for reports
class AdminReportTimesheetContractOverviewFilter(FilterSet):
    """Timesheet contract overview admin report filter."""
    performance__contract = (django_filters.ModelMultipleChoiceFilter(
                             label='Contract', queryset=models.Contract.objects.filter(active=True),  distinct=True))
    performance__contract__polymorphic_ctype__model = (django_filters.MultipleChoiceFilter(
                                               label='Contract type',
                                               choices=[('projectcontract', _('Project')),
                                                        ('consultancycontract', _('Consultancy')),
                                                        ('supportcontract', _('Support'))],
                                               distinct=True))
    performance__contract__customer = (django_filters.ModelMultipleChoiceFilter(
                                       label='Contract customer', queryset=models.Company.objects.filter(),
                                       distinct=True))
    performance__contract__company = (django_filters.ModelMultipleChoiceFilter(
                                      label='Contract company', queryset=models.Company.objects.filter(internal=True),
                                      distinct=True))
    user = django_filters.ModelMultipleChoiceFilter(queryset=auth_models.User.objects.filter(is_active=True))
    year = django_filters.ChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                         .values_list('year', flat=True)
                                                                         .order_by('year').distinct())])
    month = django_filters.ChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                          .values_list('month', flat=True)
                                                                          .order_by('month').distinct())])

    class Meta:
        model = models.Timesheet
        fields = {
            'performance__contract': ['exact'],
            'performance__contract__polymorphic_ctype__model': ['exact'],
            'performance__contract__customer': ['exact'],
            'performance__contract__company': ['exact'],
            'user': ['exact'],
            'status': ['exact'],
            'year': ['exact'],
            'month': ['exact'],
        }


class AdminReportTimesheetOverviewFilter(FilterSet):
    """Timesheet overview admin report filter."""
    user = django_filters.ModelChoiceFilter(queryset=auth_models.User.objects.filter(is_active=True))
    user__employmentcontract__company = django_filters.ModelChoiceFilter(
        label='Company', queryset=models.Company.objects.filter(internal=True), distinct=True)
    year = django_filters.ChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                         .values_list('year', flat=True)
                                                                         .order_by('year').distinct())])
    month = django_filters.ChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                          .values_list('month', flat=True)
                                                                          .order_by('month').distinct())])

    class Meta:
        model = models.Timesheet
        fields = {
            'user': ['exact'],
            'user__employmentcontract__company': ['exact'],
            'status': ['exact'],
            'year': ['exact'],
            'month': ['exact'],
        }


class AdminReportUserRangeInfoFilter(FilterSet):
    """User range info admin report filter."""
    user = django_filters.ModelChoiceFilter(queryset=auth_models.User.objects.filter(is_active=True))
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget())
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget())

    class Meta:
        model = models.Timesheet
        fields = {
            'user': ['exact'],
        }


class AdminReportUserLeaveOverviewFilter(FilterSet):
    """User leave overview admin report filter."""
    user = django_filters.ModelChoiceFilter(name='leave__user',
                                            queryset=auth_models.User.objects.filter(is_active=True))
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget(), name='starts_at',
                                          lookup_expr='date__gte')
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget(), name='starts_at',
                                           lookup_expr='date__lte')

    class Meta:
        model = models.LeaveDate
        fields = {}


class AdminReportUserWorkRatioOverviewFilter(FilterSet):
    """User work ratio overview admin report filter."""
    user = django_filters.ModelChoiceFilter(queryset=auth_models.User.objects.filter(is_active=True))
    year = django_filters.ChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                         .values_list('year', flat=True)
                                                                         .order_by('year').distinct())])

    class Meta:
        model = models.Timesheet
        fields = {}


class AdminReportResourceAvailabilityOverviewFilter(FilterSet):
    """User leave overview admin report filter."""
    user = (django_filters.ModelMultipleChoiceFilter(label='User',
                                                     queryset=auth_models.User.objects.filter(is_active=True),
                                                     distinct=True))
    group = (django_filters.ModelMultipleChoiceFilter(label='Group',
                                                      queryset=auth_models.Group.objects.all(),
                                                      distinct=True))
    contract = (django_filters.ModelMultipleChoiceFilter(label='Contract',
                                                         queryset=models.Contract.objects.filter(active=True),
                                                         distinct=True))
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget(), name='starts_at',
                                          lookup_expr='date__gte')
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget(), name='starts_at',
                                           lookup_expr='date__lte')

    class Meta:
        model = auth_models.User
        fields = {}


class AdminReportExpiringConsultancyContractOverviewFilter(FilterSet):
    """Expiring consultancy contract overview admin report filter."""
    ends_at_lte = django_filters.DateFilter(label='Ends before', widget=admin_widgets.AdminDateWidget(),
                                            name='ends_at', lookup_expr='lte')
    remaining_hours_lte = django_filters.NumberFilter(label='Remaining hours (<=, less than or equal)')
    remaining_days_lte = django_filters.NumberFilter(label='Remaining 8h days (<=, less than or equal)')
    only_final = django_filters.ChoiceFilter(label='Only display final consultancy contract for a user?',
                                             choices=(('true', 'Yes'), ('false', 'No')))

    class Meta:
        model = models.ConsultancyContract
        fields = {}


class AdminReportProjectContractOverviewFilter(FilterSet):
    """Project contract overview admin report filter."""
    contract = (django_filters.ModelMultipleChoiceFilter(label='Contract',
                                                         name='contract_ptr', lookup_expr='in',
                                                         queryset=models.ProjectContract.objects.filter(active=True),
                                                         distinct=True))
    customer = (django_filters.ModelMultipleChoiceFilter(queryset=models.Company.objects.filter(),
                                                         distinct=True))
    company = (django_filters.ModelMultipleChoiceFilter(queryset=models.Company.objects.filter(internal=True),
                                                        distinct=True))
    contract_groups = (django_filters.ModelMultipleChoiceFilter(queryset=models.ContractGroup.objects.all(),
                                                                distinct=True))

    class Meta:
        model = models.ProjectContract
        fields = {
            'contract': ['exact'],
            'name': ['icontains'],
            'contract_groups': ['exact'],
            'company': ['exact'],
            'customer': ['exact'],
        }
