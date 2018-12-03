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
from django.db.models import Q, F, Sum, Prefetch, DecimalField
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

    def resolve_user_timesheet_contracts(self, context):
        """Resolve the users, timesheets and contracts for this export."""
        raise NotImplementedError()

    def render_to_response(self, context, **response_kwargs):
        items = self.resolve_user_timesheet_contracts(context)
        ctx = {
            'items': [],
        }

        for item in items:
            item_ctx = {
                'user': item[0],
                'timesheet': item[1],
                'contract': item[2],
            }

            item_ctx['activity_performances'] = (models.ActivityPerformance.objects
                                                 .filter(timesheet=item_ctx['timesheet'],
                                                         contract=item_ctx['contract'])
                                                 .order_by('date')
                                                 .select_related('performance_type')
                                                 .all())
            item_ctx['total_performed_hours'] = sum([x.duration for x in item_ctx['activity_performances']])
            item_ctx['total_performed_days'] = round(item_ctx['total_performed_hours'] / 8, 2)

            item_ctx['total_normalized_performed_hours'] = sum([x.normalized_duration for x in item_ctx['activity_performances']])
            item_ctx['total_normalized_performed_days'] = round(item_ctx['total_normalized_performed_hours'] / 8, 2)

            item_ctx['standby_performances'] = (models.StandbyPerformance.objects
                                                .filter(timesheet=item_ctx['timesheet'], contract=item_ctx['contract'])
                                                .order_by('date')
                                                .all())
            item_ctx['total_standby_days'] = round(len(item_ctx['standby_performances']), 2)

            # Create a performances dict, indexed by date
            performances = {}
            [performances.setdefault(str(x.date), {}).setdefault('activity', []).append(x)
                for x in item_ctx['activity_performances']]
            [performances.setdefault(str(x.date), {}).setdefault('standby', []).append(x)
                for x in item_ctx['standby_performances']]
            # Sort performances dict by date
            item_ctx['performances'] = OrderedDict()
            for day in sorted(performances):
                item_ctx['performances'][day] = performances[day]

            ctx['items'].append(item_ctx)

        return super().render_to_response(ctx, **response_kwargs)


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


@login_required
def api_docs_view(request):
    """API docs view page."""
    context = {}
    return render(request, 'ninetofiver/api_docs/index.pug', context)


@login_required
def api_docs_redoc_view(request):
    """API docs redoc view page."""
    context = {}
    return render(request, 'ninetofiver/api_docs/redoc.pug', context)


@login_required
def api_docs_swagger_ui_view(request):
    """API docs swagger ui view page."""
    context = {}
    return render(request, 'ninetofiver/api_docs/swagger_ui.pug', context)


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
        'today': date.today(),
        'last_week': date.today() - relativedelta(weeks=1),
        'next_month': date.today() + relativedelta(months=1),
        'two_months_from_now': date.today() + relativedelta(months=2),
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
    try:
        contract_groups = list(map(int, request.GET.getlist('performance__contract__contract_groups', [])))
    except Exception:
        contract_groups = None

    if contract_ids:
        contracts = contracts.filter(id__in=contract_ids)
    if contract_types:
        contracts = contracts.filter(polymorphic_ctype__model__in=contract_types)
    if contract_companies:
        contracts = contracts.filter(company__id__in=contract_companies)
    if contract_customers:
        contracts = contracts.filter(customer__id__in=contract_customers)
    if contract_groups:
        contracts = contracts.filter(contract_groups__id__in=contract_groups)

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
    company = fltr.data.get('user__employmentcontract__company', None)
    year = int(fltr.data['year']) if fltr.data.get('year', None) else None
    month = int(fltr.data['month']) if fltr.data.get('month', None) else None

    # If we're filtering on company and period (year or year + month), ensure we're only showing timesheets
    # for users who worked at the company for the period we're filtering on
    if company and year:
        period_start, period_end = month_date_range(year, month) if month else (date(year, 1, 1), date(year, 12, 31))
        timesheets = timesheets.filter(Q(user__employmentcontract__ended_at__isnull=True,
                                         user__employmentcontract__started_at__lte=period_end) |
                                       Q(user__employmentcontract__ended_at__isnull=False,
                                         user__employmentcontract__ended_at__gte=period_start,
                                         user__employmentcontract__started_at__lte=period_end))

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
        # Grab timesheets, index them by year, month
        timesheets = (models.Timesheet.objects
                      .filter(user=user)
                      .filter(
                          Q(year=from_date.year, month__gte=from_date.year) |
                          Q(year__gt=from_date.year, year__lt=until_date.year) |
                          Q(year=until_date.year, month__lte=until_date.month)))
        timesheet_data = {}
        for timesheet in timesheets:
            timesheet_data.setdefault(timesheet.year, {})[timesheet.month] = timesheet

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
                'timesheet': timesheet_data.get(current_date.year, {}).get(current_date.month, None),
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

        timesheets = fltr.qs.select_related('user').order_by('year', 'month')

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

    try:
        contract_ids = list(map(int, request.GET.getlist('contract', [])))
        users = users.filter(contractuser__contract__in=contract_ids) if contract_ids else users
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
    """Expiring consultancy User work ratio overview report."""
    fltr = filters.AdminReportExpiringConsultancyContractOverviewFilter(request.GET,
                                                                        models.ConsultancyContract.objects)
    ends_at_lte = (parser.parse(request.GET.get('ends_at_lte', None)).date()
                   if request.GET.get('ends_at_lte') else None)
    remaining_hours_lte = (Decimal(request.GET.get('remaining_hours_lte'))
                           if request.GET.get('remaining_hours_lte') else None)
    remaining_days_lte = (Decimal(request.GET.get('remaining_days_lte'))
                          if request.GET.get('remaining_days_lte') else None)
    only_final = request.GET.get('only_final', 'false') == 'true'
    data = []

    if ends_at_lte or remaining_hours_lte or remaining_days_lte:
        # If remaining_days_lte * 8 is than remaining_hours_lte, use that instead
        if remaining_days_lte and ((not remaining_hours_lte) or ((remaining_days_lte * 8) < remaining_hours_lte)):
            remaining_hours_lte = remaining_days_lte * 8

        contracts = (models.ConsultancyContract.objects.all()
                     .select_related('customer')
                     .prefetch_related('contractuser_set', 'contractuser_set__contract_role', 'contractuser_set__user')
                     .filter(active=True)
                     # Ensure contracts without end date/duration are never shown, since they will never expire
                     .filter(Q(ends_at__isnull=False) | Q(duration__isnull=False))
                     # Ensure contracts where the internal company and the customer are the same are filtered out
                     # These are internal contracts to cover things such as meetings, talks, etc..
                     .exclude(customer=F('company')))

        for contract in contracts:
            alotted_hours = contract.duration
            performed_hours = (models.ActivityPerformance.objects
                               .filter(contract=contract)
                               .aggregate(performed_hours=Sum(F('duration') * F('performance_type__multiplier'))))['performed_hours']
            performed_hours = performed_hours if performed_hours else Decimal('0.00')
            remaining_hours = (alotted_hours - performed_hours) if alotted_hours else None

            if (((not ends_at_lte) or (not contract.ends_at) or (contract.ends_at > ends_at_lte)) and
                ((remaining_hours_lte is None) or (remaining_hours is None) or (remaining_hours > remaining_hours_lte))):
                continue

            for contract_user in contract.contractuser_set.all():
                # If we're only supposed to show final consultancy contracts for any given user
                # AND if the current contract actually has an end date,
                # ensure the user has no linked active consultancy contracts with a later end date
                if only_final and contract.ends_at:
                    final = (models.ConsultancyContract.objects
                             .filter(contractuser__user=contract_user.user, ends_at__isnull=False,
                                     ends_at__gte=contract.ends_at, active=True)
                             .exclude(id=contract.id)
                             .count()) == 0
                    if not final:
                        continue

                data.append({
                    'contract': contract,
                    'contract_user': contract_user,
                    'user': contract_user.user,
                    'alotted_hours': alotted_hours,
                    'performed_hours': performed_hours,
                    'remaining_hours': remaining_hours,
                })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.ExpiringConsultancyContractOverviewTable(data, order_by='ends_at')
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
    """Project contract overview report."""
    fltr = filters.AdminReportProjectContractOverviewFilter(request.GET, models.ProjectContract.objects)
    data = []

    if True in map(bool, list(fltr.data.values())):
        contracts = (fltr.qs.all()
                    .select_related('customer')
                    .prefetch_related('contractestimate_set', 'contractestimate_set__contract_role')
                    .filter(active=True)
                    # Ensure contracts where the internal company and the customer are the same are filtered out
                    # These are internal contracts to cover things such as meetings, talks, etc..
                    .exclude(customer=F('company')))

        for contract in contracts:
            # Keep track of totals
            performed_hours = Decimal('0.00')
            estimated_hours = Decimal('0.00')

            # List containing estimated and performed hours per role
            contract_role_data = {}
            # List containing performed hours per country
            country_data = {}
            # List containing performed hours per user
            user_data = {}

            # Fetch each performance for the contract, annotated with country
            performances = (models.ActivityPerformance.objects
                            .select_related('performance_type', 'contract_role', 'timesheet__user', 'timesheet__user__userinfo')
                            .filter(contract=contract))

            # Iterate over estimates to populate contract role data
            for contract_estimate in contract.contractestimate_set.all():
                estimated_hours += contract_estimate.duration

                if contract_estimate.contract_role:
                    contract_role_data[contract_estimate.contract_role.id] = {
                        'contract_role': contract_estimate.contract_role,
                        'performed_hours': Decimal('0.00'),
                        'estimated_hours': contract_estimate.duration,
                    }

            # Iterate over performance and fill in performed data
            for performance in performances:
                country = (performance.timesheet.user.userinfo.country
                        if (performance.timesheet.user.userinfo and performance.timesheet.user.userinfo.country)
                        else 'Other')
                if country not in country_data:
                    country_data[country] = {
                        'country': country,
                        'performed_hours': Decimal('0.00'),
                    }

                user = performance.timesheet.user
                if user.id not in user_data:
                    user_data[user.id] = {
                        'user': user,
                        'performed_hours': Decimal('0.00'),
                    }

                contract_role = performance.contract_role
                if contract_role.id not in contract_role_data:
                    contract_role_data[contract_role.id] = {
                        'contract_role': contract_role,
                        'performed_hours': Decimal('0.00'),
                        'estimated_hours': Decimal('0.00'),
                    }

                duration = performance.normalized_duration
                performed_hours += duration
                contract_role_data[performance.contract_role.id]['performed_hours'] += duration
                country_data[country]['performed_hours'] += duration
                user_data[user.id]['performed_hours'] += duration

            # Iterate over contract role, user, country data and calculate performed_pct
            for contract_role_id, item in contract_role_data.items():
                item['performed_pct'] = round((item['performed_hours'] / performed_hours) * 100, 2) if performed_hours else None
                item['estimated_pct'] = round((item['performed_hours'] / item['estimated_hours']) * 100, 2) if item['estimated_hours'] else None
            for user_id, item in user_data.items():
                item['performed_pct'] = round((item['performed_hours'] / performed_hours) * 100, 2) if performed_hours else None
            for country, item in country_data.items():
                item['performed_pct'] = round((item['performed_hours'] / performed_hours) * 100, 2) if performed_hours else None

            # Fetch invoiced amount
            invoiced_amount = (models.InvoiceItem.objects
                    .filter(invoice__contract=contract)
                    .aggregate(invoiced_amount=Sum(F('price') * F('amount'),
                                                   output_field=DecimalField(max_digits=9, decimal_places=2))))['invoiced_amount']
            invoiced_amount = invoiced_amount if invoiced_amount else Decimal('0.00')

            data.append({
                'contract': contract,
                'contract_roles': contract_role_data.values(),
                'countries': country_data.values(),
                'users': user_data.values(),
                'performed_hours': performed_hours,
                'estimated_hours': estimated_hours,
                'estimated_pct': round((performed_hours / estimated_hours) * 100, 2) if estimated_hours else None,
                'invoiced_amount': invoiced_amount,
                'invoiced_pct': round((invoiced_amount / contract.fixed_fee) * 100, 2) if contract.fixed_fee else None,
            })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.ProjectContractOverviewTable(data)
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


@staff_member_required
def admin_report_user_overtime_overview_view(request):
    """User overtime overview report."""
    fltr = filters.AdminReportUserOvertimeOverviewFilter(request.GET, models.LeaveDate.objects
                                                         .filter(leave__status=models.STATUS_APPROVED))
    user = get_object_or_404(auth_models.User.objects,
                             pk=request.GET.get('user', None), is_active=True) if request.GET.get('user') else None
    from_date = parser.parse(request.GET.get('from_date', None)).date() if request.GET.get('from_date') else None
    until_date = parser.parse(request.GET.get('until_date', None)).date() if request.GET.get('until_date') else None
    data = []

    overtime_leave_type_ids = list(models.LeaveType.objects.filter(overtime=True).values_list('id', flat=True))

    if user and from_date and until_date and (until_date >= from_date) and overtime_leave_type_ids:
        # Grab leave dates, index them by year, then month, then leave type ID
        leave_dates = fltr.qs.filter(leave__leave_type__id__in=overtime_leave_type_ids).select_related('leave')
        leave_date_data = {}
        for leave_date in leave_dates:
            (leave_date_data
                .setdefault(leave_date.starts_at.year, {})
                .setdefault(leave_date.starts_at.month, [])
                .append(leave_date))

        # Iterate over years, months to create monthly data
        current_date = copy.deepcopy(from_date)
        remaining_overtime_hours = Decimal('0.00')

        while current_date.strftime('%Y%m') <= until_date.strftime('%Y%m'):
            current_date_range = month_date_range(current_date.year, current_date.month)
            month_range_info = calculation.get_range_info([user], from_date=current_date_range[0],
                                                          until_date=current_date_range[1])

            overtime_hours = month_range_info[user.id]['overtime_hours']
            remaining_overtime_hours += overtime_hours

            remaining_hours = month_range_info[user.id]['remaining_hours']
            remaining_overtime_hours -= remaining_hours

            used_overtime_hours = sum([Decimal(str(round((x.ends_at - x.starts_at).total_seconds() / 3600, 2)))
                                      for x in leave_date_data.get(current_date.year, {}).get(current_date.month, {})])
            remaining_overtime_hours -= used_overtime_hours

            data.append({
                'year': current_date.year,
                'month': current_date.month,
                'user': user,
                'overtime_hours': overtime_hours,
                'remaining_hours': remaining_hours,
                'used_overtime_hours': used_overtime_hours,
                'remaining_overtime_hours': remaining_overtime_hours,
            })

            current_date += relativedelta(months=1)

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.UserOvertimeOverviewTable(data)
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('User overtime overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/user_overtime_overview.pug', context)


@staff_member_required
def admin_report_expiring_support_contract_overview_view(request):
    """Expiring support contract overview report."""
    fltr = filters.AdminReportExpiringSupportContractOverviewFilter(request.GET,
                                                                    models.SupportContract.objects)
    ends_at_lte = (parser.parse(request.GET.get('ends_at_lte', None)).date()
                   if request.GET.get('ends_at_lte') else None)
    data = []

    if ends_at_lte:
        contracts = (models.SupportContract.objects.all()
                     .select_related('customer')
                     .filter(active=True)
                     # Ensure contracts without end date/duration are never shown, since they will never expire
                     .filter(Q(ends_at__isnull=False, ends_at__lte=ends_at_lte))
                     # Ensure contracts where the internal company and the customer are the same are filtered out
                     # These are internal contracts to cover things such as meetings, talks, etc..
                     .exclude(customer=F('company')))

        for contract in contracts:
            performed_hours = (models.ActivityPerformance.objects
                               .filter(contract=contract)
                               .aggregate(performed_hours=Sum(F('duration') * F('performance_type__multiplier'))))['performed_hours']
            performed_hours = performed_hours if performed_hours else Decimal('0.00')

            data.append({
                'contract': contract,
                'performed_hours': performed_hours,
            })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.ExpiringSupportContractOverviewTable(data, order_by='ends_at')
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Expiring support contract overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/expiring_support_contract_overview.pug', context)


@staff_member_required
def admin_report_project_contract_budget_overview_view(request):
    """Project contract budget overview report."""
    fltr = filters.AdminReportProjectContractOverviewFilter(request.GET, models.ProjectContract.objects)
    data = []

    contracts = (fltr.qs.all()
                 .select_related('customer')
                 .filter(active=True)
                 # Ensure contracts where the internal company and the customer are the same are filtered out
                 # These are internal contracts to cover things such as meetings, talks, etc..
                 .exclude(customer=F('company')))

    for contract in contracts:
        performed_hours = (models.ActivityPerformance.objects
                            .filter(contract=contract)
                            .aggregate(performed_hours=Sum(F('duration') * F('performance_type__multiplier'))))['performed_hours']
        performed_hours = performed_hours if performed_hours else Decimal('0.00')

        estimated_hours = (models.ContractEstimate.objects
                            .filter(contract=contract)
                            .aggregate(estimated_hours=Sum('duration')))['estimated_hours']
        estimated_hours = estimated_hours if estimated_hours else Decimal('0.00')

        invoiced_amount = (models.InvoiceItem.objects
                            .filter(invoice__contract=contract)
                            .aggregate(invoiced_amount=Sum(F('price') * F('amount'),
                                        output_field=DecimalField(max_digits=9, decimal_places=2))))['invoiced_amount']
        invoiced_amount = invoiced_amount if invoiced_amount else Decimal('0.00')

        performance_cost = Decimal('0.00')

        data.append({
            'contract': contract,
            'performed_hours': performed_hours,
            'estimated_hours': estimated_hours,
            'estimated_pct': round((performed_hours / estimated_hours) * 100, 2) if estimated_hours else None,
            'invoiced_amount': invoiced_amount,
            'invoiced_pct': round((invoiced_amount / contract.fixed_fee) * 100, 2) if contract.fixed_fee else None,
            'performance_cost': performance_cost,
            'fixed_fee_pct': round((performance_cost / contract.fixed_fee) * 100, 2) if contract.fixed_fee else None,
        })

    config = RequestConfig(request, paginate={'per_page': pagination.CustomizablePageNumberPagination.page_size})
    table = tables.ProjectContractBudgetOverviewTable(data, order_by='-performed')
    config.configure(table)

    export_format = request.GET.get('_export', None)
    if TableExport.is_valid_format(export_format):
        exporter = TableExport(export_format, table)
        return exporter.response('table.{}'.format(export_format))

    context = {
        'title': _('Project contract budget overview'),
        'table': table,
        'filter': fltr,
    }

    return render(request, 'ninetofiver/admin/reports/project_contract_budget_overview.pug', context)


class AdminTimesheetContractPdfExportView(BaseTimesheetContractPdfExportServiceAPIView):
    """Export a timesheet contract to PDF."""

    permission_classes = (permissions.IsAdminUser,)

    def resolve_user_timesheet_contracts(self, context):
        """Resolve users, timesheets and contracts for this report."""
        data = context.get('user_timesheet_contract_pks', None)
        data = [list(map(int, x.split(':'))) for x in data.split(',')]

        for item in data:
            item[0] = get_object_or_404(auth_models.User.objects.filter().distinct(), pk=item[0])
            item[1] = get_object_or_404(models.Timesheet.objects.filter().distinct(), pk=item[1], user=item[0])
            item[2] = get_object_or_404(models.Contract.objects.filter().distinct(), pk=item[2])

        return data