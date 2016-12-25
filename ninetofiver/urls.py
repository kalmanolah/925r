"""ninetofiver URL Configuration"""
from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.views.generic.base import TemplateView
from rest_framework import routers
# from rest_framework.urlpatterns import format_suffix_patterns
from registration.backends.hmac import views as registration_views
from oauth2_provider import views as oauth2_views
from ninetofiver import views

urlpatterns = [
    url(r'^api/$', views.schema_view, name='api_docs'),
]

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'companies', views.CompanyViewSet)
router.register(r'employment_contracts', views.EmploymentContractViewSet)
router.register(r'work_schedules', views.WorkScheduleViewSet)
router.register(r'user_relatives', views.UserRelativeViewSet)
router.register(r'holidays', views.HolidayViewSet)
router.register(r'leave_types', views.LeaveTypeViewSet)
router.register(r'leaves', views.LeaveViewSet)
router.register(r'leave_dates', views.LeaveDateViewSet)
router.register(r'performance_types', views.PerformanceTypeViewSet)
router.register(r'contracts/project', views.ProjectContractViewSet)
router.register(r'contracts/consultancy', views.ConsultancyContractViewSet)
router.register(r'contracts/support', views.SupportContractViewSet)
router.register(r'contracts', views.ContractViewSet)
router.register(r'contract_roles', views.ContractRoleViewSet)
router.register(r'contract_users', views.ContractUserViewSet)
router.register(r'timesheets', views.TimesheetViewSet)
router.register(r'performances/activity', views.ActivityPerformanceViewSet)
router.register(r'performances/standby', views.StandbyPerformanceViewSet)
router.register(r'performances', views.PerformanceViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += [
    url(r'^$', views.home_view, name='home'),
    url(r'^api/v1/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    # # OAuth2
    url(r'^oauth/v2/', include(
        [
            url(r'^authorize/$', oauth2_views.AuthorizationView.as_view(template_name='ninetofiver/oauth2/authorize.jade'), name="authorize"),
            url(r'^token/$', oauth2_views.TokenView.as_view(), name="token"),
            url(r'^revoke_token/$', oauth2_views.RevokeTokenView.as_view(), name="revoke-token"),
            url(r'^applications/$', oauth2_views.ApplicationList.as_view(template_name='ninetofiver/oauth2/applications/list.jade'), name="list"),
            url(r'^applications/register/$', oauth2_views.ApplicationRegistration.as_view(template_name='ninetofiver/oauth2/applications/register.jade'), name="register"),
            url(r'^applications/(?P<pk>\d+)/$', oauth2_views.ApplicationDetail.as_view(template_name='ninetofiver/oauth2/applications/detail.jade'), name="detail"),
            url(r'^applications/(?P<pk>\d+)/delete/$', oauth2_views.ApplicationDelete.as_view(template_name='ninetofiver/oauth2/applications/delete.jade'), name="delete"),
            url(r'^applications/(?P<pk>\d+)/update/$', oauth2_views.ApplicationUpdate.as_view(template_name='ninetofiver/oauth2/applications/update.jade'), name="update"),
            url(r'^authorized_tokens/$', oauth2_views.AuthorizedTokensListView.as_view(template_name='ninetofiver/oauth2/tokens/list.jade'), name="authorized-token-list"),
            url(r'^authorized_tokens/(?P<pk>\d+)/delete/$', oauth2_views.AuthorizedTokenDeleteView.as_view(template_name='ninetofiver/oauth2/tokens/delete.jade'), name="authorized-token-delete"),
        ],
        namespace='oauth2_provider',
    )),

    # Account
    url(r'^accounts/profile/$', views.account_view, name='account'),
    url(r'^accounts/password/change/$', auth_views.password_change, {'template_name': 'ninetofiver/account/password_change.jade'}, name='password_change'),
    url(r'^accounts/password/change/done/$', auth_views.password_change_done, {'template_name': 'ninetofiver/account/password_change_done.jade'}, name='password_change_done'),

    # Auth
    url(r'^auth/login/$', auth_views.login, {'template_name': 'ninetofiver/authentication/login.jade'}, name='login'),
    url(r'^auth/logout/$', auth_views.logout, {'template_name': 'ninetofiver/authentication/logout.jade'}, name='logout'),
    url(r'^auth/password/reset/$', auth_views.password_reset, {'template_name': 'ninetofiver/authentication/password_reset.jade'}, name='password_reset'),
    url(r'^auth/password/reset/done$', auth_views.password_reset_done, {'template_name': 'ninetofiver/authentication/password_reset_done.jade'}, name='password_reset_done'),
    url(r'^auth/password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$', auth_views.password_reset_confirm, {'template_name': 'ninetofiver/authentication/password_reset_confirm.jade'}, name='password_reset_confirm'),
    url(r'^auth/password/reset/complete/$', auth_views.password_reset_complete, {'template_name': 'ninetofiver/authentication/password_reset_complete.jade'}, name='password_reset_complete'),

    # Registration
    url(
        r'^auth/activate/complete/$',
        TemplateView.as_view(template_name='ninetofiver/registration/activation_complete.jade'),
        name='registration_activation_complete',
    ),
    # The activation key can make use of any character from the
    # URL-safe base64 alphabet, plus the colon as a separator.
    url(
        r'^auth/activate/(?P<activation_key>[-:\w]+)/$',
        registration_views.ActivationView.as_view(template_name='ninetofiver/registration/activate.jade'),
        name='registration_activate',
    ),
    url(
        r'^auth/register/$',
        registration_views.RegistrationView.as_view(
            template_name='ninetofiver/registration/register.jade',
            email_body_template='ninetofiver/registration/activation_email.txt',
            email_subject_template='ninetofiver/registration/activation_email_subject.txt',
        ),
        name='registration_register',
    ),
    url(
        r'^auth/register/complete/$',
        TemplateView.as_view(template_name='ninetofiver/registration/register_complete.jade'),
        name='registration_complete',
    ),
    url(
        r'^auth/register/closed/$',
        TemplateView.as_view(template_name='ninetofiver/registration/register_closed.jade'),
        name='registration_disallowed',
    ),

    # Admin
    url(r'^admin/', admin.site.urls),
]
