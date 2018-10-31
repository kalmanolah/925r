"""Tables."""
import uuid
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables
from django_tables2.utils import A
from django_tables2.export.export import TableExport
from ninetofiver import models
from ninetofiver.utils import month_date_range, format_duration, dates_in_range


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
        attrs = {'class': 'table table-bordered table-striped table-hover', 'container': 'table-responsive'}


class HoursColumn(tables.Column):
    """Hours column."""

    def render(self, value):
        """Render the value."""
        res = format_duration(value)

        if not value:
            res = format_html('<span style="color:#999;">{}</span>', res)

        return res

    def value(self, value):
        """Return the value."""
        return value


class BarChartComparisonColumn(tables.TemplateColumn):
    """Bar chart comparison column."""

    def __init__(self, dataset=[], yLabel=None, **kwargs):
        """Constructor."""
        kwargs['template_name'] = 'ninetofiver/admin/reports/bar_chart_comparison_column.pug'
        kwargs['extra_context'] = {
            'yLabel': yLabel,
            'dataset': dataset,
        }

        super().__init__(**kwargs)

    def render(self, record, table, value, bound_column, **kwargs):
        self.extra_context['uniqueId'] = str(uuid.uuid4())

        for item in self.extra_context['dataset']:
            if item.get('accessor', None):
                item['value'] = item['accessor'].resolve(record)

        self.extra_context['title'] = '%s vs. %s: %s' % (self.extra_context['dataset'][0]['label'],
                                                         self.extra_context['dataset'][1]['label'],
                                                         ('%s%%' % round((self.extra_context['dataset'][0]['value'] / self.extra_context['dataset'][1]['value']) * 100, 2) \
                                                          if self.extra_context['dataset'][1]['value'] else 'n/a'))

        return super().render(record, table, value, bound_column, **kwargs)

    def value(self, record, table, value, bound_column, **kwargs):
        return bound_column.accessor.resolve(record)

    def render_footer(self, table, column, bound_column, **kwargs):
        self.extra_context['uniqueId'] = str(uuid.uuid4())

        for item in self.extra_context['dataset']:
            if item.get('accessor', None):
                item['value'] = sum([item['accessor'].resolve(record) for record in table.data])

        self.extra_context['title'] = 'Total: %s vs. %s: %s' % (self.extra_context['dataset'][0]['label'],
                                                         self.extra_context['dataset'][1]['label'],
                                                         ('%s%%' % round((self.extra_context['dataset'][0]['value'] / self.extra_context['dataset'][1]['value']) * 100, 2) \
                                                          if self.extra_context['dataset'][1]['value'] else 'n/a'))

        return super().render(None, table, None, bound_column, bound_row=tables.rows.BoundRow(None, table))


class SummedHoursColumn(HoursColumn):
    """Summed hours column."""

    def render_footer(self, table, column, bound_column):
        """Render the footer."""
        accessor = self.accessor if self.accessor else A(bound_column.name)
        total = [accessor.resolve(x) for x in table.data]
        total = sum([x for x in total if x is not None])
        return format_html(_('Total: {}'), self.render(total))


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
    duration = SummedHoursColumn(verbose_name='Duration (hours)')
    standby_days = tables.Column()

    def render_actions_footer(table, column, bound_column):
        buttons = []

        if table.data:
            # Determine filters for given data
            query = []
            years = []
            months = []
            users = []
            contracts = []
            for record in table.data:
                if record['timesheet'].year not in years:
                    years.append(record['timesheet'].year)
                if record['timesheet'].month not in months:
                    months.append(record['timesheet'].month)
                if record['timesheet'].user.id not in users:
                    users.append(record['timesheet'].user.id)
                if record['contract'].id not in contracts:
                    contracts.append(record['contract'].id)
            if years:
                query.append('timesheet__year__in=%s' % (','.join(map(str, years))))
            if months:
                query.append('timesheet__month__in=%s' % (','.join(map(str, months))))
            if users:
                query.append('timesheet__user__id__in=%s' % (','.join(map(str, users))))
            if contracts:
                query.append('contract__id__in=%s' % (','.join(map(str, contracts))))

            buttons.append(('<a class="button" href="%(url)s?%(query)s">Details</a>') % {
                'url': reverse('admin:ninetofiver_performance_changelist'),
                'query': '&'.join(query),
            })

            pks = ','.join(['%s:%s:%s' % (x['timesheet'].user.id, x['timesheet'].id, x['contract'].id)
                            for x in table.data])
            buttons.append('<a class="button" href="%s">PDF</a>' % reverse('admin_timesheet_contract_pdf_export',
                           kwargs={'user_timesheet_contract_pks': pks}))

        return format_html('%s' % ('&nbsp;'.join(buttons)))

    actions = tables.Column(accessor='timesheet', orderable=False, exclude_from_export=True,
                            footer=render_actions_footer)

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
            'user_timesheet_contract_pks': '%s:%s:%s' % (record['timesheet'].user.id, record['timesheet'].id,
                                                         record['contract'].id),
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
    status = tables.Column(accessor='timesheet.status')
    work_hours = SummedHoursColumn(accessor='range_info.work_hours')
    performed_hours = SummedHoursColumn(accessor='range_info.performed_hours')
    leave_hours = SummedHoursColumn(accessor='range_info.leave_hours')
    holiday_hours = SummedHoursColumn(accessor='range_info.holiday_hours')
    remaining_hours = SummedHoursColumn(accessor='range_info.remaining_hours')
    attachments = tables.Column(accessor='timesheet.attachments', orderable=False)
    actions = tables.Column(accessor='timesheet', orderable=False, exclude_from_export=True)

    def render_attachments(self, record):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(record['timesheet'].attachments.all())))

    def value_attachments(self, record):
        return format_html('\n'.join('%s|%s'
                           % (x.get_file_url(), str(x)) for x in list(record['timesheet'].attachments.all())))

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
    work_hours = SummedHoursColumn(accessor='day_detail.work_hours')
    performed_hours = SummedHoursColumn(accessor='day_detail.performed_hours')
    leave_hours = SummedHoursColumn(accessor='day_detail.leave_hours')
    holiday_hours = SummedHoursColumn(accessor='day_detail.holiday_hours')
    remaining_hours = SummedHoursColumn(accessor='day_detail.remaining_hours')
    overtime_hours = SummedHoursColumn(accessor='day_detail.overtime_hours')
    actions = tables.Column(accessor='date', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        if record['day_detail']['performed_hours']:
            buttons.append(('<a class="button" href="%(url)s?' +
                            'timesheet__user__id__exact=%(user)s&' +
                            'timesheet__year=%(year)s&' +
                            'timesheet__month=%(month)s&' +
                            'date__lte=%(date)s&' +
                            'date__gte=%(date)s">Performance</a>') % {
                'url': reverse('admin:ninetofiver_performance_changelist'),
                'user': record['user'].id,
                'year': record['date'].year,
                'month': record['date'].month,
                'date': record['date'].strftime('%Y-%m-%d'),
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


class UserLeaveOverviewTable(BaseTable):
    """User leave overview table."""

    class Meta(BaseTable.Meta):
        pass

    year = tables.Column()
    month = tables.Column()
    timesheet_status = tables.Column(accessor='timesheet.status')
    actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def __init__(self, *args, **kwargs):
        """Constructor."""
        # Create an additional column for every leave type
        extra_columns = []
        for leave_type in models.LeaveType.objects.order_by('name'):
            column = SummedHoursColumn(accessor=A('leave_type_hours.%s' % leave_type.name))
            extra_columns.append([leave_type.name, column])
        kwargs['extra_columns'] = extra_columns
        kwargs['sequence'] = ('year', 'month', '...', 'actions')
        super().__init__(*args, **kwargs)

    def render_actions(self, record):
        buttons = []

        date_range = month_date_range(record['year'], record['month'])

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
            'leavedate__starts_at__gte_0': date_range[0].strftime('%Y-%m-%d'),
            'leavedate__starts_at__gte_1': '00:00:00',
            'leavedate__starts_at__lte_0': date_range[1].strftime('%Y-%m-%d'),
            'leavedate__starts_at__lte_1': '23:59:59',
        })

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class UserWorkRatioOverviewTable(BaseTable):
    """User work ratio overview table."""

    class Meta(BaseTable.Meta):
        pass

    year = tables.Column()
    month = tables.Column()
    total_hours = SummedHoursColumn()
    consultancy_hours = SummedHoursColumn()
    project_hours = SummedHoursColumn()
    support_hours = SummedHoursColumn()
    leave_hours = SummedHoursColumn()
    consultancy_pct = tables.Column(attrs={'th': {'class': 'bg-success'}})
    project_pct = tables.Column(attrs={'th': {'class': 'bg-info'}})
    support_pct = tables.Column(attrs={'th': {'class': 'bg-warning'}})
    leave_pct = tables.Column(attrs={'th': {'class': 'bg-secondary'}})
    ratio = tables.Column(accessor='user', orderable=False, exclude_from_export=True)
    actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def render_ratio(self, record):
        res = ('<div class="progress" style="min-width: 300px;">' +
               '<div class="progress-bar bg-success" role="progressbar" style="width: %(consultancy_pct)s%%">%(consultancy_pct)s%%</div>' +
               '<div class="progress-bar bg-info" role="progressbar" style="width: %(project_pct)s%%">%(project_pct)s%%</div>' +
               '<div class="progress-bar bg-warning" role="progressbar" style="width: %(support_pct)s%%">%(support_pct)s%%</div>' +
               '<div class="progress-bar bg-secondary" role="progressbar" style="width: %(leave_pct)s%%">%(leave_pct)s%%</div>' +
               '</div>') % record

        return format_html(res)

    def render_actions(self, record):
        buttons = []

        date_range = month_date_range(record['year'], record['month'])

        if record['consultancy_hours'] or record['project_hours'] or record['support_hours']:
            buttons.append(('<a class="button" href="%(url)s?' +
                            'timesheet__user__id__exact=%(user)s&' +
                            'timesheet__year=%(year)s&' +
                            'timesheet__month=%(month)s">Performance</a>') % {
                'url': reverse('admin:ninetofiver_performance_changelist'),
                'user': record['user'].id,
                'year': record['year'],
                'month': record['month'],
            })

        if record['leave_hours']:
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
                'leavedate__starts_at__gte_0': date_range[0].strftime('%Y-%m-%d'),
                'leavedate__starts_at__gte_1': '00:00:00',
                'leavedate__starts_at__lte_0': date_range[1].strftime('%Y-%m-%d'),
                'leavedate__starts_at__lte_1': '23:59:59',
            })

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class ResourceAvailabilityDayColumn(tables.TemplateColumn):
    """Resource availability day column."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        kwargs['template_name'] = 'ninetofiver/admin/reports/resource_availability_overview_day.pug'
        super().__init__(*args, **kwargs)


class ResourceAvailabilityOverviewTable(BaseTable):
    """Resource availability overview table."""

    export_formats = []

    class Meta(BaseTable.Meta):
        pass

    user = tables.LinkColumn(
        viewname='admin:auth_user_change',
        args=[A('user.id')],
        accessor='user',
        order_by=['user.first_name', 'user.last_name', 'user.username']
    )

    def __init__(self, from_date, until_date, *args, **kwargs):
        """Constructor."""
        # Create an additional column for every leave type
        extra_columns = []
        if from_date and until_date:
            for day_date in dates_in_range(from_date, until_date):
                date_str = str(day_date)
                column = ResourceAvailabilityDayColumn(accessor=A('days.%s' % date_str), orderable=False)
                extra_columns.append([day_date.strftime('%a, %d %b'), column])
        kwargs['extra_columns'] = extra_columns
        kwargs['sequence'] = ('user', '...')
        super().__init__(*args, **kwargs)


class ExpiringConsultancyContractOverviewTable(BaseTable):
    """Expiring consultancy contract overview table."""

    class Meta(BaseTable.Meta):
        pass

    user = tables.LinkColumn(
        viewname='admin:auth_user_change',
        args=[A('user.id')],
        accessor='contract_user',
        order_by=['user.first_name', 'user.last_name', 'user.username']
    )
    contract = tables.LinkColumn(
        viewname='admin:ninetofiver_contract_change',
        args=[A('contract.id')],
        accessor='contract',
        order_by=['contract.name']
    )
    starts_at = tables.DateColumn('D d F', accessor='contract.starts_at')
    ends_at = tables.DateColumn('D d F', accessor='contract.ends_at')
    alotted_hours = SummedHoursColumn(accessor='alotted_hours')
    performed_hours = SummedHoursColumn(accessor='performed_hours')
    remaining_hours = SummedHoursColumn(accessor='remaining_hours')
    # actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class ProjectContractOverviewTable(BaseTable):
    """Project contract overview table."""

    export_formats = []

    class Meta(BaseTable.Meta):
        pass

    contract = tables.LinkColumn(
        viewname='admin:ninetofiver_contract_change',
        args=[A('contract.id')],
        accessor='contract',
        order_by=['contract.name'],
        attrs={
            'th': {
                'style': 'width: 15%; min-width: 150px;'
            }
        }
    )
    data = tables.TemplateColumn(template_name='ninetofiver/admin/reports/project_data.pug', accessor='', orderable=False)

    # actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class UserOvertimeOverviewTable(BaseTable):
    """User overtime overview table."""

    class Meta(BaseTable.Meta):
        pass

    year = tables.Column()
    month = tables.Column()
    remaining_hours = HoursColumn()
    overtime_hours = SummedHoursColumn()
    used_overtime_hours = SummedHoursColumn()
    remaining_overtime_hours = HoursColumn()
    actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        date_range = month_date_range(record['year'], record['month'])

        buttons.append(('<a class="button" href="%(url)s?' +
                        'user=%(user)s&' +
                        'from_date=%(from_date)s&' +
                        'until_date=%(until_date)s">Details</a>') % {
            'url': reverse('admin_report_user_range_info'),
            'user': record['user'].id,
            'from_date': date_range[0].strftime('%Y-%m-%d'),
            'until_date': date_range[1].strftime('%Y-%m-%d'),
        })

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class ExpiringSupportContractOverviewTable(BaseTable):
    """Expiring support contract overview table."""

    class Meta(BaseTable.Meta):
        pass

    contract = tables.LinkColumn(
        viewname='admin:ninetofiver_contract_change',
        args=[A('contract.id')],
        accessor='contract',
        order_by=['contract.name']
    )
    starts_at = tables.DateColumn('D d F', accessor='contract.starts_at')
    ends_at = tables.DateColumn('D d F', accessor='contract.ends_at')
    performed_hours = SummedHoursColumn(accessor='performed_hours')
    day_rate = tables.Column(accessor='contract.day_rate')
    fixed_fee = tables.Column(accessor='contract.fixed_fee')
    fixed_fee_period = tables.Column(accessor='contract.fixed_fee_period')
    # actions = tables.Column(accessor='user', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        return format_html('%s' % ('&nbsp;'.join(buttons)))


class ProjectContractBudgetOverviewTable(BaseTable):
    """Project contract budget overview table."""

    export_formats = []

    class Meta(BaseTable.Meta):
        pass

    contract = tables.LinkColumn(
        viewname='admin:ninetofiver_contract_change',
        args=[A('contract.id')],
        accessor='contract',
        order_by=['contract.name'],
        attrs={
            'th': {
                'style': 'width: 15%; min-width: 150px;'
            }
        }
    )
    performed = BarChartComparisonColumn(yLabel='Hours', accessor='estimated_pct', dataset=[{
        'label': 'Performed hours',
        'accessor': A('performed_hours')
    }, {
        'label': 'Estimated hours',
        'accessor': A('estimated_hours')
    }])
    profit = BarChartComparisonColumn(yLabel='Cost (€)', accessor='fixed_fee_pct', dataset=[{
        'label': 'Performance cost',
        'accessor': A('performance_cost')
    }, {
        'label': 'Fixed fee',
        'accessor': A('contract.fixed_fee')
    }])
    invoiced = BarChartComparisonColumn(yLabel='Cost (€)', accessor='invoiced_pct', dataset=[{
        'label': 'Invoiced amount',
        'accessor': A('invoiced_amount')
    }, {
        'label': 'Fixed fee',
        'accessor': A('contract.fixed_fee')
    }])
    actions = tables.Column(accessor='contract', orderable=False, exclude_from_export=True)

    def render_actions(self, record):
        buttons = []

        buttons.append(('<a class="button" href="%(url)s?' +
                        'contract=%(contract)s">Details</a>') % {
            'url': reverse('admin_report_project_contract_overview'),
            'contract': record['contract'].id,
        })

        return format_html('%s' % ('&nbsp;'.join(buttons)))