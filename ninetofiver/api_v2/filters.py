"""925r API v2 filters."""
import datetime
import dateutil
import django_filters
import rest_framework_filters as filters
from django_filters.rest_framework import FilterSet
from django.db.models import Q, Func
from django.contrib.admin import widgets as admin_widgets
from django.contrib.auth import models as auth_models
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from ninetofiver import models


class IsNull(Func):
    """IsNull func."""
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
    """User filter."""

    order_fields = ('username', 'email', 'first_name', 'last_name',)
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
        }



class HolidayFilter(FilterSet):
    """Holiday filter."""

    order_fields = ('name', 'date', 'country')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Holiday
        fields = {
            'name': ['exact', 'icontains'],
            'date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'country': ['exact'],
        }


class ContractFilter(FilterSet):
    """Contract filter."""

    order_fields = ('name', 'active',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    type = django_filters.CharFilter('polymorphic_ctype__model', lookup_expr='iexact')

    class Meta:
        model = models.Contract
        fields = {
            'name': ['exact', 'icontains'],
            'active': ['exact',],
        }


class ContractUserFilter(FilterSet):
    """Contract user filter."""

    order_fields = ('contract')
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.ContractUser
        fields = {
            'contract': ['exact'],
        }


class TimesheetFilter(FilterSet):
    """Timesheet filter."""

    order_fields = ('year', 'month', 'status',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Timesheet
        fields = {
            'year': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'month': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'status': ['exact'],
        }


class LeaveFilter(FilterSet):
    """Leave filter."""

    def date_range_distinct(self, queryset, name, value):
        """Filters leaves between a given date range."""
        try:
            values = value.split(',')
            start_date = dateutil.parser.parse(values[0])
            end_date = dateutil.parser.parse(values[1])
        except Exception:
            raise ValidationError('Datetimes have to be in the correct \'YYYY-MM-DDTHH:mm:ss\' format.')

        return queryset.filter(leavedate__starts_at__range=(start_date, end_date)).distinct()

    order_fields = ('status',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    date__range = django_filters.CharFilter(method='date_range_distinct')

    class Meta:
        model = models.Leave
        fields = {
            'status': ['exact'],
            'description': ['exact', 'icontains'],
        }


class WhereaboutFilter(FilterSet):
    """Whereabout filter."""

    order_fields = ('starts_at',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Whereabout
        fields = {
            'location': ['exact'],
            'description': ['exact', 'icontains'],
            'starts_at': ['range'],
        }


class PerformanceFilter(FilterSet):
    """Performance filter."""

    order_fields = ('date',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    type = django_filters.CharFilter('polymorphic_ctype__model', lookup_expr='iexact')

    class Meta:
        model = models.Performance
        fields = {
            'date': ['exact', 'range',],
            'contract': ['exact'],
        }


class AttachmentFilter(FilterSet):
    """Attachment filter."""

    order_fields = ('name',)
    order_by = NullLastOrderingFilter(fields=order_fields)

    class Meta:
        model = models.Attachment
        fields = {
            'name': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'leave': ['exact',],
            'timesheet': ['exact',],
        }