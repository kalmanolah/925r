from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.db import transaction
from decimal import Decimal
from django.utils import timezone
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
from ninetofiver.utils import days_in_month
from ninetofiver import settings
from django.db.models import Q
from datetime import datetime, date, timedelta
from wkhtmltopdf.views import PDFTemplateView
from dateutil import parser
import logging
import copy


logger = logging.getLogger(__name__)


def home_view(request):
    """Homepage."""
    context = {}
    return render(request, 'ninetofiver/home/index.pug', context)


@login_required
def account_view(request):
    """User-specific account page."""
    context = {}
    return render(request, 'ninetofiver/account/index.pug', context)


@staff_member_required
def admin_leave_approve_view(request, leave_pk):
    """Approve the selected leaves."""
    leave_pks = list(map(int, leave_pk.split(',')))
    return_to_referer = request.GET.get('return', 'fase').lower() == 'true'

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
    return_to_referer = request.GET.get('return', 'fase').lower() == 'true'

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


@api_view(exclude_from_schema=True)
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer, CoreJSONRenderer])
@permission_classes((permissions.IsAuthenticated,))
def schema_view(request):
    """API documentation."""
    generator = schemas.SchemaGenerator(title='Ninetofiver API')
    return response.Response(generator.get_schema(request=request))


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = auth_models.User.objects.distinct().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    filter_class = filters.UserFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = auth_models.Group.objects.all()
    serializer_class = serializers.GroupSerializer
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows companies to be viewed or edited.
    """
    queryset = models.Company.objects.all()
    serializer_class = serializers.CompanySerializer
    filter_class = filters.CompanyFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class EmploymentContractTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employment contract types to be viewed or edited.
    """
    queryset = models.EmploymentContractType.objects.all()
    serializer_class = serializers.EmploymentContractTypeSerializer
    filter_class = filters.EmploymentContractTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class EmploymentContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employment contracts to be viewed or edited.
    """
    queryset = models.EmploymentContract.objects.all()
    serializer_class = serializers.EmploymentContractSerializer
    filter_class = filters.EmploymentContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class WorkScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows workschedules to be viewed or edited.
    """
    queryset = models.WorkSchedule.objects.all()
    serializer_class = serializers.WorkScheduleSerializer
    filter_class = filters.WorkScheduleFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class UserRelativeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user relatives to be viewed or edited.
    """
    queryset = models.UserRelative.objects.all()
    serializer_class = serializers.UserRelativeSerializer
    filter_class = filters.UserRelativeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class HolidayViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows holidays to be viewed or edited.
    """
    queryset = models.Holiday.objects.all()
    serializer_class = serializers.HolidaySerializer
    filter_class = filters.HolidayFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave types to be viewed or edited.
    """
    queryset = models.LeaveType.objects.all()
    serializer_class = serializers.LeaveTypeSerializer
    filter_class = filters.LeaveTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leaves to be viewed or edited.
    """
    queryset = models.Leave.objects.all()
    serializer_class = serializers.LeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveDateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave dates to be viewed or edited.
    """
    queryset = models.LeaveDate.objects.all()
    serializer_class = serializers.LeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class PerformanceTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows performance types to be viewed or edited.
    """
    queryset = models.PerformanceType.objects.all()
    serializer_class = serializers.PerformanceTypeSerializer
    filter_class = filters.PerformanceTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractViewSet(GenericHierarchicalReadOnlyViewSet):
    """
    API endpoint that allows contracts to be viewed or edited.
    """
    queryset = models.Contract.objects.all()
    serializer_class = serializers.ContractSerializer
    serializer_classes = {
        models.ProjectContract: serializers.ProjectContractSerializer,
        models.ConsultancyContract: serializers.ConsultancyContractSerializer,
        models.SupportContract: serializers.SupportContractSerializer,
    }
    filter_class = filters.ContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ProjectContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows project contracts to be viewed or edited.
    """
    queryset = models.ProjectContract.objects.all()
    filter_class = filters.ProjectContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_serializer_class(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return serializers.AdminProjectContractSerializer
        return serializers.ProjectContractSerializer


class ConsultancyContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows consultancy contracts to be viewed or edited.
    """
    queryset = models.ConsultancyContract.objects.all()
    filter_class = filters.ConsultancyContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_serializer_class(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return serializers.AdminConsultancyContractSerializer
        return serializers.ConsultancyContractSerializer


class SupportContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows support contracts to be viewed or edited.
    """
    queryset = models.SupportContract.objects.all()
    filter_class = filters.SupportContractFilter
    permission_classes = (permissions.DjangoModelPermissions,)

    def get_serializer_class(self):
        if self.request.user.is_superuser or self.request.user.is_staff:
            return serializers.AdminSupportContractSerializer
        return serializers.SupportContractSerializer


class ContractRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract roles to be viewed or edited.
    """
    queryset = models.ContractRole.objects.all()
    serializer_class = serializers.ContractRoleSerializer
    filter_class = filters.ContractRoleFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class UserInfoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows user infos be viewed or edited.
    """
    queryset = models.UserInfo.objects.all()
    serializer_class = serializers.UserInfoSerializer
    filter_class = filters.UserInfoFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract users to be viewed or edited.
    """
    queryset = models.ContractUser.objects.all()
    serializer_class = serializers.ContractUserSerializer
    filter_class = filters.ContractUserFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract groups to be viewed or edited.
    """
    queryset = models.ContractGroup.objects.all()
    serializer_class = serializers.ContractGroupSerializer
    filter_class = filters.ContractGroupFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ProjectEstimateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows project estimates to be viewed or edited.
    """
    queryset = models.ProjectEstimate.objects.all()
    serializer_class = serializers.ProjectEstimateSerializer
    filter_class = filters.ProjectEstimateFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class TimesheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows timesheets to be viewed or edited.
    """
    queryset = models.Timesheet.objects.exclude(status = models.STATUS_CLOSED)
    serializer_class = serializers.TimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class WhereaboutViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows whereabouts to be viewed or edited.
    """
    queryset = models.Whereabout.objects.all()
    serializer_class = serializers.WhereaboutSerializer
    filter_class = filters.WhereaboutFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class PerformanceViewSet(GenericHierarchicalReadOnlyViewSet):
    """
    API endpoint that allows performances to be viewed or edited.
    """
    queryset = models.Performance.objects.all()
    serializer_class = serializers.PerformanceSerializer
    serializer_classes = {
        models.StandbyPerformance: serializers.StandbyPerformanceSerializer,
        models.ActivityPerformance: serializers.ActivityPerformanceSerializer,
    }
    filter_class = filters.PerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class ActivityPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows activity performances to be viewed or edited.
    """
    queryset = models.ActivityPerformance.objects.all()
    serializer_class = serializers.ActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class StandbyPerformanceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows standby performances to be viewed or edited.
    """
    queryset = models.StandbyPerformance.objects.all()
    serializer_class = serializers.StandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.DjangoModelPermissions,)


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows attachments to be viewed or edited.
    """
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)
    parser_classes = (parsers.MultiPartParser, parsers.FileUploadParser, parsers.JSONParser)


class PerformanceImportServiceAPIView(APIView):
    """
    Gets performances from external sources and returns them to be imported.
    """
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
    """
    Get all active users where each property of the user is the day of a 'special' event.
    Special events are: working from home, sickness leave, normal leave, nonWorkingDay based on workschedule.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Defines the entrypoint of the retrieval."""
        from_date = parser.parse(request.query_params.get('from', None)).date()
        until_date = parser.parse(request.query_params.get('until', None)).date()

        users = auth_models.User.objects.filter(is_active=True)
        sickness_type_ids = list(models.LeaveType.objects.filter(name__icontains='sick').values_list('id', flat=True))

        # Initialize data
        data = {
            'from': from_date,
            'until': until_date,
            'no_work': {},
            'holiday': {},
            'home_work': {},
            'sickness': {},
            'leave': {}
        }

        # Fetch all employment contracts for this period
        employment_contracts = (models.EmploymentContract.objects
                                .filter(
                                    (Q(ended_at__isnull=True) & Q(started_at__lte=from_date)) |
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

        # Fetch all leave dates for this period
        leave_dates = (models.LeaveDate.objects
                       .filter(leave__user__in=users, leave__status=models.STATUS_APPROVED,
                               starts_at__date__gte=from_date, starts_at__date__lte=until_date)
                       .select_related('leave', 'leave__leave_type', 'leave__user'))
        # Index leave dates by day, then by user ID
        leave_date_data = {}
        for leave_date in leave_dates:
            (leave_date_data
                .setdefault(str(leave_date.starts_at.date()), {})
                .setdefault(leave_date.leave.user.id, [])
                .append(leave_date))

        # Fetch all holidays for this period
        holidays = (models.Holiday.objects
                    .filter(date__gte=from_date, date__lte=until_date))
        # Index holidays by day, then by country
        holiday_data = {}
        for holiday in holidays:
            (holiday_data
                .setdefault(str(holiday.date), {})
                .setdefault(holiday.country, [])
                .append(holiday))

        # Count days
        day_count = (until_date - from_date).days + 1

        # Iterate over users
        for user in users:
            # Initialize user data
            user_no_work = []
            user_holiday = []
            user_home_work = []
            user_sickness = []
            user_leave = []

            # Iterate over days
            for i in range(day_count):
                # Determine date for this day
                current_date = copy.deepcopy(from_date) + timedelta(days=i)

                # Get employment contract for this day
                # This allows us to determine the work schedule and country of the user
                employment_contract = None
                try:
                    for ec in employment_contract_data[user.id]:
                        if (ec.started_at <= current_date) and ((not ec.ended_at) or (ec.ended_at >= current_date)):
                            employment_contract = ec
                            break
                except KeyError:
                    pass

                work_schedule = employment_contract.work_schedule if employment_contract else None
                country = employment_contract.company.country if employment_contract else None

                # No work occurs when there is no work_schedule, or no hours should be worked that day
                if (not work_schedule) or (getattr(work_schedule, current_date.strftime('%A').lower(), 0.00) <= 0):
                    user_no_work.append(current_date)

                # Holidays
                try:
                    if country and holiday_data[str(current_date)][country]:
                        user_holiday.append(current_date)
                except KeyError:
                    pass

                # Leave & Sickness
                try:
                    for leave_date in leave_date_data[str(current_date)][user.id]:
                        if leave_date.leave.leave_type.id in sickness_type_ids:
                            user_sickness.append(current_date)
                        else:
                            user_leave.append(current_date)
                except KeyError:
                    pass

                # Home work
                # @TODO Implement home working

            # Store user data
            data['no_work'][user.id] = user_no_work
            data['holiday'][user.id] = user_holiday
            data['home_work'][user.id] = user_home_work
            data['sickness'][user.id] = user_sickness
            data['leave'][user.id] = user_leave

        return Response(data, status=status.HTTP_200_OK)


class RangeInfoServiceAPIView(APIView):
    """Calculates and returns information for a given date range."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Get date range information."""
        user = request.user
        user_info = user.userinfo

        from_date = parser.parse(request.query_params.get('from', None)).date()
        until_date = parser.parse(request.query_params.get('until', None)).date()
        daily = request.query_params.get('daily', 'false') == 'true'
        detailed = request.query_params.get('detailed', 'false') == 'true'
        summary = request.query_params.get('summary', 'false') == 'true'

        work_hours = 0
        holiday_hours = 0
        leave_hours = 0
        performed_hours = 0
        remaining_hours = 0
        total_hours = 0

        daily_data = {}
        # Determine amount of days we are going to process leaves for, so we can
        # iterate over the dates
        day_count = (until_date - from_date).days + 1

        work_schedule = None
        employment_contract = None

        performances = []

        # Fetch holidays
        holidays = []
        if user_info and user_info.country:
            holidays = list(models.Holiday.objects.filter(country=user_info.country, date__gte=from_date,
                                                          date__lte=until_date))

        # Fetch all approved leave dates
        leave_dates = list(models.LeaveDate.objects
                           .filter(leave__user=user, leave__status=models.STATUS_APPROVED,
                                   starts_at__date__gte=from_date,
                                   starts_at__date__lte=until_date)
                           .select_related('leave', 'leave__leave_type', 'leave__user')
                           .prefetch_related('leave__attachments', 'leave__leavedate_set'))

        for i in range(day_count):
            day_work_hours = 0
            day_holiday_hours = 0
            day_leave_hours = 0
            day_remaining_hours = 0
            day_performed_hours = 0
            day_total_hours = 0

            day_holidays = []
            day_leaves = []
            day_performances = []

            # Determine date for this day
            current_date = copy.deepcopy(from_date) + timedelta(days=i)

            # For the given date, determine the active work schedule
            if ((not employment_contract) or (employment_contract.started_at > current_date) or
                    (employment_contract.ended_at and (employment_contract.ended_at < current_date))):
                employment_contract = models.EmploymentContract.objects.filter(
                    Q(user=user, started_at__lte=current_date) &
                    (Q(ended_at__isnull=True) | Q(ended_at__gte=current_date))
                ).select_related('work_schedule').first()
                work_schedule = employment_contract.work_schedule if employment_contract else None

            # Determine work hours
            if work_schedule:
                duration = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal(0.00))
                work_hours += duration
                day_work_hours += duration

            # Determine holidays
            for holiday in holidays:
                if holiday.date == current_date:
                    duration = getattr(work_schedule, holiday.date.strftime('%A').lower(), Decimal(0.00))
                    holiday_hours += duration
                    day_holiday_hours += duration
                    day_holidays.append(holiday)
                    break

            # Determine leave hours
            for leave_date in leave_dates:
                if leave_date.starts_at.date() == current_date:
                    duration = Decimal(round((leave_date.ends_at - leave_date.starts_at).total_seconds() / 3600, 2))
                    leave_hours += duration
                    day_leave_hours += duration
                    day_leaves.append(leave_date.leave)

            # Determine performed hours
            day_performances = list(models.ActivityPerformance.objects
                                    .filter(timesheet__user=user, timesheet__month=current_date.month,
                                            timesheet__year=current_date.year, day=current_date.day)
                                    .select_related('performance_type', 'contract_role', 'contract',
                                                    'contract__customer', 'timesheet', 'timesheet__user'))

            for performance in day_performances:
                duration = Decimal(performance.duration)
                performed_hours += duration
                day_performed_hours += duration
                performances.append(performance)

            day_total_hours = (day_holiday_hours + day_leave_hours + day_performed_hours)
            day_remaining_hours = day_work_hours - day_total_hours
            day_remaining_hours = max(0, day_remaining_hours)

            if daily:
                day_detail = {
                    'work_hours': day_work_hours,
                    'holiday_hours': day_holiday_hours,
                    'leave_hours': day_leave_hours,
                    'remaining_hours': day_remaining_hours,
                    'performed_hours': day_performed_hours,
                    'total_hours': day_total_hours,
                }

                if detailed:
                    day_detail['holidays'] = serializers.HolidaySerializer(day_holidays, many=True).data
                    day_detail['leaves'] = serializers.LeaveSerializer(day_leaves, many=True).data
                    day_detail['performances'] = serializers.ActivityPerformanceSerializer(day_performances,
                                                                                           many=True).data

                # Insert day detail into daily data
                daily_data[str(current_date)] = day_detail

        total_hours = holiday_hours + leave_hours + performed_hours
        remaining_hours = work_hours - total_hours
        remaining_hours = max(0, remaining_hours)

        data = {
            'work_hours': work_hours,
            'holiday_hours': holiday_hours,
            'leave_hours': leave_hours,
            'remaining_hours': remaining_hours,
            'performed_hours': performed_hours,
            'total_hours': total_hours,
            'from': from_date,
            'until': until_date,
        }

        if daily:
            data['details'] = daily_data

        if summary:
            summary_performances = {}

            for performance in performances:
                if performance.contract.id not in summary_performances:
                    summary_performances[performance.contract.id] = {
                        'contract': serializers.MinimalContractSerializer(performance.contract).data,
                        'duration': 0,
                    }

                summary_performances[performance.contract.id]['duration'] += performance.duration

            data['summary'] = {
                'performances': summary_performances.values()
            }

        return Response(data)


class MyUserServiceAPIView(APIView):
    """
    Get the currently authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        entity = request.user
        data = serializers.MyUserSerializer(entity, context={'request': request}).data

        return Response(data)


class LeaveRequestServiceAPIView(APIView):
    """
    Request leave for the given date range.
    """

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


class MyTimesheetContractPdfExportServiceAPIView(PDFTemplateView, generics.GenericAPIView):

    """View for exporting a timesheet contract to PDF."""

    filename = 'timesheet_contract.pdf'
    template_name = 'ninetofiver/timesheets/timesheet_contract_pdf_export.pug'
    permission_classes = (permissions.IsAuthenticated,)

    def render_to_response(self, context, **response_kwargs):
        user = context['view'].request.user
        timesheet = get_object_or_404(models.Timesheet, pk=context.get('timesheet_pk', None), user=user)
        contract = get_object_or_404(models.Contract, pk=context.get('contract_pk', None), contractuser__user=user)

        context['user'] = user
        context['timesheet'] = timesheet
        context['contract'] = contract
        context['performances'] = (models.ActivityPerformance.objects
                                   .filter(timesheet=timesheet, contract=contract)
                                   .order_by('day')
                                   .all())
        context['total_performed_hours'] = sum([x.duration for x in context['performances']])
        context['total_performed_days'] = round(context['total_performed_hours'] / 8, 2)

        return super().render_to_response(context, **response_kwargs)


class MyLeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leaves for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyLeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.leave_set.all()


class MyLeaveDateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave dates for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyLeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.LeaveDate.objects.filter(leave__user=user)


class MyTimesheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows timesheets for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyTimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.timesheet_set


class MyContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contracts for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyContractSerializer
    filter_class = filters.ContractFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.Contract.objects.filter(contractuser__user=user).distinct()


class MyContractUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract users for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyContractUserSerializer
    filter_class = filters.ContractUserFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.ContractUser.objects.filter(user=user).distinct()


class MyPerformanceViewSet(GenericHierarchicalReadOnlyViewSet):
    """
    API endpoint that allows performances for the currently authenticated user to be viewed or edited.
    """
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
    """
    API endpoint that allows activity performances for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.ActivityPerformance.objects.filter(timesheet__user=user)


class MyStandbyPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows standby performances for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyStandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.StandbyPerformance.objects.filter(timesheet__user=user)


class MyAttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows attachments for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyAttachmentSerializer
    filter_class = filters.AttachmentFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.attachment_set.all()


class MyWorkScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows workschedules for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyWorkScheduleSerializer
    filter_class = filters.WorkScheduleFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.WorkSchedule.objects.filter(employmentcontract__user=user)


class LeaveFeedServiceAPIView(APIView):
    """
    Get leaves as an ICS feed.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        return feeds.LeaveFeed().__call__(request)
