"""ninetofiver models."""
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth import models as auth_models
from polymorphic.models import PolymorphicModel, PolymorphicManager
from django_countries.fields import CountryField
from datetime import datetime


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

    name = models.CharField(unique=True, max_length=255)
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
    country = CountryField()

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'companies'

    def __str__(self):
        """Return a string representation."""
        # return '%s [%s]' % (self.name, self.vat_identification_number)
        return self.name


class WorkSchedule(BaseModel):

    """Work schedule model."""

    label = models.CharField(unique=True, max_length=255)
    monday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    tuesday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    wednesday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    thursday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    friday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    saturday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )
    sunday = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(24),
        ]
    )

    def __str__(self):
        """Return a string representation."""
        return self.label


class EmploymentContract(BaseModel):

    """Employment contract model."""

    def company_choices():
        return {'internal': True}

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    work_schedule = models.ForeignKey(WorkSchedule, on_delete=models.PROTECT)
    started_at = models.DateField()
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.company)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        user = data.get('user', getattr(instance, 'user', None))
        company = data.get('company', getattr(instance, 'company', None))
        started_at = data.get('started_at', getattr(instance, 'started_at', None))
        ended_at = data.get('ended_at', getattr(instance, 'ended_at', None))

        # Verify whether the end date of the employment contract
        # comes after the start date
        if ended_at:
            if ended_at < started_at:
                raise ValidationError(
                    _('The end date of an employment contract should always come before the start date'),
                )

        # Verify whether user has an active employment contract for the same
        # company/period
        if user and company:
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
            'user': getattr(self, 'user', None),
            'company': getattr(self, 'company', None),
            'started_at': getattr(self, 'started_at', None),
            'ended_at': getattr(self, 'ended_at', None),
        }


class UserRelative(BaseModel):

    """User relative model."""

    GENDER_CHOICES = (
        ('m', _('Male')),
        ('f', _('Female')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    birth_date = models.DateField()
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES)
    relation = models.CharField(max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.name, self.relation, self.user)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        birth_date = data.get('birth_date', getattr(instance, 'birth_date', None))

        # Verify whether the birth date of the relative comes before "now"
        if birth_date:
            if birth_date > datetime.now().date():
                raise ValidationError(
                    _('A birth date should not be set in the future'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'birth_date': getattr(self, 'birth_date', None),
        }


class Holiday(BaseModel):

    """Holiday model."""

    name = models.CharField(max_length=255)
    date = models.DateField()
    country = CountryField()

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.name, self.country.name)


class LeaveType(BaseModel):

    """Leave type model."""

    label = models.CharField(unique=True, max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class Leave(BaseModel):

    """Leave model."""

    STATUS_CHOICES = (
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='DRAFT')
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.leave_type, self.user)


class LeaveDate(BaseModel):

    """Leave date model."""

    leave = models.ForeignKey(Leave, on_delete=models.CASCADE)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.starts_at.strftime('%Y-%m-%d %H:%M:%S'), self.ends_at.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        starts_at = data.get('starts_at', getattr(instance, 'starts_at', None))
        ends_at = data.get('ends_at', getattr(instance, 'ends_at', None))

        # Verify whether the start datetime of the leave date comes before the end datetime
        if starts_at and ends_at:
            if starts_at >= ends_at:
                raise ValidationError(
                    _('The start date should be set before the end date'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'starts_at': getattr(self, 'starts_at', None),
            'ends_at': getattr(self, 'ends_at', None)
        }


class PerformanceType(BaseModel):

    """Performance type model."""

    label = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(5),
        ]
    )

    def __str__(self):
        """Return a string representation."""
        return '%s [%s%%]' % (self.label, int(self.multiplier * 100))


class Contract(BaseModel):

    """Contract model."""

    def company_choices():
        return {'internal': True}

    label = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    customer = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customercontact_set')
    active = models.BooleanField(default=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.label, self.company, self.customer)


class ContractRole(BaseModel):

    """Contract role model (no pun intended)."""

    label = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class ContractUser(BaseModel):

    """Contract user model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'contract', 'contract_role'),)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.contract_role)
