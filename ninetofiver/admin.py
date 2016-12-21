from django.contrib import admin
from django.utils.html import format_html
from polymorphic.admin import PolymorphicParentModelAdmin, PolymorphicChildModelAdmin
from ninetofiver import models


@admin.register(models.Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'vat_identification_number', 'address', 'country', 'internal')


@admin.register(models.EmploymentContract)
class EmploymentContractAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'company', 'started_at', 'ended_at')


@admin.register(models.WorkSchedule)
class WorkScheduleAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')


@admin.register(models.UserRelative)
class UserRelativeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'user', 'relation', 'gender', 'birth_date')


@admin.register(models.Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'name', 'date', 'country')


@admin.register(models.LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'label')


class LeaveDateInline(admin.TabularInline):
    model = models.LeaveDate


@admin.register(models.Leave)
class LeaveAdmin(admin.ModelAdmin):
    def leave_dates(self, obj):
        return format_html('<br>'.join(str(x) for x in list(obj.leavedate_set.all())))

    list_display = ('__str__', 'user', 'leave_type', 'leave_dates', 'status', 'description')
    inlines = [
        LeaveDateInline,
    ]


@admin.register(models.LeaveDate)
class LeaveDateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'leave', 'starts_at', 'ends_at')
