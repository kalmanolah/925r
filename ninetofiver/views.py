from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render

from datetime import datetime, timedelta
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
from rest_framework_swagger.renderers import OpenAPIRenderer
from rest_framework_swagger.renderers import SwaggerUIRenderer


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
    """"
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


class MyUserServiceAPIView(APIView):
    """
    Get the currently authenticated user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        entity = request.user
        data = serializers.MyUserSerializer(entity, context={'request': request}).data
        return Response(data)


class MyLeaveRequestServiceAPIView(generics.CreateAPIView):
    """
    Set the leavedates for the corresponding leave.
    """
    queryset = models.LeaveDate.objects.all()
    serializer_class = serializers.LeaveRequestSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def create_leavedates(self, this, request):
        """ Used to handle logic and return the correct response. """

        user = request.user
        leavedates = request.data

        # Make the datetimes aware of the timezone
        start = timezone.make_aware( 
            (datetime.strptime(leavedates['starts_at'], "%Y-%m-%dT%H:%M:%S")), 
            timezone.get_current_timezone()
        )
        end = timezone.make_aware(
            (datetime.strptime(leavedates['ends_at'], "%Y-%m-%dT%H:%M:%S")),
            timezone.get_current_timezone()
        )
        leave = int(leavedates['leave'])
        # timesheet = int(leavedates['timesheet'])    

        #If the leave spans across one day only
        if start.date() == end.date():
            timesheet, created = models.Timesheet.objects.get_or_create(
                user=user,
                year=start.year,
                month=start.month
            )

            try:
                #Create leavedate
                ld = models.LeaveDate(
                    leave = models.Leave.objects.get(pk=leave),
                    timesheet = timesheet,
                    starts_at = start,
                    ends_at = end
                )

                try:
                    #Validate & save
                    ld.full_clean()
                except ValidationError as ve:
                    return Response('LEAVEDATE -> ValidationError', status = status.HTTP_400_BAD_REQUEST)

                ld.save()

            except ObjectDoesNotExist as oe:
                return Response('LEAVE -> ObjectDoesNotExist', status = status.HTTP_400_BAD_REQUEST)

            return Response( [leavedates], status = status.HTTP_201_CREATED )

        #If leave spans across several days
        else:
            if(end.hour == 0 and end.minute == 0 and end.second == 0):
                end = end - timedelta(seconds=1)

            days = (end-start).days + 1

            if days < 0:
                return Response('END DATE SHOULD COME AFTER START DATE', status = status.HTTP_400_BAD_REQUEST)

            new_start = start
            new_end = end.replace(year=(start.year), month=(start.month), day=(start.day), hour=(23), minute=(59), second=(59))
            
            my_list = list()

            # Get timesheet, or create it
            timesheet = models.Timesheet.objects.get_or_create(
                user=user,
                year=new_start.year,
                month=new_start.month
            )[0]
            leave_object = models.Leave.objects.get(pk=leave)

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
                    leave=leave_object,
                    timesheet=timesheet,
                    starts_at=new_start,
                    ends_at=new_end
                )

                # Call validation on the object
                try:
                    temp.full_clean()
                except ValidationError as e:
                    models.Leave.objects.filter(pk=leave).delete()
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
                new_start += timedelta(days=1)
                new_end += timedelta(days=1)

                #After initial run, set start time on begin of day
                if x < 1:
                    new_start = new_start.replace(hour=(0), minute=(0), second=(0))
                #Set time to original end when second to last has run
                if x == days - 2:
                    new_end = new_end.replace(hour=(end.hour), minute=(end.minute), second=(end.second))

            serializer = this.get_serializer(data=my_list, many=True)
            #Empty call, does nothing (rip)
            serializer.is_valid(raise_exception=True)

            return Response(serializer.data, status = status.HTTP_201_CREATED)

    def patch(self, request, format=None):
        models.LeaveDate.objects.filter(leave=int(request.data['leave'])).delete()
        return self.create_leavedates(self, request)

    def post(self, request, format=None):
        #Return an error saying leavedates already exist for the leave object, or return the created objects
        if models.LeaveDate.objects.filter(leave=int(request.data['leave'])):
            return Response('Leavedates are already assigned to this leave object', status = status.HTTP_400_BAD_REQUEST)
        else:
            return self.create_leavedates(self, request)

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