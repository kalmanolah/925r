"""Admin."""
from django.contrib import admin
from django.contrib.auth import models as auth_models
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.core.cache import cache
from django.db.models import Q, Prefetch
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django import forms
from django.urls import reverse
from django_admin_listfilter_dropdown.filters import DropdownFilter
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter
from polymorphic.admin import PolymorphicChildModelAdmin
from polymorphic.admin import PolymorphicChildModelFilter
from polymorphic.admin import PolymorphicParentModelAdmin
from rangefilter.filter import DateRangeFilter
from rangefilter.filter import DateTimeRangeFilter
from import_export.admin import ExportMixin
from import_export.resources import ModelResource
from adminsortable.admin import SortableAdmin
from ninetofiver import models, redmine
from ninetofiver.templatetags.markdown import markdown
from datetime import date
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


@admin.register(models.ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Api key admin."""

    list_display = ('__str__', 'name', 'key', 'read_only', 'user', 'created_at')
    ordering = ('-created_at',)


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
    """Company admin."""
    def logo(obj):
        return format_html('<a href="%s">%s</a>' % (obj.get_logo_url(), _('Link')))

    list_display = ('__str__', 'name', 'vat_identification_number', 'address', 'country', 'internal', logo)
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
class LeaveTypeAdmin(SortableAdmin):
    """Leave type admin."""

    list_display = ('__str__', 'name', 'description', 'overtime', 'sickness')


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
        return format_html('<br>'.join(x.html_label() for x in list(obj.leavedate_set.all())))

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
        'created_at',
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


class UserInfoForm(forms.ModelForm):
    """User info form."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)

        self.fields['redmine_id'].label = 'Redmine user'
        redmine_user_choices = cache.get_or_set('user_info_admin_redmine_id_choices',
                                                redmine.get_redmine_user_choices)
        self.fields['redmine_id'].widget = forms.Select(choices=redmine_user_choices)


@admin.register(models.UserInfo)
class UserInfoAdmin(admin.ModelAdmin):
    def join_date(self, obj):
        return obj.get_join_date()

    def user_groups(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.user.groups.all())))

    list_display = ('__str__', 'user', 'gender', 'birth_date', 'user_groups', 'country', 'join_date')
    ordering = ('user',)
    form = UserInfoForm


@admin.register(models.PerformanceType)
class PerformanceTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'description', 'multiplier')


@admin.register(models.ContractGroup)
class ContractGroupAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', )


class ContractUserInline(admin.TabularInline):
    model = models.ContractUser
    ordering = ("user__first_name", "user__last_name",)
    show_change_link = True

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Form field for foreign key."""
        if db_field.name == 'user':
            kwargs['queryset'] = auth_models.User.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ContractUserGroupInline(admin.TabularInline):
    model = models.ContractUserGroup


class ContractEstimateInline(admin.TabularInline):
    model = models.ContractEstimate


class ContractForm(forms.ModelForm):
    """Contract form."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super().__init__(*args, **kwargs)

        self.fields['redmine_id'].label = 'Redmine project'
        redmine_project_choices = cache.get_or_set('contract_admin_redmine_id_choices',
                                                   redmine.get_redmine_project_choices)
        self.fields['redmine_id'].widget = forms.Select(choices=redmine_project_choices)


class ContractResource(ModelResource):
    """Contract resource."""

    class Meta:
        """Contract resource meta class."""

        model = models.Contract
        fields = (
            'id',
            'name',
            'company__id',
            'company__name',
            'customer__id',
            'customer__name',
            'active',
            'starts_at',
            'ends_at',
            'description',
            'projectcontract__fixed_fee',
            'consultancycontract__duration',
            'consultancycontract__day_rate',
            'supportcontract_fixed_fee',
            'supportcontract__fixed_fee_period',
            'supportcontract__day_rate',
            'polymorphic_ctype__model',
        )


@admin.register(models.Contract)
class ContractParentAdmin(ExportMixin, PolymorphicParentModelAdmin):
    """Contract parent admin."""

    def get_queryset(self, request):
        return (super().get_queryset(request)
                .select_related('company', 'customer')
                .prefetch_related('contractusergroup_set',
                                  'contractusergroup_set__group', 'contractusergroup_set__contract_role',
                                  'contractuser_set', 'contractuser_set__user',
                                  'contractuser_set__contract_role',
                                  Prefetch('performance_types', queryset=(models.PerformanceType.objects
                                                                          .non_polymorphic())),
                                  Prefetch('attachments', queryset=(models.Attachment.objects
                                                                    .non_polymorphic())))
                .distinct())

    def contract_users(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractuser_set.all())))

    def contract_user_groups(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.contractusergroup_set.all())))

    def performance_type(obj):
        return format_html('<br>'.join(str(x) for x in list(obj.performance_types.all())))

    def attachments(obj):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

    def fixed_fee(obj):
        real_obj = obj.get_real_instance()
        if real_obj.__class__ in [models.ProjectContract, models.SupportContract]:
            return real_obj.fixed_fee
        return None

    def fixed_fee_period(obj):
        real_obj = obj.get_real_instance()
        if real_obj.__class__ is models.SupportContract:
            return real_obj.fixed_fee_period
        return None

    def duration(obj):
        real_obj = obj.get_real_instance()
        if real_obj.__class__ is models.ConsultancyContract:
            return real_obj.duration
        return None

    def day_rate(obj):
        real_obj = obj.get_real_instance()
        if real_obj.__class__ in [models.ConsultancyContract, models.SupportContract]:
            return real_obj.day_rate
        return None

    def item_actions(obj):
        """Actions."""
        actions = []

        actions.append('<a class="button" href="%s?contract__id__exact=%s">%s</a>' %
                       (reverse('admin:ninetofiver_invoice_changelist'), obj.id, _('Invoices')))

        return format_html('&nbsp;'.join(actions))

    resource_class = ContractResource

    base_model = models.Contract
    child_models = (
        models.ProjectContract,
        models.ConsultancyContract,
        models.SupportContract,
    )
    list_display = ('__str__', 'name', 'company', 'customer', contract_users, contract_user_groups, performance_type,
                    'active', 'starts_at', 'ends_at', 'description', attachments, fixed_fee, fixed_fee_period,
                    duration, day_rate, item_actions)

    list_filter = (
        PolymorphicChildModelFilter,
        ContractStatusFilter,
        ('company', RelatedDropdownFilter),
        ('customer', RelatedDropdownFilter),
        ('contract_groups', RelatedDropdownFilter),
        ('contractuser__user', RelatedDropdownFilter),
        ('contractusergroup__group', RelatedDropdownFilter),
        ('performance_types', RelatedDropdownFilter),
        ('starts_at', DateRangeFilter),
        ('ends_at', DateRangeFilter),
        'active'
    )
    search_fields = ('name', 'description', 'company__name', 'customer__name', 'contractuser__user__first_name',
                     'contractuser__user__last_name', 'contractuser__user__username', 'contractusergroup__group__name',
                     'performance_types__name')
    ordering = ('name', 'company', 'starts_at', 'ends_at', '-customer',)


class ContractChildAdmin(PolymorphicChildModelAdmin):
    """Base contract admin."""

    def get_queryset(self, request):
        return (super().get_queryset(request)
                .select_related('company', 'customer')
                .prefetch_related('contractusergroup_set',
                                  'contractusergroup_set__group', 'contractusergroup_set__contract_role',
                                  'contractuser_set', 'contractuser_set__user',
                                  'contractuser_set__contract_role',)
                .distinct())

    inlines = [
        ContractEstimateInline,
        ContractUserGroupInline,
        ContractUserInline,
    ]
    base_model = models.Contract
    base_form = ContractForm
    list_display = ContractParentAdmin.list_display
    list_filter = ContractParentAdmin.list_filter[1:]
    search_fields = ContractParentAdmin.search_fields
    ordering = ContractParentAdmin.ordering


@admin.register(models.ConsultancyContract)
class ConsultancyContractAdmin(ContractChildAdmin):
    """Consultancy contract admin."""

    base_model = models.ConsultancyContract


@admin.register(models.SupportContract)
class SupportContractAdmin(ContractChildAdmin):
    """Support contract admin."""

    base_model = models.SupportContract


@admin.register(models.ProjectContract)
class ProjectContractAdmin(ContractChildAdmin):
    """Project contract admin."""

    base_model = models.ProjectContract


@admin.register(models.ContractRole)
class ContractRoleAdmin(admin.ModelAdmin):
    """Contract role admin."""
    list_display = ('__str__', 'name', 'description')
    ordering = ('name',)


class ContractUserWorkScheduleInline(admin.TabularInline):
    model = models.ContractUserWorkSchedule


@admin.register(models.ContractUser)
class ContractUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'contract', 'contract_role')
    ordering = ('user__first_name', 'user__last_name')
    inlines = [
        ContractUserWorkScheduleInline,
    ]
    list_filter = (
        ('contract_role', RelatedDropdownFilter),
        ('contract__customer', RelatedDropdownFilter),
        ('user', RelatedDropdownFilter),
    )


@admin.register(models.Timesheet)
class TimesheetAdmin(admin.ModelAdmin):
    """Timesheet admin."""

    def get_queryset(self, request):
        """Get the queryset."""
        return super().get_queryset(request).select_related('user').prefetch_related('attachments')

    def attachments(obj):
        return format_html('<br>'.join('<a href="%s">%s</a>'
                           % (x.get_file_url(), str(x)) for x in list(obj.attachments.all())))

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

    def item_actions(self, obj):
        """Actions."""
        actions = []

        if obj.status == models.STATUS_PENDING:
            actions.append('<a class="button" href="%s?return=true">%s</a>' %
                           (reverse('admin_timesheet_close', kwargs={'timesheet_pk': obj.id}), _('Close')))
            actions.append('<a class="button" href="%s?return=true">%s</a>' %
                           (reverse('admin_timesheet_activate', kwargs={'timesheet_pk': obj.id}), _('Reopen')))

        return format_html('&nbsp;'.join(actions))

    list_display = ('__str__', 'user', 'month', 'year', 'status', attachments, 'item_actions')
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
    search_fields = (
        'user__username',
        'user__first_name',
        'user__last_name',
        'status',
    )
    ordering = ('-year', 'month', 'user__first_name', 'user__last_name')


@admin.register(models.Location)
class LocationAdmin(SortableAdmin):
    """Location admin."""

    list_display = (
        '__str__',
        'name',
    )
    search_fields = ('name',)


@admin.register(models.Whereabout)
class WhereaboutAdmin(admin.ModelAdmin):
    """Whereabout admin."""

    list_display = (
        '__str__',
        'timesheet',
        'location',
        'starts_at',
        'ends_at',
        'description',
    )
    list_filter = (
        ('location', RelatedDropdownFilter),
        ('timesheet__user', RelatedDropdownFilter),
        ('starts_at', DateTimeRangeFilter),
        ('ends_at', DateTimeRangeFilter)
    )
    search_fields = ('timesheet__user__username', 'timesheet__user__first_name', 'timesheet__user__last_name',
                     'location', 'starts_at', 'ends_at', 'description')
    ordering = ('-starts_at',)


class PerformanceResource(ModelResource):
    """Performance resource."""

    class Meta:
        """Performance resource meta class."""

        model = models.Performance
        fields = (
            'id',
            'timesheet__user__id',
            'timesheet__user__username',
            'timesheet__year',
            'timesheet__month',
            'timesheet__status',
            'date',
            'contract__id',
            'contract__name',
            'activityperformance__duration',
            'activityperformance__description',
            'activityperformance__performance_type__id',
            'activityperformance__performance_type__name',
            'activityperformance__contract_role__id',
            'activityperformance__contract_role__name',
            'polymorphic_ctype__model',
        )


@admin.register(models.Performance)
class PerformanceParentAdmin(ExportMixin, PolymorphicParentModelAdmin):
    """Performance parent admin."""

    resource_class = PerformanceResource

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('activityperformance',
                                                            'activityperformance__performance_type',
                                                            'activityperformance__contract_role',
                                                            'contract',
                                                            'contract__customer',
                                                            'timesheet',
                                                            'timesheet__user')

    def duration(self, obj):
        return obj.activityperformance.duration

    def performance_type(self, obj):
        return obj.activityperformance.performance_type

    def description(self, obj):
        value = obj.activityperformance.description
        value = markdown(value) if value else value
        return value

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
        ('contract__company', RelatedDropdownFilter),
        ('contract__customer', RelatedDropdownFilter),
        ('timesheet__user', RelatedDropdownFilter),
        ('timesheet__year', DropdownFilter),
        ('timesheet__month', DropdownFilter),
        ('date', DateRangeFilter),
        ('activityperformance__contract_role', RelatedDropdownFilter),
        ('activityperformance__performance_type', RelatedDropdownFilter),
    )
    list_display = (
        '__str__',
        'timesheet',
        'date',
        'contract',
        'performance_type',
        'duration',
        'description',
        'contract_role',
    )


class PerformanceChildAdmin(PolymorphicChildModelAdmin):
    base_model = models.Performance


@admin.register(models.ActivityPerformance)
class ActivityPerformanceChildAdmin(PerformanceChildAdmin):
    base_model = models.ActivityPerformance


@admin.register(models.StandbyPerformance)
class StandbyPerformanceChildAdmin(PerformanceChildAdmin):
    base_model = models.StandbyPerformance


class InvoiceItemInline(admin.TabularInline):
    """Invoice item inline."""

    model = models.InvoiceItem


@admin.register(models.Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Invoice admin."""

    def get_queryset(self, request):
        """Get the queryset."""
        return (super().get_queryset(request)
                .select_related('contract', 'contract__customer')
                .prefetch_related('invoiceitem_set'))

    def amount(self, obj):
        """Amount."""
        return sum([x.price * x.amount for x in obj.invoiceitem_set.all()])

    list_display = (
        '__str__',
        'date',
        'amount',
        'contract',
        'reference',
        'period_starts_at',
        'period_ends_at',
        'description',
    )
    list_filter = (
        ('contract', RelatedDropdownFilter),
        ('contract__company', RelatedDropdownFilter),
        ('contract__customer', RelatedDropdownFilter),
        ('date', DateTimeRangeFilter),
        ('period_starts_at', DateTimeRangeFilter),
        ('period_ends_at', DateTimeRangeFilter),
    )
    search_fields = ('reference', 'contract__name', 'contract__customer__name', 'contract__company__name',
                     'description', 'date')
    inlines = [
        InvoiceItemInline,
    ]
    ordering = ('-reference',)