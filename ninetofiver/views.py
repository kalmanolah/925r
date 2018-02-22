from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from calendar import monthcalendar, monthrange, day_name
from collections import Counter
from django.utils import timezone
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from ninetofiver import filters
from ninetofiver import models
from ninetofiver import serializers
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
from rest_framework.schemas import SchemaGenerator
from rest_framework_swagger import renderers
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer
from ninetofiver.redmine.views import get_redmine_user_time_entries
from ninetofiver.redmine.serializers import RedmineTimeEntrySerializer
from ninetofiver.utils import days_in_month
from django.db.models import Q
from django.db import DatabaseError
from django.core.mail import send_mail
from datetime import datetime, date, timedelta
from wkhtmltopdf.views import PDFTemplateView
import ninetofiver.settings as settings

import logging
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
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ProjectContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows project contracts to be viewed or edited.
    """
    queryset = models.ProjectContract.objects.all()
    filter_class = filters.ProjectContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)

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
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)

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
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)

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
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ActivityPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows activity performances to be viewed or edited.
    """
    queryset = models.ActivityPerformance.objects.all()
    serializer_class = serializers.ActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class StandbyPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows standby performances to be viewed or edited.
    """
    queryset = models.StandbyPerformance.objects.all()
    serializer_class = serializers.StandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows attachments to be viewed or edited.
    """
    queryset = models.Attachment.objects.all()
    serializer_class = serializers.AttachmentSerializer
    filter_class = filters.AttachmentFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)
    parser_classes = (parsers.MultiPartParser, parsers.FileUploadParser, parsers.JSONParser)


class TimeEntryImportServiceAPIView(APIView):
    """
    Gets time entries from external sources and returns them to be imported as performances.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        try:
            redmine_id = models.UserInfo.objects.get(user_id=request.user.id).redmine_id
            if redmine_id:
                try:
                    redmine_time_entries = get_redmine_user_time_entries(
                        user_id=redmine_id,
                        params=request.query_params
                    )
                except Exception as e:
                    return Response('Something went wrong: ' + str(e), status = status.HTTP_400_BAD_REQUEST)

                serializer = RedmineTimeEntrySerializer(
                    instance=redmine_time_entries,
                    many=True
                )
                if serializer.data:
                    # serializer.is_valid(raise_exception=True)
                    return Response(serializer.data, status = status.HTTP_200_OK)

                return Response(serializer.data, status = status.HTTP_200_OK)
            else:
                return Response('Redmine_id for the current user has not been found.', status = status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response('Something went wrong: ' + str(e), status = status.HTTP_400_BAD_REQUEST)


class MonthlyAvailabilityServiceAPIView(APIView):
    """
    Get all active users where each property of the user is the day of a 'special' event.
    Special events are: working from home, sickness leave, normal leave, nonWorkingDay based on workschedule.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Defines the entrypoint of the retrieval."""
        users = auth_models.User.objects.filter(is_active=True)
        year = int(request.query_params.get('year', None))
        month = int(request.query_params.get('month', None))

        period = timezone.make_aware(datetime(year, month, 1), timezone.get_current_timezone())
        sickness_type_ids = models.LeaveType.objects.filter(name__icontains='sick').values_list('id', flat=True)

        data = {
            'year': period.year,
            'month': period.month,
            'no_work': {},
            'holiday': {},
            'home_work': {},
            'sickness': {},
            'leave': {}
        }

        for user in users:
            data['no_work'][user.id] = []
            data['holiday'][user.id] = []
            data['home_work'][user.id] = []
            data['sickness'][user.id] = []
            data['leave'][user.id] = []

            try:
                timesheet = models.Timesheet.objects.get(user=user, year=period.year, month=period.month)
            except models.Timesheet.DoesNotExist:
                timesheet = None

            if timesheet:
                # Determine leave & sickness
                leaves = (models.Leave.objects
                          .filter(user=user, status=models.STATUS_APPROVED, leavedate__timesheet=timesheet)
                          .distinct())

                for leave in leaves:
                    for leave_date in leave.leavedate_set.all():
                        if leave.leave_type.id in sickness_type_ids:
                            data['sickness'][user.id].append(leave_date.starts_at.day)
                        else:
                            data['leave'][user.id].append(leave_date.starts_at.day)

                # Determine home work
                whereabouts = models.Whereabout.objects.filter(timesheet=timesheet, location__icontains='home')

                for whereabout in whereabouts:
                    data['home_work'][user.id].append(whereabout.day)

            # Iterate over days, attempting to determine employment contract for each day
            employment_contract = None
            for i in range(days_in_month(period.year, period.month)):
                day = date(period.year, period.month, i + 1)

                if ((not employment_contract) or
                        (employment_contract.ended_at and (employment_contract.ended_at < day))):
                    try:
                        employment_contract = models.EmploymentContract.objects.filter(
                            Q(ended_at__isnull=True) | Q(ended_at__gte=day), user=user, started_at__lte=day).first()
                    except models.EmploymentContract.DoesNotExist:
                        employment_contract = None

                if employment_contract:
                    # Determine holiday
                    holiday_cnt = (models.Holiday.objects
                                   .filter(country=employment_contract.company.country, date=day)
                                   .count())
                    if holiday_cnt:
                        data['holiday'][user.id].append(day.day)

                    # Determine work schedule
                    work_schedule = employment_contract.work_schedule
                    day_hours = getattr(work_schedule, day.strftime('%A').lower(), 0.00)
                    if day_hours <= 0:
                        data['no_work'][user.id].append(day.day)
                else:
                    # Determine work schedule
                    data['no_work'][user.id].append(day.day)

        return Response(data, status=status.HTTP_200_OK)


class MonthInfoServiceAPIView(APIView):
    """
    Calculates and returns information for a given month.

    Returns: hours_required of a given month and user
    (as a string because decimal serialization can cause precision loss).

    """

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        """Get month information."""
        user = request.user

        if user.is_superuser and request.query_params.get('user_id'):
            user = get_object_or_404(auth_models.User.objects, pk=request.query_params.get('user_id'))

        # get month from params, defaults to the current month if month is omitted.
        month = int(request.query_params.get('month') or datetime.now().month)
        year = int(request.query_params.get('year') or datetime.now().year)

        work_hours = 0
        holiday_hours = 0
        leave_hours = 0
        remaining_hours = 0
        performed_hours = 0

        # Calculate work hours based on work schedule and employment contract
        ec = None
        work_schedule = None
        for day in range(days_in_month(year, month)):
            dt = date(year, month, day + 1)

            if (not ec) or (ec.started_at > dt) or (ec.ended_at and (ec.ended_at < dt)):
                ec = models.EmploymentContract.objects.filter(
                    Q(user=user, started_at__gte=dt) &
                    (Q(ended_at__isnull=True) | Q(ended_at__lte=dt))
                ).first()

                work_schedule = ec.work_schedule if ec else None

            if work_schedule:
                work_hours += self._get_weekday_hours(work_schedule, dt.weekday())

        # Calculate holiday hours
        user_info = models.UserInfo.objects.filter(user=user).first()
        if user_info and work_schedule:
            holidays = models.Holiday.objects.filter(country=user_info.country, date__month=month, date__year=year)

            for holiday in holidays:
                holiday_hours += self._get_weekday_hours(work_schedule, holiday.date.weekday())

        # Get all approved leaves of the user with a leavedate in the given month.
        leaves = models.Leave.objects.filter(user=user, status=models.STATUS_APPROVED,
                                             leavedate__starts_at__month=month, leavedate__starts_at__year=year)

        # Calculate leave hours
        for leave in leaves:
            for leave_date in leave.leavedate_set.all():
                if (leave_date.starts_at.month == month) and (leave_date.starts_at.year == year):
                    leave_hours += Decimal(round((leave_date.ends_at - leave_date.starts_at).total_seconds() / 3600, 2))

        # Calculate performed hours
        performances = models.ActivityPerformance.objects.filter(timesheet__user=user, timesheet__month=month,
                                                                 timesheet__year=year)
        for performance in performances:
            performed_hours += Decimal(performance.duration)

        remaining_hours = work_hours - holiday_hours - leave_hours - performed_hours
        remaining_hours = 0 if remaining_hours < 0 else remaining_hours

        data = {
            'work_hours': work_hours,
            'holiday_hours': holiday_hours,
            'leave_hours': leave_hours,
            'remaining_hours': remaining_hours,
            'performed_hours': performed_hours,
            'year': year,
            'month': month,
        }

        return Response(data)

    def _get_weekday_hours(self, work_schedule, weekday):
        """Get the amount of required working hours for the given weekday for the given workschedule."""
        work_schedule_list = [
            work_schedule.monday,
            work_schedule.tuesday,
            work_schedule.wednesday,
            work_schedule.thursday,
            work_schedule.friday,
            work_schedule.saturday,
            work_schedule.sunday,
        ]

        return work_schedule_list[weekday]


class MyUserServiceAPIView(APIView):
    """
    Get the currently authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        entity = request.user
        data = serializers.MyUserSerializer(entity, context={'request': request}).data
        return Response(data)


class MyLeaveRequestService(generics.GenericAPIView):
    """
    Baseclass to create all leavedates for a given range.
    """
    serializer_class = serializers.LeaveRequestCreateSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def calculate_end(self, user, start, end):
        """
        Calculcate the end_date's time, based off of the workschedule's hours & minutes for that day.
        """

        # Get current workschedule, based off of the active employmentcontract
        ec = models.EmploymentContract.objects.get(
            Q(user=user),
            Q(ended_at__isnull=True)
            | Q(ended_at__gte=datetime.now())
        )
        ws = models.WorkSchedule.objects.get(employmentcontract=ec).__dict__

        # Get the hours of required work, count from midnight to those hours
        working_day = ws[start.strftime('%A').lower()]
        working_hours = int(working_day)
        working_minutes = (working_day - working_hours) * 60

        return end.replace(
            year=(start.year),
            month=(start.month),
            day=(start.day),
            hour=working_hours,
            minute=working_minutes,
            second=(1)
        )

    def create_leavedates(self, this, request, leave):
        """
        Used to handle logic and return the correct response.
        """
        user = request.user
        data = request.data

        try:
            # Make the datetimes aware of the timezone
            start = timezone.make_aware(
                (datetime.strptime(data['starts_at'], "%Y-%m-%dT%H:%M:%S")),
                timezone.get_current_timezone()
            )
            end = timezone.make_aware(
                (datetime.strptime(data['ends_at'], "%Y-%m-%dT%H:%M:%S")),
                timezone.get_current_timezone()
            )

            full_day = False
            if type(data['full_day']) is not str:
                full_day = data['full_day']
            elif data['full_day'] == 'true':
                full_day = True

            # If the leave isn't flagged as full_day
            if start.date() == end.date() and not full_day:
                timesheet, created = models.Timesheet.objects.get_or_create(
                    user=user,
                    year=start.year,
                    month=start.month
                )

                # Create leavedate
                ld = models.LeaveDate(
                    leave=leave,
                    timesheet=timesheet,
                    starts_at=start,
                    ends_at=end
                )

                # Validate & save
                ld.full_clean()
                ld.save()

                leave.status = models.STATUS_PENDING
                leave.save()

                return_dict = {
                    'leave': leave.id,
                    'description': leave.description,
                    'leave_type': leave.leave_type.id,
                    'full_day': data['full_day'],
                    'starts_at': start,
                    'ends_at': end
                }
                return Response(return_dict, status=status.HTTP_201_CREATED)

            # If the leave is flagged as full_day
            elif full_day and start.date() != end.date():
                try:
                    new_start = start.replace(
                        year=start.year,
                        month=start.month,
                        day=start.day,
                        hour=0,
                        minute=0,
                        second=0
                    )
                    new_end = self.calculate_end(user, new_start, end)
                    days = (end - start).days + 1

                except Exception as e:
                    leave.delete()
                    return Response('Workschedule couldn\'t be found for that user.', status = status.HTTP_404_NOT_FOUND)

                if days < 0:
                    leave.delete()
                    return Response('End date should come after start date.', status = status.HTTP_400_BAD_REQUEST)

                # Get timesheet, or create it
                timesheet = models.Timesheet.objects.get_or_create(
                    user=user,
                    year=new_start.year,
                    month=new_start.month
                )[0]

                my_list = list()

                # Create all leavedates ranging from the start to the end
                for x in range(0, days):

                    # If not correct timesheet, get /create it and overwrite
                    if not (timesheet.year == new_start.year and timesheet.month == new_start.month):
                        timesheet = models.Timesheet.objects.get_or_create(
                            user=user,
                            year=new_start.year,
                            month=new_start.month
                        )[0]

                    temp = models.LeaveDate(
                        leave=leave,
                        timesheet=timesheet,
                        starts_at=new_start,
                        ends_at=new_end
                    )

                    # Call validation on the object
                    try:
                        temp.full_clean()
                    except ValidationError as e:
                        leave.delete()
                        return Response(e, status = status.HTTP_400_BAD_REQUEST)

                    # Save the object
                    temp.save()

                    # Convert object into a list because serializer needs a list
                    my_list.append({
                        'id': temp.id,
                        'created_at': temp.created_at,
                        'updated_at': temp.updated_at,
                        'leave': temp.leave_id,
                        'timesheet': temp.timesheet_id,
                        'starts_at': temp.starts_at,
                        'ends_at': temp.ends_at
                    })

                    # Set time to original end when second to last has run
                    if x <= days - 2:
                        try:
                            new_start += timedelta(days=1)
                            new_end = self.calculate_end(user, new_start, new_end + timedelta(days=1))
                        except Exception as e:
                            leave.delete()
                            return Response('Workschedule couldn\'t be found for that user', status = status.HTTP_400_BAD_REQUEST)

                leave.status = models.STATUS_PENDING
                leave.save()

                return_dict = {
                    'leave': leave.id,
                    'description': leave.description,
                    'leave_type': leave.leave_type.id,
                    'full_day': data['full_day'],
                    'starts_at': start,
                    'ends_at': end
                }
                return Response(return_dict, status = status.HTTP_201_CREATED)

            else:
                leave.delete()
                return Response('The request can not be marked as full_day and only span a single day.', status = status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            leave.delete()
            return Response(str(e), status = status.HTTP_404_NOT_FOUND)


class MyLeaveRequestServiceAPIView(generics.CreateAPIView, MyLeaveRequestService):
    """
    Creates a leave and all its leavedates for a given range.
    """
    serializer_class = serializers.LeaveRequestCreateSerializer

    def create_leave(self, request):
        """Creates the leave object for the leavedates."""
        lt = models.LeaveType.objects.get(pk=request.data['leave_type'])

        if lt is None:
            raise ObjectDoesNotExist('Leavetype could not be found based on the provided pk.')

        return models.Leave.objects.create(
            user = request.user,
            description = request.data['description'],
            leave_type = lt,
            status = models.STATUS_DRAFT,
        )

    def post(self, request, format=None):
        """Defines the behaviour for a post request."""
        leave = self.create_leave(request)
        return self.create_leavedates(self, request, leave)


class MyLeaveRequestUpdateServiceAPIView(generics.UpdateAPIView, MyLeaveRequestService):
    """
    Updates a leave's leavedates for a given range.
    """
    serializer_class = serializers.LeaveRequestUpdateSerializer

    def get_leave(self, request):
        """Creates the leave object for the leavedates."""
        lv = models.Leave.objects.filter(pk=request.data['leave_id'])

        if len(lv) is 0:
            raise ObjectDoesNotExist('Leave object could not be found based on the provided pk.')

        return lv[0]

    def update(self, request):
        """Defines the behaviour for an update request."""
        lv = self.get_leave(request)
        models.LeaveDate.objects.filter(leave=lv).delete()
        return self.create_leavedates(self, request, lv)

    def patch(self, request, format=None):
        """Defines the behaviour for a patch request."""
        return self.update(request)

    def put(self, request, format=None):
        """Defines the behaviour for a put request."""
        return self.update(request)


class MyTimesheetContractPdfExportServiceAPIView(PDFTemplateView, generics.GenericAPIView):

    """View for exporting a timesheet contract to PDF."""

    filename = 'timesheet_contract.pdf'
    template_name = 'ninetofiver/timesheets/timesheet_contract_pdf_export.pug'

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
        return user.timesheet_set.exclude(status = models.STATUS_CLOSED)


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
