"""ninetofiver models."""
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth import models as auth_models
from polymorphic.models import PolymorphicModel, PolymorphicManager
from django_countries.fields import CountryField


class BaseManager(PolymorphicManager):

    """Base manager."""


class BaseModel(PolymorphicModel):

    """Abstract base model."""

    objects = BaseManager()

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        pass

    def validate_unique(self, *args, **kwargs):
        """Validate whether the object is unique."""
        super().validate_unique(*args, **kwargs)
        self.perform_additional_validation(self.get_validation_args(), instance=self)

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {}

    def get_absolute_url(self):
        """Get an absolute URL for the object."""
        from django.urls import reverse
        # return reverse('%s-detail' % self.__class__._meta.verbose_name.replace(' ', ''), args=[str(self.id)])
        return reverse('%s-detail' % self.__class__.__name__.lower(), args=[str(self.id)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(BaseModel):

    """Company model."""

    label = models.CharField(unique=True, max_length=255)
    vat_identification_number = models.CharField(
        max_length=15,
        unique=True,
        validators=[
            validators.RegexValidator(
                regex='^[A-Z]{2}[a-zA-Z0-9]{2,13}$',
                message=_('Invalid VAT identification number'),
            ),
        ]
    )
    address = models.TextField(max_length=255)
    internal = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'companies'

    def __str__(self):
        """Return a string representation."""
        # return '%s [%s]' % (self.label, self.vat_identification_number)
        return self.label


class EmploymentContract(BaseModel):

    """Employment contract model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    legal_country = CountryField()
    started_at = models.DateField()
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.company)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        user = data.get('user', instance.user if instance else None)
        company = data.get('company', instance.company if instance else None)
        started_at = data.get('started_at', instance.started_at if instance else None)
        ended_at = data.get('ended_at', instance.ended_at if instance else None)

        # Verify whether the end date of the employment contract
        # comes after the start date
        if ended_at:
            if ended_at < started_at:
                raise ValidationError(
                    _('The end date of an employment contract should always come before the start date'),
                )

        # Verify whether user has an active employment contract for the same
        # company/period
        existing = None
        if ended_at:
            existing = cls.objects.filter(
                models.Q(
                    user=user,
                    company=company,
                ) &
                (
                    models.Q(
                        ended_at__isnull=True,
                        started_at__lte=ended_at,
                    ) |
                    models.Q(
                        ended_at__isnull=False,
                        started_at__lte=ended_at,
                        ended_at__gte=started_at,
                    )
                )
            )
        else:
            existing = cls.objects.filter(
                models.Q(
                    user=user,
                    company=company,
                ) &
                (
                    models.Q(
                        ended_at__isnull=True,
                    ) |
                    models.Q(
                        ended_at__isnull=False,
                        started_at__lte=started_at,
                        ended_at__gte=started_at,
                    )
                )
            )

        if instance_id:
            existing = existing.exclude(id=instance_id)

        try:
            existing = existing.all()[0]
        except (cls.DoesNotExist, IndexError):
            existing = None

        if existing:
            raise ValidationError(
                _('User already has an active employment contract for this company for this period'),
            )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'user': self.user,
            'company': self.company,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
        }
