from django import forms
from django.contrib.auth import models as auth_models
from ninetofiver import models
from ninetofiver.redmine import choices
from ninetofiver import widgets


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s %s" % (obj.first_name, obj.last_name)


class UserInfoAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))
    redmine_id = forms.ChoiceField(choices=choices.get_redmine_user_choices())

    class Meta:
        model = models.UserInfo
        fields = ['user', 'gender', 'birth_date', 'country', 'redmine_id']


class UserRelativeAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))

    class Meta:
        model = models.UserRelative
        fields = ['user', 'gender', 'birth_date', 'name', 'relation']


class TimesheetAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))

    class Meta:
        model = models.Timesheet
        fields = ['user', 'month', 'year', 'status']


class LeaveAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))

    class Meta:
        model = models.Leave
        fields = ['user', 'leave_type', 'description', 'status', 'attachments']


class ContractUserAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))

    class Meta:
        model = models.ContractUser
        fields = ['user', 'contract', 'contract_role']


class EmploymentContractAdminForm(forms.ModelForm):
    user = UserModelChoiceField(queryset=auth_models.User.objects.order_by(
        'first_name', 'last_name'))

    class Meta:
        model = models.EmploymentContract
        fields = [
            'user', 'company', 'employment_contract_type', 'work_schedule',
            'started_at', 'ended_at'
        ]


class ProjectContractAdminForm(forms.ModelForm):
    redmine_choices = choices.get_redmine_project_choices()

    redmine_id = forms.ChoiceField(choices=redmine_choices)

    class Meta:
        model = models.ProjectContract
        fields = [
            'label', 'description', 'customer', 'company', 'active',
            'performance_types', 'contract_groups', 'attachments',
            'redmine_id', 'external_only', 'fixed_fee', 'starts_at', 'ends_at'
        ]


class ConsultancyContractAdminForm(forms.ModelForm):
    redmine_id = forms.ChoiceField(choices=choices.get_redmine_project_choices())

    class Meta:
        model = models.ConsultancyContract
        fields = [
            'label', 'description', 'customer', 'company', 'active',
            'performance_types', 'contract_groups', 'attachments',
            'redmine_id', 'external_only', 'starts_at', 'ends_at', 'duration',
            'day_rate'
        ]


class SupportContractAdminForm(forms.ModelForm):
    redmine_id = forms.ChoiceField(choices=choices.get_redmine_project_choices())

    class Meta:
        model = models.SupportContract
        fields = [
            'label', 'description', 'customer', 'company', 'active',
            'performance_types', 'contract_groups', 'attachments',
            'redmine_id', 'external_only', 'day_rate', 'fixed_fee',
            'fixed_fee_period', 'starts_at', 'ends_at'
        ]


class WorkScheduleAdminForm(forms.ModelForm):
    class Meta:
        model = models.WorkSchedule
        fields = [
            'label', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
            'saturday', 'sunday'
        ]
        widgets = {
            'monday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'tuesday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'wednesday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'thursday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'friday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'saturday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'}),
            'sunday':
            widgets.DurationInput(
                attrs={'min': '0',
                       'max': '24',
                       'step': '0.50'})
        }
