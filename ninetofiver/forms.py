from django import forms
from django.contrib import admin
from django.contrib.auth import models as auth_models
from ninetofiver import models


class UserModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "%s, %s" % (obj.first_name, obj.last_name)


class UserInfoAdminForm(forms.ModelForm):
    user = UserModelChoiceField(
        queryset = auth_models.User.objects.order_by('first_name', 'last_name'))
    class Meta:
        model = models.UserInfo
        fields = ['user', 'gender', 'birth_date', 'country', 'join_date']
