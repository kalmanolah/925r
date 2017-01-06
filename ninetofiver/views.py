from django.shortcuts import render, get_object_or_404
from django.contrib.auth import models as auth_models
from django.contrib.auth.decorators import login_required
from rest_framework import viewsets, permissions, response, schemas
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import CoreJSONRenderer
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework_swagger.renderers import OpenAPIRenderer, SwaggerUIRenderer
from ninetofiver import models, serializers, filters
from ninetofiver.viewsets import GenericHierarchicalReadOnlyViewSet


def home_view(request):
    """Homepage."""
    context = {}
    return render(request, 'ninetofiver/home/index.jade', context)


@login_required
def account_view(request):
    """User-specific account page."""
    context = {}
    return render(request, 'ninetofiver/account/index.jade', context)


@api_view(exclude_from_schema=True)
@renderer_classes([OpenAPIRenderer, SwaggerUIRenderer, CoreJSONRenderer])
@permission_classes((permissions.IsAuthenticated,))
def schema_view(request):
    """API documentation."""
    generator = schemas.SchemaGenerator(title='ninetofiver API')
    return response.Response(generator.get_schema(request=request))


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = auth_models.User.objects.distinct().order_by('-date_joined')
    serializer_class = serializers.UserSerializer
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class GroupViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = auth_models.Group.objects.distinct()
    serializer_class = serializers.GroupSerializer
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class CompanyViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows companies to be viewed or edited.
    """
    queryset = models.Company.objects.distinct()
    serializer_class = serializers.CompanySerializer
    filter_class = filters.CompanyFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class EmploymentContractTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employment contract types to be viewed or edited.
    """
    queryset = models.EmploymentContractType.objects.distinct()
    serializer_class = serializers.EmploymentContractTypeSerializer
    filter_class = filters.EmploymentContractTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class EmploymentContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employment contracts to be viewed or edited.
    """
    queryset = models.EmploymentContract.objects.distinct()
    serializer_class = serializers.EmploymentContractSerializer
    filter_class = filters.EmploymentContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class WorkScheduleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows employment contracts to be viewed or edited.
    """
    queryset = models.WorkSchedule.objects.distinct()
    serializer_class = serializers.WorkScheduleSerializer
    filter_class = filters.WorkScheduleFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class UserRelativeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows user relatives to be viewed or edited.
    """
    queryset = models.UserRelative.objects.distinct()
    serializer_class = serializers.UserRelativeSerializer
    filter_class = filters.UserRelativeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class HolidayViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows holidays to be viewed or edited.
    """
    queryset = models.Holiday.objects.distinct()
    serializer_class = serializers.HolidaySerializer
    filter_class = filters.HolidayFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave types to be viewed or edited.
    """
    queryset = models.LeaveType.objects.distinct()
    serializer_class = serializers.LeaveTypeSerializer
    filter_class = filters.LeaveTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leaves to be viewed or edited.
    """
    queryset = models.Leave.objects.distinct()
    serializer_class = serializers.LeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class LeaveDateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave dates to be viewed or edited.
    """
    queryset = models.LeaveDate.objects.distinct()
    serializer_class = serializers.LeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class PerformanceTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows performance types to be viewed or edited.
    """
    queryset = models.PerformanceType.objects.distinct()
    serializer_class = serializers.PerformanceTypeSerializer
    filter_class = filters.PerformanceTypeFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractViewSet(GenericHierarchicalReadOnlyViewSet):
    """
    API endpoint that allows contracts to be viewed or edited.
    """
    queryset = models.Contract.objects.distinct()
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
    queryset = models.ProjectContract.objects.distinct()
    serializer_class = serializers.ProjectContractSerializer
    filter_class = filters.ProjectContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ConsultancyContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows consultancy contracts to be viewed or edited.
    """
    queryset = models.ConsultancyContract.objects.distinct()
    serializer_class = serializers.ConsultancyContractSerializer
    filter_class = filters.ConsultancyContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class SupportContractViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows support contracts to be viewed or edited.
    """
    queryset = models.SupportContract.objects.distinct()
    serializer_class = serializers.SupportContractSerializer
    filter_class = filters.SupportContractFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractRoleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract roles to be viewed or edited.
    """
    queryset = models.ContractRole.objects.distinct()
    serializer_class = serializers.ContractRoleSerializer
    filter_class = filters.ContractRoleFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class ContractUserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows contract users to be viewed or edited.
    """
    queryset = models.ContractUser.objects.distinct()
    serializer_class = serializers.ContractUserSerializer
    filter_class = filters.ContractUserFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class TimesheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows timesheets to be viewed or edited.
    """
    queryset = models.Timesheet.objects.distinct()
    serializer_class = serializers.TimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class PerformanceViewSet(GenericHierarchicalReadOnlyViewSet):
    """
    API endpoint that allows performances to be viewed or edited.
    """
    queryset = models.Performance.objects.distinct()
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
    queryset = models.ActivityPerformance.objects.distinct()
    serializer_class = serializers.ActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class StandbyPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows standby performances to be viewed or edited.
    """
    queryset = models.StandbyPerformance.objects.distinct()
    serializer_class = serializers.StandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.IsAuthenticated, permissions.DjangoModelPermissions)


class MyUserServiceAPIView(APIView):
    """
    Get the currently authenticated user.

    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, format=None):
        entity = request.user
        data = serializers.MyUserSerializer(entity, context={'request': request}).data
        return Response(data)


class MyLeaveViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leaves for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyLeaveSerializer
    filter_class = filters.LeaveFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.leave_set.distinct()


class MyLeaveDateViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows leave dates for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyLeaveDateSerializer
    filter_class = filters.LeaveDateFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.LeaveDate.objects.filter(leave__user=user).distinct()


class MyTimesheetViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows timesheets for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyTimesheetSerializer
    filter_class = filters.TimesheetFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return user.timesheet_set.exclude(closed=True).distinct()


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
        return models.Performance.objects.filter(timesheet__user=user).distinct()


class MyActivityPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows activity performances for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyActivityPerformanceSerializer
    filter_class = filters.ActivityPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.ActivityPerformance.objects.filter(timesheet__user=user).distinct()


class MyStandbyPerformanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows standby performances for the currently authenticated user to be viewed or edited.
    """
    serializer_class = serializers.MyStandbyPerformanceSerializer
    filter_class = filters.StandbyPerformanceFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.StandbyPerformance.objects.filter(timesheet__user=user).distinct()
