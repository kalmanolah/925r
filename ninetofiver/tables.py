"""Tables."""
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables
from django_tables2.utils import A
from django_tables2.export.export import TableExport
from ninetofiver import models


class BaseTable(tables.Table):
    """Base table."""

    # export_formats = TableExport.FORMATS
    export_formats = [
        TableExport.CSV,
        TableExport.JSON,
        TableExport.ODS,
        TableExport.XLS,
    ]

    class Meta:
        template_name = 'django_tables2/bootstrap4.html'
        attrs = {'class': 'table table-bordered table-striped table-hover'}


class TimesheetContractOverviewTable(BaseTable):
    """Timesheet contract overview table."""

    class Meta(BaseTable.Meta):
        pass

    user = tables.LinkColumn(
        viewname='admin:auth_user_change',
        args=[A('timesheet.user.id')],
        accessor='timesheet.user',
        order_by=['timesheet.user.first_name', 'timesheet.user.last_name', 'timesheet.user.username']
    )
    timesheet = tables.LinkColumn(
        viewname='admin:ninetofiver_timesheet_change',
        args=[A('timesheet.id')],
        order_by=['timesheet.year', 'timesheet.month']
    )
    status = tables.Column(
        accessor='timesheet.status'
    )
    contract = tables.LinkColumn(
        viewname='admin:ninetofiver_contract_change',
        args=[A('contract.id')],
        order_by=['contract.name']
    )
    duration = tables.Column(verbose_name='Duration (hours)',
                             footer=lambda table: _('Total: %(amount)s') %
                             {'amount': sum(x['duration'] for x in table.data)})
    actions = tables.Column(accessor='timesheet', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []
        buttons.append(('<a class="button" href="%(url)s?' +
                        'contract__id__exact=%(contract)s&' +
                        'timesheet__user__id__exact=%(user)s&' +
                        'timesheet__year=%(year)s&' +
                        'timesheet__month=%(month)s">Details</a>') % {
            'url': reverse('admin:ninetofiver_performance_changelist'),
            'contract': record['contract'].id,
            'user': record['timesheet'].user.id,
            'year': record['timesheet'].year,
            'month': record['timesheet'].month,
        })
        buttons.append('<a class="button" href="%s">PDF</a>' % reverse('admin_timesheet_contract_pdf_export', kwargs={
            'timesheet_pk': record['timesheet'].id,
            'user_pk': record['timesheet'].user.id,
            'contract_pk': record['contract'].id,
        }))

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class TimesheetOverviewTable(BaseTable):
    """Timesheet overview table."""

    class Meta(BaseTable.Meta):
        pass

    user = tables.LinkColumn(
        viewname='admin:auth_user_change',
        args=[A('timesheet.user.id')],
        accessor='timesheet.user',
        order_by=['timesheet.user.first_name', 'timesheet.user.last_name', 'timesheet.user.username']
    )
    timesheet = tables.LinkColumn(
        viewname='admin:ninetofiver_timesheet_change',
        args=[A('timesheet.id')],
        order_by=['timesheet.year', 'timesheet.month']
    )
    status = tables.Column(
        accessor='timesheet.status'
    )
    work_hours = tables.Column(
        accessor='range_info.work_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['range_info']['work_hours'] for x in table.data)}
    )
    performed_hours = tables.Column(
        accessor='range_info.performed_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['range_info']['performed_hours'] for x in table.data)}
    )
    leave_hours = tables.Column(
        accessor='range_info.leave_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['range_info']['leave_hours'] for x in table.data)}
    )
    holiday_hours = tables.Column(
        accessor='range_info.holiday_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['range_info']['holiday_hours'] for x in table.data)}
    )
    remaining_hours = tables.Column(
        accessor='range_info.remaining_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['range_info']['remaining_hours'] for x in table.data)}
    )
    actions = tables.Column(accessor='timesheet', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        if record['timesheet'].status == models.STATUS_PENDING:
            buttons.append('<a class="button" href="%(url)s?return=true">Close</a>' % {
                'url': reverse('admin_timesheet_close', kwargs={'timesheet_pk': record['timesheet'].id}),
            })
            buttons.append('<a class="button" href="%(url)s?return=true">Reopen</a>' % {
                'url': reverse('admin_timesheet_activate', kwargs={'timesheet_pk': record['timesheet'].id}),
            })

        from_date, until_date = record['timesheet'].get_date_range()

        buttons.append(('<a class="button" href="%(url)s?' +
                        'user=%(user)s&' +
                        'from_date=%(from_date)s&' +
                        'until_date=%(until_date)s">Details</a>') % {
            'url': reverse('admin_report_user_range_info'),
            'user': record['timesheet'].user.id,
            'from_date': from_date.strftime('%Y-%m-%d'),
            'until_date': until_date.strftime('%Y-%m-%d'),
        })

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class UserRangeInfoTable(BaseTable):
    """User range info table."""

    class Meta(BaseTable.Meta):
        pass

    date = tables.DateColumn('D d F')
    work_hours = tables.Column(
        accessor='day_detail.work_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['work_hours'] for x in table.data)}
    )
    performed_hours = tables.Column(
        accessor='day_detail.performed_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['performed_hours'] for x in table.data)}
    )
    leave_hours = tables.Column(
        accessor='day_detail.leave_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['leave_hours'] for x in table.data)}
    )
    holiday_hours = tables.Column(
        accessor='day_detail.holiday_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['holiday_hours'] for x in table.data)}
    )
    remaining_hours = tables.Column(
        accessor='day_detail.remaining_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['remaining_hours'] for x in table.data)}
    )
    overtime_hours = tables.Column(
        accessor='day_detail.overtime_hours',
        footer=lambda table: _('Total: %(amount)s') % {'amount':
                                                       sum(x['day_detail']['overtime_hours'] for x in table.data)}
    )
    actions = tables.Column(accessor='date', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        if record['day_detail']['performed_hours']:
            buttons.append(('<a class="button" href="%(url)s?' +
                            'timesheet__user__id__exact=%(user)s&' +
                            'timesheet__year=%(year)s&' +
                            'timesheet__month=%(month)s&' +
                            'day=%(day)s">Performance</a>') % {
                'url': reverse('admin:ninetofiver_performance_changelist'),
                'user': record['user'].id,
                'year': record['date'].year,
                'month': record['date'].month,
                'day': record['date'].day,
            })

        if record['day_detail']['holiday_hours']:
            buttons.append(('<a class="button" href="%(url)s?' +
                            'date__gte=%(date)s&' +
                            'date__lte=%(date)s">Holidays</a>') % {
                'url': reverse('admin:ninetofiver_holiday_changelist'),
                'date': record['date'].strftime('%Y-%m-%d'),
            })

        if record['day_detail']['leave_hours']:
            buttons.append(('<a class="button" href="%(url)s?' +
                            'user__id__exact=%(user)s&' +
                            'status__exact=%(status)s&' +
                            'leavedate__starts_at__gte_0=%(leavedate__starts_at__gte_0)s&' +
                            'leavedate__starts_at__gte_1=%(leavedate__starts_at__gte_1)s&' +
                            'leavedate__starts_at__lte_0=%(leavedate__starts_at__lte_0)s&' +
                            'leavedate__starts_at__lte_1=%(leavedate__starts_at__lte_1)s">Leave</a>') % {
                'url': reverse('admin:ninetofiver_leave_changelist'),
                'user': record['user'].id,
                'status': models.STATUS_APPROVED,
                'leavedate__starts_at__gte_0': record['date'].strftime('%Y-%m-%d'),
                'leavedate__starts_at__gte_1': '00:00:00',
                'leavedate__starts_at__lte_0': record['date'].strftime('%Y-%m-%d'),
                'leavedate__starts_at__lte_1': '23:59:59',
            })

        return format_html('%s' % ('&nbsp;'.join(buttons)))
