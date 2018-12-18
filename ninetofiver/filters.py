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


# Filters for reports
class AdminReportTimesheetContractOverviewFilter(FilterSet):
    """Timesheet contract overview admin report filter."""
    performance__contract = (django_filters.ModelMultipleChoiceFilter(
                             label='Contract', queryset=(models.Contract.objects
                                                         .filter(active=True)
                                                         .select_related('customer'))))
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
    performance__contract__contract_groups = (django_filters.ModelMultipleChoiceFilter(
                                              label='Contract group', queryset=models.ContractGroup.objects.all(),
                                              distinct=True))
    user = django_filters.ModelMultipleChoiceFilter(queryset=auth_models.User.objects.filter(is_active=True))
    year = django_filters.MultipleChoiceFilter(choices=lambda: [[x, x] for x in (models.Timesheet.objects
                                                                                 .values_list('year', flat=True)
                                                                                 .order_by('year').distinct())])
    month = django_filters.MultipleChoiceFilter(choices=lambda: [[x + 1, x + 1] for x in range(12)])

    class Meta:
        model = models.Timesheet
        fields = {
            'performance__contract': ['exact'],
            'performance__contract__polymorphic_ctype__model': ['exact'],
            'performance__contract__customer': ['exact'],
            'performance__contract__company': ['exact'],
            'performance__contract__contract_groups': ['exact'],
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
    user = django_filters.ModelChoiceFilter(field_name='leave__user',
                                            queryset=auth_models.User.objects.filter(is_active=True))
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
                                          lookup_expr='date__gte')
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
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
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
                                          lookup_expr='date__gte')
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
                                           lookup_expr='date__lte')

    class Meta:
        model = auth_models.User
        fields = {}


class AdminReportExpiringConsultancyContractOverviewFilter(FilterSet):
    """Expiring consultancy contract overview admin report filter."""
    ends_at_lte = django_filters.DateFilter(label='Ends before', widget=admin_widgets.AdminDateWidget(),
                                            field_name='ends_at', lookup_expr='lte')
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
                                                         field_name='contract_ptr', lookup_expr='in',
                                                         queryset=models.ProjectContract.objects.filter(active=True),
                                                         distinct=True))
    customer = (django_filters.ModelMultipleChoiceFilter(queryset=models.Company.objects.filter(),
                                                         distinct=True))
    company = (django_filters.ModelMultipleChoiceFilter(queryset=models.Company.objects.filter(internal=True),
                                                        distinct=True))
    contractuser__user = (django_filters.ModelMultipleChoiceFilter(label='User',
                                                                   queryset=auth_models.User.objects.filter(is_active=True),
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
            'contractuser__user': ['exact'],
        }


class AdminReportUserOvertimeOverviewFilter(FilterSet):
    """User overtime overview admin report filter."""
    user = django_filters.ModelChoiceFilter(field_name='leave__user',
                                            queryset=auth_models.User.objects.filter(is_active=True))
    from_date = django_filters.DateFilter(label='From', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
                                          lookup_expr='date__gte')
    until_date = django_filters.DateFilter(label='Until', widget=admin_widgets.AdminDateWidget(), field_name='starts_at',
                                           lookup_expr='date__lte')

    class Meta:
        model = models.LeaveDate
        fields = {}


class AdminReportExpiringSupportContractOverviewFilter(FilterSet):
    """Expiring support contract overview admin report filter."""
    ends_at_lte = django_filters.DateFilter(label='Ends before', widget=admin_widgets.AdminDateWidget(),
                                            field_name='ends_at', lookup_expr='lte')

    class Meta:
        model = models.SupportContract
        fields = {}
