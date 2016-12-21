import django_filters
from django_filters.rest_framework import FilterSet
from django.db.models import Func
from collections import Counter
from rest_framework import generics
from ninetofiver import models


class IsNull(Func):
    template = '%(expressions)s IS NULL'


class NullLastOrderingFilter(django_filters.OrderingFilter):
    def filter(self, qs, value):
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


class CompanyFilter(FilterSet):
    class Meta:
        model = models.Company
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'country': ['exact'],
            'vat_identification_number': ['exact', 'contains', 'icontains'],
            'address': ['exact', 'contains', 'icontains'],
            'internal': ['exact'],
        }


class EmploymentContractFilter(FilterSet):
    class Meta:
        model = models.EmploymentContract
        fields = {
            'started_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ended_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }


class WorkScheduleFilter(FilterSet):
    class Meta:
        model = models.WorkSchedule
        fields = {
            'label': ['exact', 'contains', 'icontains'],
        }


class UserRelativeFilter(FilterSet):
    class Meta:
        model = models.UserRelative
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'relation': ['exact', 'contains', 'icontains'],
            'birth_date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'gender': ['exact'],
        }


class HolidayFilter(FilterSet):
    class Meta:
        model = models.Holiday
        fields = {
            'name': ['exact', 'contains', 'icontains'],
            'date': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'country': ['exact'],
        }


class LeaveTypeFilter(FilterSet):
    class Meta:
        model = models.LeaveType
        fields = {
            'label': ['exact', 'contains', 'icontains'],
        }


class LeaveFilter(FilterSet):
    class Meta:
        model = models.Leave
        fields = {
            'status': ['exact'],
            'description': ['exact', 'contains', 'icontains'],
        }


class LeaveDateFilter(FilterSet):
    class Meta:
        model = models.LeaveDate
        fields = {
            'starts_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
            'ends_at': ['exact', 'gt', 'gte', 'lt', 'lte'],
        }
