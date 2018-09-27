"""ninetofiver serializers."""
from django.contrib.auth import models as auth_models
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from django_countries.serializers import CountryFieldMixin
from django.db.models import Q
from rest_framework import serializers
import logging
import datetime
from ninetofiver import models


logger = logging.getLogger(__name__)
