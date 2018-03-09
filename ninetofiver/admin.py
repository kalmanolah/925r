from datetime import date
from django.contrib import admin
from django.contrib.auth import models as auth_models
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.db.models import Q
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django_admin_listfilter_dropdown.filters import DropdownFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin import PolymorphicParentModelAdmin
from rangefilter.filter import DateRangeFilter
from rangefilter.filter import DateTimeRangeFilter
from django import forms
from django.urls import reverse
from ninetofiver import models
import logging


log = logging.getLogger(__name__)


class GroupForm(forms.ModelForm):

    """Group form."""

    users = forms.ModelMultipleChoiceField(
        label=_('Users'),
        required=False,
        queryset=auth_models.User.objects.all(),
        widget=admin.widgets.FilteredSelectMultiple('users', is_stacked=False)
    )

    class Meta:
        model = auth_models.Group
        fields = '__all__'


class GroupAdmin(BaseGroupAdmin):

    """Group admin."""

    form = GroupForm

    def save_model(self, request, obj, form, change):
        """Save the given model."""
        super(GroupAdmin, self).save_model(request, obj, form, change)
        obj.user_set.set(form.cleaned_data['users'])

    def get_form(self, request, obj=None, **kwargs):
        """Get the form."""
        pks = [x.pk for x in obj.user_set.all()] if obj else []
        self.form.base_fields['users'].initial = pks

        return GroupForm


# Unregister previous admin to register current one
admin.site.unregister(auth_models.Group)
admin.site.register(auth_models.Group, GroupAdmin)


class EmploymentContractStatusFilter(admin.SimpleListFilter):

    """Employment contract status filter."""

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
            return queryset.filter(
                Q(started_at__lte=date.today()) &
                (Q(ended_at__gte=date.today()) | Q(ended_at__isnull=True))
            )
        elif self.value() == 'ended':
            return queryset.filter(ended_at__lte=date.today())
        elif self.value() == 'future':
            return queryset.filter(started_at__gte=date.today())


class ContractStatusFilter(admin.SimpleListFilter):

    """Contract status filter."""

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
            return queryset.filter(
                Q(starts_at__lte=date.today()) &
                (Q(ends_at__gte=date.today()) | Q(ends_at__isnull=True)) &
                Q(active=True)
            )
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
    list_display = ('__str__', 'name')
    search_fields = ('name',)
    ordering = ('name',)


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
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employment_contract_type__name',
                     'started_at', 'ended_at')
    ordering = ('user__first_name', 'user__last_name')


@admin.register(models.WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')
    ordering = ('name',)


@admin.register(models.UserRelative)
class UserRelativeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'user', 'relation', 'gender', 'birth_date', )
    ordering = ('name',)


@admin.register(models.Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    def link(self, obj):
        return format_html('<a href="%s">%s</a>' % (obj.get_file_url(), str(obj)))
    list_display = ('__str__', 'user', 'name', 'description', 'file', 'slug', 'link')


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
    """Leave type admin."""

    list_display = ('__str__', 'name', 'description')
    ordering = ('name',)


class LeaveDateInline(admin.TabularInline):
    """Leave date inline."""

    model = models.LeaveDate


@admin.register(models.Leave)
class LeaveAdmin(admin.ModelAdmin):
    """Leave admin."""

    def make_approved(self, request, queryset):
        """Approve selected leaves."""
        for leave in queryset:
            leave.status = models.STATUS_APPROVED
            leave.save(validate=False)
    make_approved.short_description = _('Approve selected leaves')

    def make_rejected(self, request, queryset):
        """Reject selected leaves."""
        for leave in queryset:
            leave.status = models.STATUS_REJECTED
            leave.save(validate=False)
    make_rejected.short_description = _('Reject selected leaves')

    def date(self, obj):
        """List leave dates."""
        return format_html('<br>'.join(str(x) for x in list(obj.leavedate_set.all())))

    def attachment(self, obj):
        """Attachment URLs."""
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

    def item_actions(self, obj):
        """Actions."""
        actions = []

        if obj.status == models.STATUS_PENDING:
            actions.append('<a class="button" href="%s?return=true">%s</a>' %
                           (reverse('admin_leave_approve', kwargs={'leave_pk': obj.id}), _('Approve')))
            actions.append('<a class="button" href="%s?return=true">%s</a>' %
                           (reverse('admin_leave_reject', kwargs={'leave_pk': obj.id}), _('Reject')))

        return format_html('&nbsp;'.join(actions))

    list_display = (
        '__str__',
        'user',
        'leave_type',
        'date',
        'status',
        'description',
        'attachment',
        'item_actions',
    )
    list_filter = (
        'status',
        ('leave_type', RelatedDropdownFilter),
        ('user', RelatedDropdownFilter),
        ('leavedate__starts_at', DateTimeRangeFilter),
        ('leavedate__ends_at', DateTimeRangeFilter)
    )
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'leave_type__name', 'status',
                     'leavedate__starts_at', 'leavedate__ends_at', 'description')
    inlines = [
        LeaveDateInline,
    ]
    actions = [
        'make_approved',
        'make_rejected',
    ]
    ordering = ('-status',)


@admin.register(models.LeaveDate)
class LeaveDateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'leave', 'starts_at', 'ends_at')
    ordering = ('-starts_at',)


@admin.register(models.UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    def join_date(self, obj):
        return obj.get_join_date()

    def user_groups(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.user.groups.all())))

    list_display = ('__str__', 'user', 'gender', 'birth_date', 'user_groups', 'country', 'join_date')
    ordering = ('user',)


@admin.register(models.PerformanceType)
class PerformanceTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'description', 'multiplier')
    ordering = ('multiplier',)


class ContractUserInline(admin.TabularInline):
    model = models.ContractUser
    ordering = ("user__first_name", "user__last_name",)


@admin.register(models.ContractGroup)
class ContractGroupAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', )


class ContractChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Contract
    inlines = [
        ContractUserInline,
    ]


# @admin.register(models.ProjectContract)
class ProjectContractChildAdmin(ContractChildAdmin):
    base_model = models.ProjectContract


# @admin.register(models.ConsultancyContract)
class ConsultancyContractChildAdmin(ContractChildAdmin):
    base_model = models.ConsultancyContract


# @admin.register(models.SupportContract)
class SupportContractChildAdmin(ContractChildAdmin):
    base_model = models.SupportContract


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
    list_display = ('name', 'active', '__str__', 'company', 'customer', 'contract_users',
                    performance_types, 'starts_at', 'ends_at', 'description', 'attachment')
    list_filter = (
        PolymorphicChildModelFilter,
        ('company', RelatedDropdownFilter),
        ('customer', RelatedDropdownFilter),
        ('contractuser', RelatedDropdownFilter),
        ('performance_types', RelatedDropdownFilter),
        ('starts_at', DateRangeFilter),
        ('ends_at', DateRangeFilter),
        'active'
    )
    search_fields = ('name', 'description', 'company__name', 'customer__name', 'contractuser__user__first_name',
                     'contractuser__user__last_name', 'contractuser__user__username', 'performance_types__name')
    ordering = ('name', 'company', 'starts_at', 'ends_at', '-customer',)


@admin.register(models.ConsultancyContract)
class ConsultancyContractAdmin(admin.ModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    list_display = ('name', 'company', 'customer', 'contract_users', 'active', 'starts_at', 'ends_at', 'duration')
    list_filter = (ContractStatusFilter, ('company', RelatedDropdownFilter),
                   ('customer', RelatedDropdownFilter), ('contractuser__user', RelatedDropdownFilter))

    inlines = [
        ContractUserInline,
    ]


@admin.register(models.SupportContract)
class SupportContractAdmin(admin.ModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    list_display = ('name', 'company', 'customer', 'contract_users', 'active', 'starts_at', 'ends_at', 'day_rate', 'fixed_fee', 'fixed_fee_period')
    list_filter = (ContractStatusFilter, ('company', RelatedDropdownFilter),
                   ('customer', RelatedDropdownFilter), ('contractuser__user', RelatedDropdownFilter))

    inlines = [
        ContractUserInline,
    ]


@admin.register(models.ProjectContract)
class ProjectContractAdmin(admin.ModelAdmin):
    def contract_users(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    list_display = ('name', 'company', 'customer', 'contract_users', 'active', 'starts_at', 'ends_at', 'fixed_fee')
    list_filter = (ContractStatusFilter, ('company', RelatedDropdownFilter),
                   ('customer', RelatedDropdownFilter), ('contractuser__user', RelatedDropdownFilter))

    inlines = [
        ContractUserInline,
    ]


@admin.register(models.ContractRole)
class ContractRoleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'description')
    ordering = ('name',)


@admin.register(models.ContractUser)
class ContractUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'contract', 'contract_role')
    ordering = ('user__first_name', 'user__last_name')


@admin.register(models.ProjectEstimate)
class ProjectEstimateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'project', 'role', 'hours_estimated', )
    search_fields = ('role__name', 'project__name', 'project__customer')
    ordering = ('project', 'hours_estimated')


@admin.register(models.Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    def make_closed(self, request, queryset):
        for timesheet in queryset:
            timesheet.status = models.STATUS_CLOSED
            timesheet.save(validate=False)
    make_closed.short_description = _('Close selected timesheets')

    def make_active(self, request, queryset):
        for timesheet in queryset:
            timesheet.status = models.STATUS_ACTIVE
            timesheet.save(validate=False)
    make_active.short_description = _('Activate selected timesheets')

    def make_pending(self, request, queryset):
        for timesheet in queryset:
            timesheet.status = models.STATUS_PENDING
            timesheet.save(validate=False)
    make_pending.short_description = _('Set selected timesheets to pending')

    list_display = ('__str__', 'user', 'month', 'year', 'status')
    list_filter = (
        'status',
        ('user', RelatedDropdownFilter),
        'year',
        'month',
    )
    actions = [
        'make_closed',
        'make_active',
        'make_pending',
    ]
    ordering = ('-year', 'month', 'user__first_name', 'user__last_name')


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
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activityperformance',
                                                            'activityperformance__performance_type',
                                                            'activityperformance__contract_role',
                                                            'contract',
                                                            'timesheet',
                                                            'timesheet__user')

    def duration(self, obj):
        return obj.activityperformance.duration

    def performance_type(self, obj):
        return obj.activityperformance.performance_type

    def description(self, obj):
        return obj.activityperformance.description

    def contract_role(self, obj):
        return obj.activityperformance.contract_role

    base_model = models.Performance
    child_models = (
        models.ActivityPerformance,
        models.StandbyPerformance,
    )
    list_filter = (
        PolymorphicChildModelFilter,
        ('contract', RelatedDropdownFilter),
        ('timesheet__user', RelatedDropdownFilter),
        ('timesheet__year', DropdownFilter),
        ('timesheet__month', DropdownFilter),
        ('activityperformance__contract_role', RelatedDropdownFilter),
        ('activityperformance__performance_type', RelatedDropdownFilter),
    )
    list_display = (
        '__str__',
        'timesheet',
        'day',
        'contract',
        'performance_type',
        'duration',
        'description',
        'contract_role',
    )
