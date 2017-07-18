"""redmine URL configuration."""
from django.conf.urls import include, url
from rest_framework import routers
from ninetofiver.redmine import views

router = routers.DefaultRouter()
router.register(r'time_entries', views.RedmineTimeEntryViewSet, base_name='redminetimeentry')

urlpatterns = [
  url(r'^', include(router.urls))
]
