from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from decimal import Decimal
from datetime import datetime, timedelta, time
from calendar import monthcalendar, weekday, monthrange, day_name
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
from django.db.models import Q

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
    serializer_class = serializers.ProjectContractSerializer
    filter_class = filters.ProjectContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ConsultancyContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows consultancy contracts to be viewed or edited.
    """
    queryset = models.ConsultancyContract.objects.all()
    serializer_class = serializers.ConsultancyContractSerializer
    filter_class = filters.ConsultancyContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class SupportContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows support contracts to be viewed or edited.
    """
    queryset = models.SupportContract.objects.all()
    serializer_class = serializers.SupportContractSerializer
    filter_class = filters.SupportContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract roles to be viewed or edited.
    """
    queryset = models.ContractRole.objects.all()
    serializer_class = serializers.ContractRoleSerializer
    filter_class = filters.ContractRoleFilter
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
    queryset = models.Timesheet.objects.all()
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
        # If Redmine credentials are provided
        if settings.REDMINE_URL and settings.REDMINE_API_KEY:
            redmine_id = models.UserInfo.objects.get(user_id=request.user.id).redmine_id
            if redmine_id:
                redmine_time_entries = get_redmine_user_time_entries(user_id=redmine_id, params=request.query_params)
                data = RedmineTimeEntrySerializer(
                    instance=redmine_time_entries, many=True).data
        return Response(data)


class MonthInfoServiceAPIView(APIView):
    """
    Calculates and returns information from a given month.
    Returns: hours_required of a given month and user
    (as a string because decimal serialization can cause precision loss).
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        # get user from params, defaults to the current user if user is omitted.
        user = request.query_params.get('user_id') or request.user
        # get month from params, defaults to the current month if month is omitted.
        month = int(request.query_params.get('month') or datetime.now().month)
        data = {}
        data['hours_required'] = self.total_hours_required(user, month)
        data['hours_performed'] = self.hours_performed(user, month)
        serializer = serializers.MonthInfoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def total_hours_required(self, user, month):
        total = 0
        # Calculate total hours required.
        try:
            employmentcontract = models.EmploymentContract.objects.get(user_id=user)
        except ObjectDoesNotExist as oe:
            return Response('Failed to get employmentcontract' + str(oe), status=status.HTTP_400_BAD_REQUEST)
        work_schedule = models.WorkSchedule.objects.get(pk=employmentcontract.work_schedule.id)
    

        year = datetime.now().year
        # List that contains the amount of weekdays of the given month.
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, monthrange(year, month)[1])
        days_count = {}

        for i in range((end_date - start_date).days + 1):
            day = day_name[(start_date + timedelta(days=i)).weekday()]
            days_count[day] = days_count[day] + 1 if day in days_count else 1

        # Caluculate total hours required to work according to work schedule.
        total += work_schedule.monday * days_count['Monday']
        total += work_schedule.tuesday * days_count['Tuesday']
        total += work_schedule.wednesday * days_count['Wednesday']
        total += work_schedule.thursday * days_count['Thursday']
        total += work_schedule.friday * days_count['Friday']
        total += work_schedule.saturday * days_count['Saturday']
        total += work_schedule.sunday * days_count['Sunday']
        # logger.debug('total: ' + str(total))
        
        # Subtract holdays from total.
        try:
            user_country = models.UserInfo.objects.get(user_id=user).country
        except ObjectDoesNotExist as oe:
            return Response('Failed to get user country: ' + str(oe), status=status.HTTP_400_BAD_REQUEST)
        
        holidays = models.Holiday.objects.filter(country=user_country).filter(date__month=month)
        for holiday in holidays:
            total -= 8
        # logger.debug('total after holidays: ' + str(total))

        DAY_START = '09:00'
        DAY_END = '17:30'
        DAY_DURATION = 8
        RANGE_START = timezone.make_aware(datetime(year, month, 1, 0, 0, 0, 0), timezone.get_current_timezone())
        RANGE_END = timezone.make_aware(datetime(year, month, monthrange(year, month)[1], 0, 0, 0), timezone.get_current_timezone())

        # Get all approved leaves of the user.
        leaves = models.Leave.objects.filter(user_id=user, status=models.Leave.STATUS.APPROVED)
        # Filter out those who don't start or end in the current month.
        result = list(filter(lambda x: (x.leavedate_set.first().starts_at >= RANGE_START and x.leavedate_set.first().starts_at <= RANGE_END) or (x.leavedate_set.last().starts_at >= RANGE_START and x.leavedate_set.last().starts_at <= RANGE_END), leaves))
        
        # Subtract leaves from total.
        for leave in result:
            leavedates = leave.leavedate_set.all()

            first_leavedate = leavedates.first()
            last_leavedate = leavedates.last()

            for leavedate in leavedates:
                if leavedate.starts_at >= RANGE_START:
                    first_leavedate = leavedate
                    break
            for leavedate in leavedates:
                if leavedate.ends_at >= RANGE_END:
                    last_leavedate = leavedate
                    break
            # first leavedate time deltas
            fld_day_start_delta = datetime.strptime(str(first_leavedate.starts_at.time()), '%H:%M:%S') - (datetime.strptime(DAY_START, '%H:%M'))
            fld_day_end_delta = (datetime.strptime(DAY_END, '%H:%M')) - datetime.strptime(str(first_leavedate.ends_at.time()), '%H:%M:%S') 
            # subtract first leavedate time deltas from total
            hours_required = round(fld_day_start_delta.seconds/3600, 1) + round(fld_day_end_delta.seconds/3600, 1)
            hours_required = hours_required if hours_required <= 8 else 8
            total -= Decimal(hours_required)
            
            # if the leave spans more than one day: calculate last leavedate time deltas
            if len(leavedates) > 1:
                lld_day_start_delta = datetime.strptime(str(last_leavedate.starts_at.time()), '%H:%M:%S') - datetime.strptime(DAY_START, '%H:%M')
                lld_day_end_delta = datetime.strptime(DAY_END, '%H:%M') - datetime.strptime(str(last_leavedate.ends_at.time()), '%H:%M:%S') 
                # subtract last leavedate time deltas from total
                hours_required = round(lld_day_start_delta.seconds/3600, 1) + round(lld_day_end_delta.seconds/3600, 1)
                hours_required = hours_required if hours_required <= 8 else 8
                total -= Decimal(hours_required)
            
            # Check if the leave spans more days than one.
            if len(leavedates) > 1:
                for leavedate in leavedates:
                    # subtract a whole day if the leavedate is between the first leavedate and the last leavedate (of the specified month)
                    if leavedate.starts_at.weekday() < 5 and leavedate.starts_at > first_leavedate.starts_at and leavedate.starts_at  < last_leavedate.starts_at: 
                        total -= DAY_DURATION

            # logger.debug('total after leaves: ' + str(total))
        return Decimal(total)

    def hours_performed(self, user, month):
        total = 0
        try:
            performances = models.ActivityPerformance.objects.filter(timesheet__user_id=user, timesheet__month=month)
        except ObjectDoesNotExist as oe:
            return Response('Performances not found: ' + str(oe), status=status.HTTP_404_NOT_FOUND)
        for performance in performances:
            total += Decimal(performance.duration)
        return Decimal(total)


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
        """Calculcate the end_date's time, based off of the workschedule's hours & minutes for that day."""

        #Get the current workschedule, based off of the active employmentcontract
        ec = models.EmploymentContract.objects.get(
            Q(user = user),
            Q(ended_at__isnull = True)  | Q(ended_at__gte = datetime.now())
        )
        ws = models.WorkSchedule.objects.get(employmentcontract = ec).__dict__

        #Get the hours of required work, count from midnight to those hours
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
        """ Used to handle logic and return the correct response. """
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

            #If the leave isn't flagged as full_day
            if not data['full_day'] and start.date() == end.date():
                timesheet, created = models.Timesheet.objects.get_or_create(
                    user=user,
                    year=start.year,
                    month=start.month
                )

                #Create leavedate
                ld = models.LeaveDate(
                    leave = leave,
                    timesheet = timesheet,
                    starts_at = start,
                    ends_at = end
                )

                #Validate & save
                ld.full_clean()
                ld.save()

                leave.status = 'PENDING'
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

            #If the leave is flagged as full_day
            elif data['full_day'] and start.date() != end.date():
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

                    #Set time to original end when second to last has run
                    if x <= days - 2:
                        try:
                            new_start += timedelta(days=1)
                            new_end = self.calculate_end(user, new_start, new_end + timedelta(days=1))
                        except Exception as e:
                            leave.delete()
                            return Response('Workschedule couldn\'t be found for that user', status = status.HTTP_400_BAD_REQUEST)

                leave.status = 'PENDING'
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
                return Response('The request can not be marked as full_day and only span a single day.', status = status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            leave.delete()
            return Response(e, status = status.HTTP_404_NOT_FOUND)


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
            status = 'DRAFT',
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
        return user.timesheet_set.exclude(status = models.Timesheet.STATUS.CLOSED)


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
