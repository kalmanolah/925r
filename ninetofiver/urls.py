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
from ninetofiver import views, models, feeds


urlpatterns = [
    url(r'^api/$', views.schema_view, name='api_docs'),
]

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'companies', views.CompanyViewSet)
router.register(r'employment_contract_types', views.EmploymentContractTypeViewSet)
router.register(r'employment_contracts', views.EmploymentContractViewSet)
router.register(r'work_schedules', views.WorkScheduleViewSet)
router.register(r'user_relatives', views.UserRelativeViewSet)
router.register(r'user_infos', views.UserInfoViewSet)
router.register(r'holidays', views.HolidayViewSet)
router.register(r'leave_types', views.LeaveTypeViewSet)
router.register(r'leaves', views.LeaveViewSet)
router.register(r'leave_dates', views.LeaveDateViewSet)
router.register(r'performance_types', views.PerformanceTypeViewSet)
router.register(r'contracts/project', views.ProjectContractViewSet, base_name='projectcontract')
router.register(r'contracts/consultancy', views.ConsultancyContractViewSet, base_name='consultancycontract')
router.register(r'contracts/support', views.SupportContractViewSet, base_name='supportcontract')
router.register(r'contracts', views.ContractViewSet)
router.register(r'contract_roles', views.ContractRoleViewSet)
router.register(r'contract_users', views.ContractUserViewSet)
router.register(r'contract_groups', views.ContractGroupViewSet)
router.register(r'timesheets', views.TimesheetViewSet)
router.register(r'whereabouts', views.WhereaboutViewSet)
router.register(r'performances/activity', views.ActivityPerformanceViewSet, base_name='activityperformance')
router.register(r'performances/standby', views.StandbyPerformanceViewSet)
router.register(r'performances', views.PerformanceViewSet)
router.register(r'project_estimates', views.ProjectEstimateViewSet)
router.register(r'attachments', views.AttachmentViewSet)
router.register(r'my_leaves', views.MyLeaveViewSet, base_name='myleave')
router.register(r'my_leave_dates', views.MyLeaveDateViewSet, base_name='myleavedate')
router.register(r'my_timesheets', views.MyTimesheetViewSet, base_name='mytimesheet')
router.register(r'my_contracts', views.MyContractViewSet, base_name='mycontract')
router.register(r'my_contract_users', views.MyContractUserViewSet, base_name='mycontractuser')
router.register(r'my_performances/activity', views.MyActivityPerformanceViewSet, base_name='myactivityperformance')
router.register(r'my_performances/standby', views.MyStandbyPerformanceViewSet, base_name='mystandbyperformance')
router.register(r'my_performances', views.MyPerformanceViewSet, base_name='myperformance')
router.register(r'my_attachments', views.MyAttachmentViewSet, base_name='myattachment')
router.register(r'my_workschedules', views.MyWorkScheduleViewSet, base_name='myworkschedule')

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns += [
    url(r'^$', views.home_view, name='home'),
    url(r'^api/v1/', include(router.urls + [
        url(r'^services/my_user/$', views.MyUserServiceAPIView.as_view(), name='my_user_service'),
        url(r'^services/leave_request/$', views.LeaveRequestServiceAPIView.as_view(), name='leave_request_service'),
        url(r'^services/performance_import/$', views.PerformanceImportServiceAPIView.as_view(), name='performance_import_service'),
        url(r'^services/monthly_availability/$', views.MonthlyAvailabilityServiceAPIView.as_view(), name='monthly_availability_service'),
        url(r'^services/month_info/$', views.MonthInfoServiceAPIView.as_view(), name='month_info_service'),
        url(r'^services/range_info/$', views.RangeInfoServiceAPIView.as_view(), name='range_info_service'),
        url(r'^services/download_attachment/(?P<slug>[A-Za-z0-9_-]+)/$', ObjectDownloadView.as_view(model=models.Attachment, file_field='file'), name='download_attachment_service'),
        url(r'^services/my_timesheet_contract_pdf_export/(?P<timesheet_pk>[0-9]+)/(?P<contract_pk>[0-9_-]+)/$', views.MyTimesheetContractPdfExportServiceAPIView.as_view(), name='my_timesheet_contract_pdf_export_service'),
        url(r'^services/feeds/leaves\.ics$', views.LeaveFeedServiceAPIView.as_view()),
    ])),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # # OAuth2
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

    # Custom admin routes
    url(r'^admin/ninetofiver/leave/approve/(?P<leave_pk>[0-9,]+)/$', views.admin_leave_approve_view, name='admin_leave_approve'),  # noqa
    url(r'^admin/ninetofiver/leave/reject/(?P<leave_pk>[0-9,]+)/$', views.admin_leave_reject_view, name='admin_leave_reject'),  # noqa

    # Admin
    url(r'^admin/', admin.site.urls),
]
