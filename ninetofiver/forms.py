from django import forms
from django.contrib import admin
from django.contrib.auth import models as auth_models
from ninetofiver import models


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        if obj.first_name:
            return "%s, %s" % (obj.first_name, obj.last_name)
        else:
            return "%s" % (obj)

class UserInfoAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.UserInfo
        fields = ['user', 'gender', 'birth_date', 'country', 'join_date']


class TimesheetAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.Timesheet
        fields = ['user', 'month', 'year', 'status']


class LeaveAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.Leave
        fields = ['user', 'leave_type', 'description', 'status', 'attachments']


class ContractUserAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.ContractUser
        fields = ['user', 'contract', 'contract_role']


class EmploymentContractAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.EmploymentContract
        fields = ['user', 'company', 'employment_contract_type', 'work_schedule', 'started_at', 'ended_at']
