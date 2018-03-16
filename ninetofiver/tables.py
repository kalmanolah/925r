"""Tables."""
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
import django_tables2 as tables
from django_tables2.utils import A


class BaseTable(tables.Table):
    """Base table."""

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
    actions = tables.Column(accessor='timesheet', orderable=False)

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
