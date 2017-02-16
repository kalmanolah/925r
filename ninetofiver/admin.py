from django.contrib import admin
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


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'vat_identification_number', 'address', 'country', 'internal')
    ordering = ('-internal', 'name')


@admin.register(models.WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    ordering = ('label',)


@admin.register(models.EmploymentContractType)
class EmploymentContractTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label')
    search_fields = ('label',)
    ordering = ('label',)


@admin.register(models.EmploymentContract)
class EmploymentContractAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'company', 'employment_contract_type', 'started_at', 'ended_at')
    list_filter = (('user', RelatedDropdownFilter), ('company', RelatedDropdownFilter),
                   ('employment_contract_type', RelatedDropdownFilter), ('started_at', DateRangeFilter),
                   ('ended_at', DateRangeFilter))
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employment_contract_type__label',
                     'started_at', 'ended_at')
    ordering = ('user__first_name', 'user__last_name')


@admin.register(models.UserRelative)
class UserRelativeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'user', 'relation', 'gender', 'birth_date', 'country')
    ordering = ('name',)


@admin.register(models.UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'gender', 'birth_date', 'country')
    ordering = ('user',)


@admin.register(models.UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label')
    ordering = ('label',)


@admin.register(models.UserGrouping)
class UserGroupingAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'group', 'user')
    list_filter = (
        ('group', RelatedDropdownFilter),
        ('user', RelatedDropdownFilter)
    )
    search_fields = (
        'user__username',
        'group__label'
    )
    ordering = ('group',)


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    def link(self, obj):
        return format_html('<a href="%s">%s</a>' % (obj.get_file_url(), str(obj)))

    list_display = ('__str__', 'user', 'label', 'description', 'file', 'slug', 'link')
    list_filter = (
        ('user', RelatedDropdownFilter),
    )


@admin.register(models.Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'date', 'country')
    list_filter = (
        ('country', DropdownFilter),
    )
    ordering = ('-date',)


@admin.register(models.LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label')
    ordering = ('label',)


class LeaveDateInline(admin.TabularInline):
    model = models.LeaveDate


@admin.register(models.Leave)
class LeaveAdmin(admin.ModelAdmin):

    def make_approved(self, request, queryset):
        queryset.update(status=models.Leave.STATUS.APPROVED)
    make_approved.short_description = _('Approve selected leaves')

    def make_rejected(self, request, queryset):
        queryset.update(status=models.Leave.STATUS.REJECTED)
    make_rejected.short_description = _('Reject selected leaves')

    def leave_dates(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.leavedate_set.all())))

    def attachment(self, obj):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

    list_display = ('__str__', 'user', 'leave_type', 'leave_dates', 'status', 'description', 'attachment')
    list_filter = ('status', ('leave_type', RelatedDropdownFilter), ('user', RelatedDropdownFilter),
                   ('leavedate__starts_at', DateTimeRangeFilter), ('leavedate__ends_at', DateTimeRangeFilter))
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'leave_type__label', 'status',
                     'leavedate__starts_at', 'leavedate__ends_at', 'description')
    inlines = [
        LeaveDateInline,
    ]
    actions = [
        'make_approved',
        'make_rejected',
    ]
    ordering = ('-leavedate__starts_at',)


@admin.register(models.LeaveDate)
class LeaveDateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'leave', 'starts_at', 'ends_at')
    search_fields = (
        'leave__user__username',
        'leave__leave_type__label',
        'leave__status'
    )
    ordering = ('-starts_at',)


@admin.register(models.PerformanceType)
class PerformanceTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'description', 'multiplier')
    ordering = ('multiplier',)


class ContractUserInline(admin.TabularInline):
    model = models.ContractUser


class ContractChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Contract
    inlines = [
        ContractUserInline,
    ]


@admin.register(models.ProjectContract)
class ProjectContractChildAdmin(ContractChildAdmin):
    base_model = models.ProjectContract


@admin.register(models.ConsultancyContract)
class ConsultancyContractChildAdmin(ContractChildAdmin):
    base_model = models.ConsultancyContract


@admin.register(models.SupportContract)
class SupportContractChildAdmin(ContractChildAdmin):
    base_model = models.SupportContract


@admin.register(models.Contract)
class ContractParentAdmin(PolymorphicParentModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    def performance_types(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.performance_types.all())))

    base_model = models.Contract
    child_models = (models.ProjectContract, models.ConsultancyContract, models.SupportContract)

    list_display = ('__str__', 'label', 'company', 'customer', 'contract_users',
                    performance_types, 'description', 'active')
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


@admin.register(models.ContractRole)
class ContractRoleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'description')
    ordering = ('label',)


@admin.register(models.ContractUser)
class ContractUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'contract', 'contract_role')
    ordering = ('user__first_name', 'user__last_name')


@admin.register(models.Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    def make_closed(self, request, queryset):
        queryset.update(closed=True)
    make_closed.short_description = _('Close selected timesheets')

    def make_opened(self, request, queryset):
        queryset.update(closed=False)
    make_opened.short_description = _('Open selected timesheets')

    list_display = ('__str__', 'user', 'month', 'year', 'closed')
    list_filter = ('closed',)
    actions = [
        'make_closed',
        'make_opened',
    ]
    ordering = ('-year', 'month', 'user__first_name', 'user__last_name')


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

    base_model = models.Performance
    child_models = (models.ActivityPerformance, models.StandbyPerformance)
    list_filter = (PolymorphicChildModelFilter,)
    list_display = ('__str__', 'timesheet', 'day', 'contract', 'performance_type', 'duration', 'description')
