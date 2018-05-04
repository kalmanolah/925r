from django.contrib.auth import models as auth_models, mixins as auth_mixins
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.forms.models import modelform_factory
from django.views import generic as generic_views
from django.db import transaction
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.urls import reverse_lazy
from decimal import Decimal
from ninetofiver import filters
from ninetofiver import models
from ninetofiver import serializers
from ninetofiver import redmine
from ninetofiver import feeds
from ninetofiver.viewsets import GenericHierarchicalReadOnlyViewSet
from rest_framework import parsers
from rest_framework import permissions
from rest_framework import response
from rest_framework import status
from rest_framework import schemas
from rest_framework import viewsets
from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.decorators import permission_classes
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer
from rest_framework.authtoken import models as authtoken_models
from ninetofiver import settings, tables, calculation, pagination
from ninetofiver.utils import month_date_range, dates_in_range
from django.db.models import Q
from django_tables2 import RequestConfig
from django_tables2.export.export import TableExport
from datetime import datetime, date, timedelta
from wkhtmltopdf.views import PDFTemplateView
from dateutil import parser
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
import logging
import copy


logger = logging.getLogger(__name__)


# Reused classes

class BaseTimesheetContractPdfExportServiceAPIView(PDFTemplateView, generics.GenericAPIView):
    """Export a timesheet contract to PDF."""

    filename = 'timesheet_contract.pdf'
    template_name = 'ninetofiver/timesheets/timesheet_contract_pdf_export.pug'

    def resolve_user(self, context):
        """Resolve the user for this export."""
        raise NotImplementedError()

    def render_to_response(self, context, **response_kwargs):
        user = self.resolve_user(context)
        timesheet = get_object_or_404(models.Timesheet, pk=context.get('timesheet_pk', None), user=user)
        contract = get_object_or_404(models.Contract, pk=context.get('contract_pk', None), contractuser__user=user)

        context['user'] = user
        context['timesheet'] = timesheet
        context['contract'] = contract

        context['activity_performances'] = (models.ActivityPerformance.objects
                                            .filter(timesheet=timesheet, contract=contract)
                                            .order_by('day')
                                            .select_related('performance_type')
                                            .all())
        context['total_performed_hours'] = sum([x.duration for x in context['activity_performances']])
        context['total_performed_days'] = round(context['total_performed_hours'] / 8, 2)

        context['standby_performances'] = (models.StandbyPerformance.objects
                                           .filter(timesheet=timesheet, contract=contract)
                                           .order_by('day')
                                           .all())
        context['total_standby_days'] = round(len(context['standby_performances']), 2)

        # Create a performances dict, indexed by date
        performances = {}
        [performances.setdefault(str(x.get_date()), {}).setdefault('activity', []).append(x)
            for x in context['activity_performances']]
        [performances.setdefault(str(x.get_date()), {}).setdefault('standby', []).append(x)
            for x in context['standby_performances']]
        # Sort performances dict by date
        context['performances'] = OrderedDict()
        for day in sorted(performances):
            context['performances'][day] = performances[day]

        return super().render_to_response(context, **response_kwargs)


# Homepage and others
def home_view(request):
    """Homepage."""
    context = {}
    return render(request, 'ninetofiver/home/index.pug', context)


@login_required
def account_view(request):
    """User-specific account page."""
    context = {}
    return render(request, 'ninetofiver/account/index.pug', context)


class ApiKeyCreateView(auth_mixins.LoginRequiredMixin, generic_views.CreateView):
    """View used to create an API key."""

    template_name = 'ninetofiver/api_keys/create.pug'
    success_url = reverse_lazy('api-key-list')

    def get_form_class(self):
        """Get the form class."""
        return modelform_factory(models.ApiKey, fields=('name', 'read_only',))

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class ApiKeyListView(auth_mixins.LoginRequiredMixin, generic_views.ListView):
    """List view for all API keys owned by the user."""

    context_object_name = 'tokens'
    template_name = 'ninetofiver/api_keys/list.pug'

    def get_queryset(self):
        return models.ApiKey.objects.filter(user=self.request.user)


class ApiKeyDeleteView(auth_mixins.LoginRequiredMixin, generic_views.DeleteView):
    """View used to delete an API key owned by the user."""

    context_object_name = "apikey"
    success_url = reverse_lazy('api-key-list')
    template_name = 'ninetofiver/api_keys/delete.pug'

    def get_queryset(self):
        return models.ApiKey.objects.filter(user=self.request.user)


@api_view(exclude_from_schema=True)
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer, CoreJSONRenderer])
@permission_classes((permissions.IsAuthenticated,))
def schema_view(request):
    """API documentation."""
    generator = schemas.SchemaGenerator(title='Ninetofiver API')
    return response.Response(generator.get_schema(request=request))


# Admin-only
@staff_member_required
def admin_leave_approve_view(request, leave_pk):
    """Approve the selected leaves."""
    leave_pks = list(map(int, leave_pk.split(',')))
    return_to_referer = request.GET.get('return', 'false').lower() == 'true'

    leaves = models.Leave.objects.filter(id__in=leave_pks, status=models.STATUS_PENDING)

    for leave in leaves:
        leave.status = models.STATUS_APPROVED
        leave.save()

    context = {
        'leaves': leaves,
    }

    if return_to_referer and request.META.get('HTTP_REFERER', None):
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'ninetofiver/admin/leaves/approve.pug', context)


@staff_member_required
def admin_leave_reject_view(request, leave_pk):
    """Reject the selected leaves."""
    leave_pks = list(map(int, leave_pk.split(',')))
    return_to_referer = request.GET.get('return', 'false').lower() == 'true'

    leaves = models.Leave.objects.filter(id__in=leave_pks, status=models.STATUS_PENDING)

    for leave in leaves:
        leave.status = models.STATUS_REJECTED
        leave.save()

    context = {
        'leaves': leaves,
    }

    if return_to_referer and request.META.get('HTTP_REFERER', None):
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'ninetofiver/admin/leaves/reject.pug', context)


@staff_member_required
def admin_timesheet_close_view(request, timesheet_pk):
    """Close the selected timesheets."""
    timesheet_pks = list(map(int, timesheet_pk.split(',')))
    return_to_referer = request.GET.get('return', 'false').lower() == 'true'

    timesheets = models.Timesheet.objects.filter(id__in=timesheet_pks, status=models.STATUS_PENDING)

    for timesheet in timesheets:
        timesheet.status = models.STATUS_CLOSED
        timesheet.save()

    context = {
        'timesheets': timesheets,
    }

    if return_to_referer and request.META.get('HTTP_REFERER', None):
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'ninetofiver/admin/timesheets/close.pug', context)


@staff_member_required
def admin_timesheet_activate_view(request, timesheet_pk):
    """Activate the selected timesheets."""
    timesheet_pks = list(map(int, timesheet_pk.split(',')))
    return_to_referer = request.GET.get('return', 'false').lower() == 'true'

    timesheets = models.Timesheet.objects.filter(id__in=timesheet_pks, status=models.STATUS_PENDING)

    for timesheet in timesheets:
        timesheet.status = models.STATUS_ACTIVE
        timesheet.save()

    context = {
        'timesheets': timesheets,
    }

    if return_to_referer and request.META.get('HTTP_REFERER', None):
        return redirect(request.META.get('HTTP_REFERER'))

    return render(request, 'ninetofiver/admin/timesheets/activate.pug', context)


@staff_member_required
def admin_report_index_view(request):
    """Report index."""
    context = {
        'title': _('Reports'),
    }

    return render(request, 'ninetofiver/admin/reports/index.pug', context)


@staff_member_required
def admin_report_timesheet_contract_overview_view(request):
    """Timesheet contract overview report."""
    fltr = filters.AdminReportTimesheetContractOverviewFilter(request.GET, models.Timesheet.objects)
    timesheets = fltr.qs.select_related('user')

    contracts = (models.Contract.objects.all())

    try:
        contract_ids = list(map(int, request.GET.getlist('performance__contract', [])))
    except Exception:
        contract_ids = None
    try:
        contract_types = list(map(str, request.GET.getlist('performance__contract__polymorphic_ctype__model', [])))
    except Exception:
        contract_types = None
    try:
        contract_companies = list(map(int, request.GET.getlist('performance__contract__company', [])))
    except Exception:
        contract_companies = None
    try:
        contract_customers = list(map(int, request.GET.getlist('performance__contract__customer', [])))
    except Exception:
        contract_customers = None

    if contract_ids:
        contracts = contracts.filter(id__in=contract_ids)
    if contract_types:
        contracts = contracts.filter(polymorphic_ctype__model__in=contract_types)
    if contract_companies:
        contracts = contracts.filter(company__id__in=contract_companies)
    if contract_customers:
        contracts = contracts.filter(customer__id__in=contract_customers)

    contracts = contracts.values_list('id', flat=True)

    data = []
    for timesheet in timesheets:
        date_range = timesheet.get_date_range()
        range_info = calculation.get_range_info([timesheet.user], date_range[0], date_range[1], summary=True)

        for contract_performance in range_info[timesheet.user.id]['summary']['performances']:
            if (not contracts) or (contract_performance['contract'].id in contracts):
                data.append({
                    'contract': contract_performance['contract'],
                    'duration': contract_performance['duration'],
                    'standby_days': contract_performance['standby_days'],
                    'timesheet': timesheet,
                })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.TimesheetContractOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Timesheet contract overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/timesheet_contract_overview.pug', context)


@staff_member_required
def admin_report_timesheet_overview_view(request):
    """Timesheet overview report."""
    fltr = filters.AdminReportTimesheetOverviewFilter(request.GET, models.Timesheet.objects)
    timesheets = fltr.qs.select_related('user')

    data = []
    for timesheet in timesheets:
        date_range = timesheet.get_date_range()
        range_info = calculation.get_range_info([timesheet.user], date_range[0], date_range[1])
        range_info = range_info[timesheet.user.id]

        data.append({
            'timesheet': timesheet,
            'range_info': range_info,
        })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size * 4})
    table = tables.TimesheetOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Timesheet overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/timesheet_overview.pug', context)


@staff_member_required
def admin_report_user_range_info_view(request):
    """User range info report."""
    fltr = filters.AdminReportUserRangeInfoFilter(request.GET, models.Timesheet.objects.all())
    user = get_object_or_404(auth_models.User.objects,
                             pk=request.GET.get('user', None), is_active=True) if request.GET.get('user') else None
    from_date = parser.parse(request.GET.get('from_date', None)).date() if request.GET.get('from_date') else None
    until_date = parser.parse(request.GET.get('until_date', None)).date() if request.GET.get('until_date') else None

    data = []

    if user and from_date and until_date and (until_date >= from_date):
        range_info = calculation.get_range_info([user], from_date, until_date, daily=True)[user.id]

        for day in sorted(range_info['details'].keys()):
            day_detail = range_info['details'][day]
            data.append({
                'day_detail': day_detail,
                'date': parser.parse(day),
                'user': user,
            })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size * 2})
    table = tables.UserRangeInfoTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('User range info'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/user_range_info.pug', context)


@staff_member_required
def admin_report_user_leave_overview_view(request):
    """User leave overview report."""
    fltr = filters.AdminReportUserLeaveOverviewFilter(request.GET, models.LeaveDate.objects
                                                      .filter(leave__status=models.STATUS_APPROVED))
    user = get_object_or_404(auth_models.User.objects,
                             pk=request.GET.get('user', None), is_active=True) if request.GET.get('user') else None
    from_date = parser.parse(request.GET.get('from_date', None)).date() if request.GET.get('from_date') else None
    until_date = parser.parse(request.GET.get('until_date', None)).date() if request.GET.get('until_date') else None
    data = []

    if user and from_date and until_date and (until_date >= from_date):
        # Grab leave types, index them by ID
        leave_types = models.LeaveType.objects.all()

        # Grab leave dates, index them by year, then month, then leave type ID
        leave_dates = fltr.qs.filter().select_related('leave', 'leave__leave_type')
        leave_date_data = {}
        for leave_date in leave_dates:
            (leave_date_data
                .setdefault(leave_date.starts_at.year, {})
                .setdefault(leave_date.starts_at.month, {})
                .setdefault(leave_date.leave.leave_type.id, [])
                .append(leave_date))

        # Iterate over years, months to create monthly data
        current_date = copy.deepcopy(from_date)
        while current_date.strftime('%Y%m') <= until_date.strftime('%Y%m'):
            month_leave_dates = leave_date_data.get(current_date.year, {}).get(current_date.month, {})
            month_leave_type_hours = {}

            # Iterate over leave types to gather totals
            for leave_type in leave_types:
                duration = sum([Decimal(str(round((x.ends_at - x.starts_at).total_seconds() / 3600, 2)))
                                for x in month_leave_dates.get(leave_type.id, [])])
                month_leave_type_hours[leave_type.name] = duration

            data.append({
                'year': current_date.year,
                'month': current_date.month,
                'user': user,
                'leave_type_hours': month_leave_type_hours,
            })

            current_date += relativedelta(months=1)

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.UserLeaveOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('User leave overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/user_leave_overview.pug', context)


@staff_member_required
def admin_report_user_work_ratio_overview_view(request):
    """User work ratio overview report."""
    fltr = filters.AdminReportUserWorkRatioOverviewFilter(request.GET, models.Timesheet.objects)
    data = []

    if fltr.data.get('user', None) and fltr.data.get('year', None):
        year = int(fltr.data['year'])
        user = get_object_or_404(auth_models.User.objects,
                                 pk=request.GET.get('user', None), is_active=True) if request.GET.get('user') else None

        timesheets = fltr.qs.select_related('user')

        for timesheet in timesheets:
            date_range = timesheet.get_date_range()
            range_info = calculation.get_range_info([timesheet.user], date_range[0], date_range[1], summary=True)
            range_info = range_info[timesheet.user.id]

            total_hours = range_info['performed_hours'] + range_info['leave_hours']
            leave_hours = range_info['leave_hours']
            consultancy_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                    if x['contract'].get_real_instance_class() == models.ConsultancyContract])
            project_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                if x['contract'].get_real_instance_class() == models.ProjectContract])
            support_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                if x['contract'].get_real_instance_class() == models.SupportContract])

            consultancy_pct = round((consultancy_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            project_pct = round((project_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            support_pct = round((support_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            leave_pct = round((leave_hours / (total_hours if total_hours else 1.0)) * 100, 2)

            data.append({
                'year': timesheet.year,
                'month': timesheet.month,
                'user': timesheet.user,
                'total_hours': total_hours,
                'leave_hours': leave_hours,
                'consultancy_hours': consultancy_hours,
                'project_hours': project_hours,
                'support_hours': support_hours,
                'leave_pct': leave_pct,
                'consultancy_pct': consultancy_pct,
                'project_pct': project_pct,
                'support_pct': support_pct,
            })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.UserWorkRatioOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('User work ratio overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/user_work_ratio_overview.pug', context)


@staff_member_required
def admin_report_resource_availability_overview_view(request):
    """Resource availability overview report."""
    data = []
    fltr = filters.AdminReportResourceAvailabilityOverviewFilter(request.GET, models.Timesheet.objects)
    from_date = parser.parse(request.GET.get('from_date', None)).date() if request.GET.get('from_date') else None
    until_date = parser.parse(request.GET.get('until_date', None)).date() if request.GET.get('until_date') else None

    users = auth_models.User.objects.filter(is_active=True).distinct()
    try:
        user_ids = list(map(int, request.GET.getlist('user', [])))
        users = users.filter(id__in=user_ids) if user_ids else users
    except Exception:
        pass
    try:
        group_ids = list(map(int, request.GET.getlist('group', [])))
        users = users.filter(groups__in=group_ids) if group_ids else users
    except Exception:
        pass

    if users and from_date and until_date and (until_date >= from_date):
        dates = dates_in_range(from_date, until_date)

        # Fetch availability
        availability = calculation.get_availability_info(users, from_date, until_date)

        # Fetch contract user work schedules
        contract_user_work_schedules = (models.ContractUserWorkSchedule.objects
                                        .filter(contract_user__user__in=users)
                                        .filter(Q(ends_at__isnull=True, starts_at__lte=until_date) |
                                                Q(ends_at__isnull=False, starts_at__lte=until_date,
                                                  ends_at__gte=from_date))
                                        .select_related('contract_user', 'contract_user__user',
                                                        'contract_user__contract_role', 'contract_user__contract',
                                                        'contract_user__contract__customer'))
        # Index contract user work schedules by user
        contract_user_work_schedule_data = {}
        for contract_user_work_schedule in contract_user_work_schedules:
            (contract_user_work_schedule_data
                .setdefault(contract_user_work_schedule.contract_user.user.id, [])
                .append(contract_user_work_schedule))

        # Fetch employment contracts
        employment_contracts = (models.EmploymentContract.objects
                                .filter(
                                    (Q(ended_at__isnull=True) & Q(started_at__lte=until_date)) |
                                    (Q(started_at__lte=until_date) & Q(ended_at__gte=from_date)),
                                    user__in=users)
                                .order_by('started_at')
                                .select_related('user', 'company', 'work_schedule'))
        # Index employment contracts by user ID
        employment_contract_data = {}
        for employment_contract in employment_contracts:
            (employment_contract_data
                .setdefault(employment_contract.user.id, [])
                .append(employment_contract))

        # Iterate over users, days to create daily user data
        for user in users:
            user_data = {
                'user': user,
                'days': {},
            }
            data.append(user_data)

            for current_date in dates:
                date_str = str(current_date)
                user_day_data = user_data['days'][date_str] = {}

                day_availability = availability[str(user.id)][date_str]
                day_contract_user_work_schedules = []
                day_scheduled_hours = Decimal('0.00')
                day_work_hours = Decimal('0.00')

                # Get contract user work schedules for this day
                # This allows us to determine the scheduled hours for this user
                for contract_user_work_schedule in contract_user_work_schedule_data.get(user.id, []):
                    if (contract_user_work_schedule.starts_at <= current_date) and \
                            ((not contract_user_work_schedule.ends_at) or
                                (contract_user_work_schedule.ends_at >= current_date)):
                        day_contract_user_work_schedules.append(contract_user_work_schedule)
                        day_scheduled_hours += getattr(contract_user_work_schedule,
                                                       current_date.strftime('%A').lower(), Decimal('0.00'))

                # Get employment contract for this day
                # This allows us to determine the required hours for this user
                employment_contract = None
                try:
                    for ec in employment_contract_data[user.id]:
                        if (ec.started_at <= current_date) and ((not ec.ended_at) or (ec.ended_at >= current_date)):
                            employment_contract = ec
                            break
                except KeyError:
                    pass

                work_schedule = employment_contract.work_schedule if employment_contract else None
                if work_schedule:
                    day_work_hours = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal('0.00'))

                user_day_data['availability'] = day_availability
                user_day_data['contract_user_work_schedules'] = day_contract_user_work_schedules
                user_day_data['scheduled_hours'] = day_scheduled_hours
                user_day_data['work_hours'] = day_work_hours
                user_day_data['enough_hours'] = day_scheduled_hours >= day_work_hours

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size * 4})
    table = tables.ResourceAvailabilityOverviewTable(from_date, until_date, data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Resource availability overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/resource_availability_overview.pug', context)


@staff_member_required
def admin_report_expiring_consultancy_contract_overview_view(request):
    """User work ratio overview report."""
    fltr = filters.AdminReportUserWorkRatioOverviewFilter(request.GET, models.Timesheet.objects)
    data = []

    if fltr.data.get('user', None) and fltr.data.get('year', None):
        year = int(fltr.data['year'])
        user = get_object_or_404(auth_models.User.objects,
                                 pk=request.GET.get('user', None), is_active=True) if request.GET.get('user') else None

        timesheets = fltr.qs.select_related('user')

        for timesheet in timesheets:
            date_range = timesheet.get_date_range()
            range_info = calculation.get_range_info([timesheet.user], date_range[0], date_range[1], summary=True)
            range_info = range_info[timesheet.user.id]

            total_hours = range_info['performed_hours'] + range_info['leave_hours']
            leave_hours = range_info['leave_hours']
            consultancy_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                    if x['contract'].get_real_instance_class() == models.ConsultancyContract])
            project_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                if x['contract'].get_real_instance_class() == models.ProjectContract])
            support_hours = sum([x['duration'] for x in range_info['summary']['performances']
                                if x['contract'].get_real_instance_class() == models.SupportContract])

            consultancy_pct = round((consultancy_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            project_pct = round((project_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            support_pct = round((support_hours / (total_hours if total_hours else 1.0)) * 100, 2)
            leave_pct = round((leave_hours / (total_hours if total_hours else 1.0)) * 100, 2)

            data.append({
                'year': timesheet.year,
                'month': timesheet.month,
                'user': timesheet.user,
                'total_hours': total_hours,
                'leave_hours': leave_hours,
                'consultancy_hours': consultancy_hours,
                'project_hours': project_hours,
                'support_hours': support_hours,
                'leave_pct': leave_pct,
                'consultancy_pct': consultancy_pct,
                'project_pct': project_pct,
                'support_pct': support_pct,
            })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.UserWorkRatioOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Expiring consultancy contract overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/expiring_consultancy_contract_overview.pug', context)


@staff_member_required
def admin_report_project_contract_overview_view(request):
    """User work ratio overview report."""
    fltr = filters.AdminReportUserWorkRatioOverviewFilter(request.GET, models.Timesheet.objects)
    data = []

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.UserWorkRatioOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Project contract overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/project_contract_overview.pug', context)


class AdminTimesheetContractPdfExportView(BaseTimesheetContractPdfExportServiceAPIView):
    """Export a timesheet contract to PDF."""

    permission_classes = (permissions.IsAdminUser,)

    def resolve_user(self, context):
        return get_object_or_404(auth_models.User, pk=context.get('user_pk', None))


# API calls
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows users to be viewed."""
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.UserSerializer
    filter_class = filters.UserFilter
    queryset = (auth_models.User.objects.distinct().exclude(is_active=False).order_by('-date_joined')
                .select_related('userinfo').prefetch_related('groups'))


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows groups to be viewed."""

    queryset = auth_models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (permissions.IsAuthenticated,)


class CompanyViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows companies to be viewed."""

    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer
    filter_class = filters.CompanyFilter
    permission_classes = (permissions.IsAuthenticated,)


class EmploymentContractTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows employment contract types to be viewed."""

    queryset = models.EmploymentContractType.objects.all()
    serializer_class = serializers.EmploymentContractTypeSerializer
    filter_class = filters.EmploymentContractTypeFilter
    permission_classes = (permissions.IsAuthenticated,)


class UserRelativeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows user relatives to be viewed."""

    queryset = models.UserRelative.objects.all()
    serializer_class = serializers.UserRelativeSerializer
    filter_class = filters.UserRelativeFilter
    permission_classes = (permissions.IsAuthenticated,)


class HolidayViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows holidays to be viewed."""

    queryset = models.Holiday.objects.all()
    serializer_class = serializers.HolidaySerializer
    filter_class = filters.HolidayFilter
    permission_classes = (permissions.IsAuthenticated,)


class LeaveTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows leave types to be viewed."""

    queryset = models.LeaveType.objects.all()
    serializer_class = serializers.LeaveTypeSerializer
    filter_class = filters.LeaveTypeFilter
    permission_classes = (permissions.IsAuthenticated,)


class LeaveViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows leaves to be viewed."""

    queryset = models.Leave.objects.all()
    serializer_class = serializers.LeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated,)


class LeaveDateViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows leave dates to be viewed."""

    queryset = models.LeaveDate.objects.all()
    serializer_class = serializers.LeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated,)


class PerformanceTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows performance types to be viewed."""

    queryset = models.PerformanceType.objects.all()
    serializer_class = serializers.PerformanceTypeSerializer
    filter_class = filters.PerformanceTypeFilter
    permission_classes = (permissions.IsAuthenticated,)


class TimesheetViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows timesheets to be viewed."""

    queryset = models.Timesheet.objects.all()
    serializer_class = serializers.TimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class AttachmentViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows attachments to be viewed."""

    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class PerformanceViewSet(GenericHierarchicalReadOnlyViewSet):
    """API endpoint that allows performance to be viewed."""

    queryset = models.Performance.objects.all()
    serializer_class = serializers.PerformanceSerializer
    serializer_classes = {
        models.ActivityPerformance: serializers.ActivityPerformanceSerializer,
        models.StandbyPerformance: serializers.StandbyPerformanceSerializer,
    }
    filter_class = filters.PerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ActivityPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows activity performance to be viewed."""

    queryset = models.ActivityPerformance.objects.all()
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.ActivityPerformanceSerializer


class StandbyPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows consultancy standby performance to be viewed or edited."""

    queryset = models.StandbyPerformance.objects.all()
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.StandbyPerformanceSerializer


class EmploymentContractViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows employment contracts to be viewed."""

    queryset = models.EmploymentContract.objects.all()
    filter_class = filters.EmploymentContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.EmploymentContractSerializer


class WorkScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows work schedules to be viewed."""

    queryset = models.WorkSchedule.objects.all()
    filter_class = filters.WorkScheduleFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.WorkScheduleSerializer


class ContractViewSet(GenericHierarchicalReadOnlyViewSet):
    """API endpoint that allows contracts to be viewed."""

    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    serializer_classes = {
        models.ProjectContract: serializers.ProjectContractSerializer,
        models.ConsultancyContract: serializers.ConsultancyContractSerializer,
        models.SupportContract: serializers.SupportContractSerializer,
    }
    filter_class = filters.ContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ProjectContractViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows project contracts to be viewed."""

    queryset = models.ProjectContract.objects.all()
    filter_class = filters.ProjectContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.ProjectContractSerializer


class ConsultancyContractViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows consultancy contracts to be viewed or edited."""
    queryset = models.ConsultancyContract.objects.all()
    filter_class = filters.ConsultancyContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.ConsultancyContractSerializer


class SupportContractViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows support contracts to be viewed or edited."""

    queryset = models.SupportContract.objects.all()
    filter_class = filters.SupportContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)
    serializer_class = serializers.SupportContractSerializer


class ContractRoleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows contract roles to be viewed."""

    queryset = models.ContractRole.objects.all()
    serializer_class = serializers.ContractRoleSerializer
    filter_class = filters.ContractRoleFilter
    permission_classes = (permissions.IsAuthenticated,)


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows user info to be viewed."""

    queryset = models.UserInfo.objects.all()
    serializer_class = serializers.UserInfoSerializer
    filter_class = filters.UserInfoFilter
    permission_classes = (permissions.IsAuthenticated,)


class ContractUserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows contract users to be viewed."""

    queryset = models.ContractUser.objects.all()
    serializer_class = serializers.ContractUserSerializer
    filter_class = filters.ContractUserFilter
    permission_classes = (permissions.IsAuthenticated,)


class ContractGroupViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows contract groups to be viewed."""

    queryset = models.ContractGroup.objects.all()
    serializer_class = serializers.ContractGroupSerializer
    filter_class = filters.ContractGroupFilter
    permission_classes = (permissions.IsAuthenticated,)


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows locations to be viewed."""

    queryset = models.Location.objects.all()
    serializer_class = serializers.LocationSerializer
    filter_class = filters.LocationFilter
    permission_classes = (permissions.IsAuthenticated,)


class PerformanceImportServiceAPIView(APIView):
    """Gets performances from external sources and returns them to be imported."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        from_date = request.query_params.get('from', str(date.today()))
        to_date = request.query_params.get('to', str(date.today()))

        data = []

        # Redmine
        redmine_data = redmine.get_user_redmine_performances(request.user, from_date=from_date, to_date=to_date)
        data += redmine_data

        return Response(data)


class RangeAvailabilityServiceAPIView(APIView):
    """Get availability for all active users."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Defines the entrypoint of the retrieval."""
        from_date = parser.parse(request.query_params.get('from', None)).date()
        until_date = parser.parse(request.query_params.get('until', None)).date()

        users = auth_models.User.objects.filter(is_active=True)
        data = calculation.get_availability_info(users, from_date, until_date)

        return Response(data, status=status.HTTP_200_OK)


class RangeInfoServiceAPIView(APIView):
    """Calculates and returns information for a given date range."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Get date range information."""
        user = request.user

        from_date = parser.parse(request.query_params.get('from', None)).date()
        until_date = parser.parse(request.query_params.get('until', None)).date()
        daily = request.query_params.get('daily', 'false') == 'true'
        detailed = request.query_params.get('detailed', 'false') == 'true'
        summary = request.query_params.get('summary', 'false') == 'true'

        data = calculation.get_range_info([user], from_date, until_date, daily=daily, detailed=detailed,
                                          summary=summary, serialize=True)
        data = data[user.id]

        return Response(data)


class MyUserServiceAPIView(APIView):
    """Get the currently authenticated user."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        entity = request.user
        data = serializers.MyUserSerializer(entity, context={'request': request}).data

        return Response(data)


class LeaveRequestServiceAPIView(APIView):
    """Request leave for the given date range."""

    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, format=None):
        user = request.user
        leave_type = get_object_or_404(models.LeaveType, pk=request.data['leave_type'])
        description = request.data.get('description', None)
        full_day = request.data.get('full_day', False)

        starts_at = parser.parse(request.data['starts_at'])
        starts_at = timezone.make_aware(starts_at) if not timezone.is_aware(starts_at) else starts_at
        ends_at = parser.parse(request.data['ends_at'])
        ends_at = timezone.make_aware(ends_at) if not timezone.is_aware(ends_at) else ends_at

        # If the end date comes before the start date, NOPE
        if ends_at < starts_at:
            raise serializers.ValidationError(_('The end date should come after the start date.'))

        # Ensure we can roll back if something goes wrong
        with transaction.atomic():
            # Create leave
            leave = models.Leave.objects.create(user=user, description=description, leave_type=leave_type,
                                                status=models.STATUS_DRAFT)

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
                    current_dt = copy.deepcopy(starts_at) + timedelta(days=i)
                    current_date = current_dt.date()

                    # For the given date, determine the active work schedule
                    if ((not employment_contract) or (employment_contract.started_at > current_date) or
                            (employment_contract.ended_at and (employment_contract.ended_at < current_date))):
                        employment_contract = models.EmploymentContract.objects.filter(
                            Q(user=user, started_at__lte=current_date) &
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
                                                            second=0)
                        # Add work hours to pair start to obtain pair end
                        pair_ends_at = pair_starts_at.replace(hour=int(pair_starts_at.hour + work_hours),
                                                              minute=int((work_hours % 1) * 60))
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
                    timesheet, created = models.Timesheet.objects.get_or_create(user=user, year=pair[0].year,
                                                                                month=pair[0].month)

                models.LeaveDate.objects.create(leave=leave, timesheet=timesheet, starts_at=pair[0],
                                                ends_at=pair[1])

            # Mark leave as Pending
            leave.status = models.STATUS_PENDING
            leave.save()

        data = serializers.MyLeaveSerializer(leave, context={'request': request}).data

        return Response(data)


class MyTimesheetContractPdfExportServiceAPIView(BaseTimesheetContractPdfExportServiceAPIView):
    """Export a timesheet contract to PDF."""

    permission_classes = (permissions.IsAuthenticated,)

    def resolve_user(self, context):
        """Resolve the user for this export."""
        return context['view'].request.user


class MyLeaveViewSet(viewsets.ModelViewSet):
    """API endpoint that allows leaves for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyLeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.leave_set.all()


class MyLeaveDateViewSet(viewsets.ModelViewSet):
    """API endpoint that allows leave dates for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyLeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.LeaveDate.objects.filter(leave__user=user)


class MyTimesheetViewSet(viewsets.ModelViewSet):
    """API endpoint that allows timesheets for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyTimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.timesheet_set

    def perform_destroy(self, instance):
        if instance.status != models.STATUS_ACTIVE:
            raise serializers.ValidationError({'status': _('Only active timesheets can be deleted.')})

        return super().perform_destroy(instance)


class MyContractViewSet(GenericHierarchicalReadOnlyViewSet):
    """API endpoint that allows contracts for the currently authenticated user to be viewed."""

    serializer_class = serializers.ContractSerializer
    serializer_classes = {
        models.ProjectContract: serializers.ProjectContractSerializer,
        models.ConsultancyContract: serializers.ConsultancyContractSerializer,
        models.SupportContract: serializers.SupportContractSerializer,
    }
    filter_class = filters.ContractFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.Contract.objects.filter(contractuser__user=user).distinct()


class MyContractUserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows contract users for the currently authenticated user to be viewed."""

    serializer_class = serializers.MyContractUserSerializer
    filter_class = filters.ContractUserFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.ContractUser.objects.filter(user=user).distinct()


class MyPerformanceViewSet(GenericHierarchicalReadOnlyViewSet):
    """API endpoint that allows performances for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyPerformanceSerializer
    serializer_classes = {
        models.StandbyPerformance: serializers.MyStandbyPerformanceSerializer,
        models.ActivityPerformance: serializers.MyActivityPerformanceSerializer,
    }
    filter_class = filters.PerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.Performance.objects.filter(timesheet__user=user)


class MyActivityPerformanceViewSet(viewsets.ModelViewSet):
    """API endpoint that allows activity performances for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.ActivityPerformance.objects.filter(timesheet__user=user)


class MyStandbyPerformanceViewSet(viewsets.ModelViewSet):
    """API endpoint that allows standby performances for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyStandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.StandbyPerformance.objects.filter(timesheet__user=user)


class MyWhereaboutViewSet(viewsets.ModelViewSet):
    """API endpoint that allows whereabouts for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyWhereaboutSerializer
    filter_class = filters.WhereaboutFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.Whereabout.objects.filter(timesheet__user=user)


class MyAttachmentViewSet(viewsets.ModelViewSet):
    """API endpoint that allows attachments for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyAttachmentSerializer
    filter_class = filters.AttachmentFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.attachment_set.all()


class MyWorkScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint that allows workschedules for the currently authenticated user to be viewed or edited."""

    serializer_class = serializers.MyWorkScheduleSerializer
    filter_class = filters.WorkScheduleFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.WorkSchedule.objects.filter(employmentcontract__user=user)


class LeaveFeedServiceAPIView(APIView):
    """Get leave as an ICS feed."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        return feeds.LeaveFeed().__call__(request)


class UserLeaveFeedServiceAPIView(APIView):
    """Get leave for a specific user as an ICS feed."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, user_username=None, format=None):
        username = request.parser_context['kwargs'].get('user_username', None)
        user = get_object_or_404(auth_models.User, username=username, is_active=True) if username else request.user
        return feeds.UserLeaveFeed().__call__(request, user=user)
