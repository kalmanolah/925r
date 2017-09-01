from datetime import date
from django.contrib import admin
from django.contrib.auth import models as auth_models
from django.db.models import Q
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django_admin_listfilter_dropdown.filters import DropdownFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from ninetofiver import models
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin import PolymorphicParentModelAdmin
from rangefilter.filter import DateRangeFilter
from rangefilter.filter import DateTimeRangeFilter
from django import forms
from django.contrib.admin import widgets
from ninetofiver.forms import *
from django.core.mail import send_mail


class EmploymentContractStatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'Status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active')),
            ('ended', _('Ended')),
            ('future', _('Future')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(Q(started_at__lte=date.today()) & ( Q(ended_at__gte=date.today()) | Q(ended_at__isnull=True)) )
        elif self.value() == 'ended':
            return queryset.filter(ended_at__lte=date.today())
        elif self.value() == 'future':
            return queryset.filter(started_at__gte=date.today())

class ConsultancyContractStatusFilter(admin.SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Active')),
            ('ended', _('Ended')),
            ('future', _('Future')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(Q(starts_at__lte=date.today()) & ( Q(ends_at__gte=date.today()) | Q(ends_at__isnull=True)) & Q(active=True) )
        elif self.value() == 'ended':
            return queryset.filter(Q(ends_at__lte=date.today()) | Q(active=False))
        elif self.value() == 'future':
            return queryset.filter(starts_at__gte=date.today())


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'vat_identification_number', 'address', 'country', 'internal')
    ordering = ('-internal', 'name')


@admin.register(models.EmploymentContractType)
class EmploymentContractTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label')
    search_fields = ('label',)
    ordering = ('label',)


@admin.register(models.EmploymentContract)
class EmploymentContractAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'employment_contract_type', 'work_schedule', 'started_at', 'ended_at')
    list_filter = (
        EmploymentContractStatusFilter, 
        ('user', RelatedDropdownFilter), 
        ('company', RelatedDropdownFilter),
        ('employment_contract_type', RelatedDropdownFilter), 
        ('started_at', DateRangeFilter),
        ('ended_at', DateRangeFilter)
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employment_contract_type__label',
                     'started_at', 'ended_at')
    ordering = ('user__first_name', 'user__last_name')
    form = EmploymentContractAdminForm


@admin.register(models.WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    ordering = ('label',)
    form = WorkScheduleAdminForm


@admin.register(models.UserRelative)
class UserRelativeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'user', 'relation', 'gender', 'birth_date', )
    ordering = ('name',)
    form = UserRelativeAdminForm


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    def link(self, obj):
        return format_html('<a href="%s">%s</a>' % (obj.get_file_url(), str(obj)))

    list_display = ('__str__', 'user', 'label', 'description', 'file', 'slug', 'link')


@admin.register(models.Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'date', 'country')
    ordering = ('-date',)
    list_filter = (
        ('country', DropdownFilter),
        ('date', DateRangeFilter)
    )
    search_fields = ('name',)


@admin.register(models.LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'description')
    ordering = ('label',)


class LeaveDateInline(admin.TabularInline):
    model = models.LeaveDate


@admin.register(models.Leave)
class LeaveAdmin(admin.ModelAdmin):

    def make_approved(self, request, queryset):
        queryset.update(status=models.Leave.STATUS.APPROVED)
        for leave in queryset:
            self.send_notification_email(leave, 'approved')
    make_approved.short_description = _('Approve selected leaves')

    def make_rejected(self, request, queryset):
        queryset.update(status=models.Leave.STATUS.REJECTED)
        for leave in queryset:
            self.send_notification_email(leave, 'rejected')
    make_rejected.short_description = _('Reject selected leaves')

    def leave_dates(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.leavedate_set.all())))

    def attachment(self, obj):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

    def send_notification_email(self, leave, status):
        send_mail(
            str(leave.leave_type) + ' - ' + str(leave.description),
            'Dear %s\n\nyour %s from \n%s to %s\nhas been %s.\n\nKind regards\nAn inocent bot' % 
            (str(leave.user.first_name), str(leave.leave_type), str(leave.leavedate_set.first().starts_at.date()), str(leave.leavedate_set.last().ends_at.date()), str(status)),
            'we_approve_leaves@yahoo.com',
            [leave.user.email],
            fail_silently=False
        )

    list_display = ('__str__', 'user', 'leave_type', 'leave_dates', 'status', 'description', 'attachment')
    list_filter = (
        'status', 
        ('leave_type', RelatedDropdownFilter), 
        ('user', RelatedDropdownFilter),
        ('leavedate__starts_at', DateTimeRangeFilter), 
        ('leavedate__ends_at', DateTimeRangeFilter)
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'leave_type__label', 'status',
                     'leavedate__starts_at', 'leavedate__ends_at', 'description')
    inlines = [
        LeaveDateInline,
    ]
    actions = [
        'make_approved',
        'make_rejected',
    ]
    ordering = ('-status',)
    form = LeaveAdminForm


@admin.register(models.LeaveDate)
class LeaveDateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'leave', 'starts_at', 'ends_at')
    ordering = ('-starts_at',)


@admin.register(models.UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    def user_groups(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.user.groups.all())))

    list_display = ('__str__', 'user', 'gender', 'birth_date', user_groups, 'country')
    ordering = ('user',)
    form = UserInfoAdminForm


@admin.register(models.PerformanceType)
class PerformanceTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'description', 'multiplier')
    ordering = ('multiplier',)


class ContractUserInline(admin.TabularInline):
    model = models.ContractUser
    ordering = ("user__first_name", "user__last_name",)

@admin.register(models.ContractGroup)
class ContractGroupAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', )
    ordering = ('label', )


class ContractChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Contract
    inlines = [
        ContractUserInline,
    ]


@admin.register(models.ProjectContract)
class ProjectContractChildAdmin(ContractChildAdmin):
    base_model = models.ProjectContract
    form = ProjectContractAdminForm


#@admin.register(models.ConsultancyContract)
class ConsultancyContractChildAdmin(ContractChildAdmin):
    base_model = models.ConsultancyContract
    form = ConsultancyContractAdminForm


@admin.register(models.SupportContract)
class SupportContractChildAdmin(ContractChildAdmin):
    base_model = models.SupportContract
    form = SupportContractAdminForm


@admin.register(models.Contract)
class ContractParentAdmin(PolymorphicParentModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    def performance_types(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.performance_types.all())))

    def attachment(self, obj):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

    base_model = models.Contract
    child_models = (models.ProjectContract, models.ConsultancyContract, models.SupportContract)
    list_display = ('__str__', 'label', 'company', 'customer', 'contract_users',
                    performance_types, 'description', 'active', 'attachment')
    list_filter = (
        PolymorphicChildModelFilter, 
        ('company', RelatedDropdownFilter),
        ('customer', RelatedDropdownFilter), 
        ('contractuser', RelatedDropdownFilter),
        ('performance_types', RelatedDropdownFilter), 
        'active'
    )
    search_fields = ('label', 'description', 'company__name', 'customer__name', 'contractuser__user__first_name',
                     'contractuser__user__last_name', 'contractuser__user__username', 'performance_types__label')
    ordering = ('label', 'company', '-customer', 'contractuser__user__first_name', 'contractuser__user__last_name')


@admin.register(models.ConsultancyContract)
class ConsultancyContract(admin.ModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    list_display = ('label', 'company', 'customer', 'contract_users', 'active', 'starts_at', 'ends_at', 'duration')
    list_filter = (ConsultancyContractStatusFilter, ('company', RelatedDropdownFilter),
                   ('customer', RelatedDropdownFilter), ('contractuser__user', RelatedDropdownFilter))

    inlines = [
        ContractUserInline,
    ]

@admin.register(models.ContractRole)
class ContractRoleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'description')
    ordering = ('label',)


@admin.register(models.ContractUser)
class ContractUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'contract', 'contract_role')
    ordering = ('user__first_name', 'user__last_name')
    form = ContractUserAdminForm


@admin.register(models.ProjectEstimate)
class ProjectEstimateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'project', 'role', 'hours_estimated', )
    search_fields = ('role__label', 'project__label', 'project__customer')
    ordering = ('project', 'hours_estimated')


@admin.register(models.Timesheet)
class TimesheetAdmin(admin.ModelAdmin):

    def make_closed(self, request, queryset):
        queryset.update(status=models.Timesheet.STATUS.CLOSED)
    make_closed.short_description = _('Close selected timesheets')

    def make_active(self, request, queryset):
        queryset.update(status=models.Timesheet.STATUS.ACTIVE)
    make_active.short_description = _('Activate selected timesheets')

    def make_pending(self, request, queryset):
        queryset.update(status=models.Timesheet.STATUS.PENDING)
    make_pending.short_description = _('Set selected timesheets to pending')

    list_display = ('__str__', 'user', 'month', 'year', 'status')
    list_filter = ('status',)
    actions = [
        'make_closed',
        'make_active',
        'make_pending',
    ]
    ordering = ('-year', 'month', 'user__first_name', 'user__last_name')
    form = TimesheetAdminForm


@admin.register(models.Whereabout)
class WhereaboutAdmin(admin.ModelAdmin):
    list_display = ('__str__', )
    ordering = ('-day', )    


class PerformanceChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Performance


@admin.register(models.ActivityPerformance)
class ActivityPerformanceChildAdmin(PerformanceChildAdmin):
    base_model = models.ActivityPerformance


@admin.register(models.StandbyPerformance)
class StandbyPerformanceChildAdmin(PerformanceChildAdmin):
    base_model = models.StandbyPerformance


@admin.register(models.Performance)
class PerformanceParentAdmin(PolymorphicParentModelAdmin):
    def duration(self, obj):
        try:
            activity = getattr(obj, 'activityperformance', None)
        except:
            activity = None

        if activity:
            return activity.duration

        return None

    def contract(self, obj):
        try:
            activity = getattr(obj, 'activityperformance', None)
        except:
            activity = None

        if activity:
            return activity.contract

        return _('Standby')

    def performance_type(self, obj):
        try:
            activity = getattr(obj, 'activityperformance', None)
        except:
            activity = None

        if activity:
            return activity.performance_type

        return _('Standby')

    def description(self, obj):
        try:
            activity = getattr(obj, 'activityperformance', None)
        except:
            activity = None

        if activity:
            return activity.description

        return None

    def contract_role(self, obj):
        try:
            activity = getattr(obj, 'activityperformance', None)
        except:
            activity = None

        if activity:
            return activity.contract_role

    base_model = models.Performance
    child_models = (models.ActivityPerformance, models.StandbyPerformance)
    list_filter = (PolymorphicChildModelFilter,)
    list_display = ('__str__', 'timesheet', 'day', 'contract', 'performance_type', 'duration', 'description', 'contract_role')
