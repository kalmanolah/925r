"""ninetofiver URL Configuration"""
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.views.generic.base import TemplateView
from rest_framework import routers
# from rest_framework.urlpatterns import format_suffix_patterns
from django_downloadview import ObjectDownloadView
from oauth2_provider import views as oauth2_views
from registration.backends.hmac import views as registration_views
from ninetofiver import views, models


urlpatterns = [
    url(r'^api/v2/', include('ninetofiver.api_v2.urls', namespace='ninetofiver_api_v2')),
]

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns += [
    url(r'^$', views.home_view, name='home'),
    url(r'^api-docs/$', views.api_docs_view, name='api_docs'),
    url(r'^api-docs/swagger_ui/$', views.api_docs_swagger_ui_view, name='api_docs_swagger_ui'),
    url(r'^api-docs/redoc/$', views.api_docs_redoc_view, name='api_docs_redoc'),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # OAuth2
    url(r'^oauth/v2/', include(
        [
            url(r'^authorize/$', oauth2_views.AuthorizationView.as_view(template_name='ninetofiver/oauth2/authorize.pug'), name="authorize"),
            url(r'^token/$', oauth2_views.TokenView.as_view(), name="token"),
            url(r'^revoke_token/$', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
            url(r'^applications/$', oauth2_views.ApplicationList.as_view(template_name='ninetofiver/oauth2/applications/list.pug'), name="list"),
            url(r'^applications/register/$', oauth2_views.ApplicationRegistration.as_view(template_name='ninetofiver/oauth2/applications/register.pug'), name="register"),
            url(r'^applications/(?P<pk>\d+)/$', oauth2_views.ApplicationDetail.as_view(template_name='ninetofiver/oauth2/applications/detail.pug'), name="detail"),
            url(r'^applications/(?P<pk>\d+)/delete/$', oauth2_views.ApplicationDelete.as_view(template_name='ninetofiver/oauth2/applications/delete.pug'), name="delete"),
            url(r'^applications/(?P<pk>\d+)/update/$', oauth2_views.ApplicationUpdate.as_view(template_name='ninetofiver/oauth2/applications/update.pug'), name="update"),
            url(r'^authorized_tokens/$', oauth2_views.AuthorizedTokensListView.as_view(template_name='ninetofiver/oauth2/tokens/list.pug'), name="authorized-token-list"),
            url(r'^authorized_tokens/(?P<pk>\d+)/delete/$', oauth2_views.AuthorizedTokenDeleteView.as_view(template_name='ninetofiver/oauth2/tokens/delete.pug'), name="authorized-token-delete"),
        ],
        namespace='oauth2_provider',
    )),

    # Account
    url(r'^accounts/profile/$', views.account_view, name='account'),
    url(r'^accounts/password/change/$', auth_views.password_change, {'template_name': 'ninetofiver/account/password_change.pug'}, name='password_change'),
    url(r'^accounts/password/change/done/$', auth_views.password_change_done, {'template_name': 'ninetofiver/account/password_change_done.pug'}, name='password_change_done'),

    url(r'^accounts/api_keys/$', views.ApiKeyListView.as_view(), name='api-key-list'),
    url(r'^accounts/api_keys/create/$', views.ApiKeyCreateView.as_view(), name='api-key-create'),
    url(r'^accounts/api_keys/(?P<pk>\d+)/delete/$', views.ApiKeyDeleteView.as_view(), name='api-key-delete'),

    # Auth
    url(r'^auth/login/$', auth_views.login, {'template_name': 'ninetofiver/authentication/login.pug'}, name='login'),
    url(r'^auth/logout/$', auth_views.logout, {'template_name': 'ninetofiver/authentication/logout.pug'}, name='logout'),
    url(r'^auth/password/reset/$', auth_views.password_reset, {'template_name': 'ninetofiver/authentication/password_reset.pug'}, name='password_reset'),
    url(r'^auth/password/reset/done$', auth_views.password_reset_done, {'template_name': 'ninetofiver/authentication/password_reset_done.pug'}, name='password_reset_done'),
    url(r'^auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'ninetofiver/authentication/password_reset_confirm.pug'}, name='password_reset_confirm'),
    url(r'^auth/password/reset/complete/$', auth_views.password_reset_complete, {'template_name': 'ninetofiver/authentication/password_reset_complete.pug'}, name='password_reset_complete'),

    # Registration
    url(
        r'^auth/activate/complete/$',
        TemplateView.as_view(template_name='ninetofiver/registration/activation_complete.pug'),
        name='registration_activation_complete',
    ),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(
        r'^auth/activate/(?P<activation_key>[-:\w]+)/$',
        registration_views.ActivationView.as_view(template_name='ninetofiver/registration/activate.pug'),
        name='registration_activate',
    ),
    url(
        r'^auth/register/$',
        registration_views.RegistrationView.as_view(
            template_name='ninetofiver/registration/register.pug',
            email_body_template='ninetofiver/registration/activation_email.txt',
            email_subject_template='ninetofiver/registration/activation_email_subject.txt',
        ),
        name='registration_register',
    ),
    url(
        r'^auth/register/complete/$',
        TemplateView.as_view(template_name='ninetofiver/registration/register_complete.pug'),
        name='registration_complete',
    ),
    url(
        r'^auth/register/closed/$',
        TemplateView.as_view(template_name='ninetofiver/registration/register_closed.pug'),
        name='registration_disallowed',
    ),

    # Silk (profiling)
    url(r'^admin/silk/', include('silk.urls', namespace='silk')),

    # Django SQL explorer
    url(r'^admin/sqlexplorer/', include('explorer.urls')),

    # Custom admin routes
    url(r'^admin/ninetofiver/leave/approve/(?P<leave_pk>[0-9,]+)/$', views.admin_leave_approve_view, name='admin_leave_approve'),  # noqa
    url(r'^admin/ninetofiver/leave/reject/(?P<leave_pk>[0-9,]+)/$', views.admin_leave_reject_view, name='admin_leave_reject'),  # noqa
    url(r'^admin/ninetofiver/timesheet/close/(?P<timesheet_pk>[0-9,]+)/$', views.admin_timesheet_close_view, name='admin_timesheet_close'),  # noqa
    url(r'^admin/ninetofiver/timesheet/activate/(?P<timesheet_pk>[0-9,]+)/$', views.admin_timesheet_activate_view, name='admin_timesheet_activate'),  # noqa
    url(r'^admin/ninetofiver/report/$', views.admin_report_index_view, name='admin_report_index'),  # noqa
    url(r'^admin/ninetofiver/report/timesheet_contract_overview/$', views.admin_report_timesheet_contract_overview_view, name='admin_report_timesheet_contract_overview'),  # noqa
    url(r'^admin/ninetofiver/report/timesheet_overview/$', views.admin_report_timesheet_overview_view, name='admin_report_timesheet_overview'),  # noqa
    url(r'^admin/ninetofiver/report/user_range_info/$', views.admin_report_user_range_info_view, name='admin_report_user_range_info'),  # noqa
    url(r'^admin/ninetofiver/report/user_leave_overview/$', views.admin_report_user_leave_overview_view, name='admin_report_user_leave_overview'),  # noqa
    url(r'^admin/ninetofiver/report/user_work_ratio_overview/$', views.admin_report_user_work_ratio_overview_view, name='admin_report_user_work_ratio_overview'),  # noqa
    url(r'^admin/ninetofiver/report/user_overtime_overview/$', views.admin_report_user_overtime_overview_view, name='admin_report_user_overtime_overview'),  # noqa
    url(r'^admin/ninetofiver/report/resource_availability_overview/$', views.admin_report_resource_availability_overview_view, name='admin_report_resource_availability_overview'),  # noqa
    url(r'^admin/ninetofiver/report/expiring_consultancy_contract_overview/$', views.admin_report_expiring_consultancy_contract_overview_view, name='admin_report_expiring_consultancy_contract_overview'),  # noqa
    url(r'^admin/ninetofiver/report/expiring_support_contract_overview/$', views.admin_report_expiring_support_contract_overview_view, name='admin_report_expiring_support_contract_overview'),  # noqa
    url(r'^admin/ninetofiver/report/project_contract_overview/$', views.admin_report_project_contract_overview_view, name='admin_report_project_contract_overview'),  # noqa
    url(r'^admin/ninetofiver/report/project_contract_budget_overview/$', views.admin_report_project_contract_budget_overview_view, name='admin_report_project_contract_budget_overview'),  # noqa
    url(r'^admin/ninetofiver/timesheet_contract_pdf_export/(?P<user_timesheet_contract_pks>[0-9:,]+)/$', views.AdminTimesheetContractPdfExportView.as_view(), name='admin_timesheet_contract_pdf_export'),  # noqa

    # Admin
    url(r'^admin/', admin.site.urls),
]
