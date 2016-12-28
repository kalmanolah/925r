"""ninetofiver models."""
from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _
from django.contrib.auth import models as auth_models
from polymorphic.models import PolymorphicModel, PolymorphicManager
from django_countries.fields import CountryField
from model_utils import Choices
from datetime import datetime
from calendar import monthrange
from decimal import Decimal
from ninetofiver.utils import merge_dicts


# Monkey patch user model to serialize properly
def user_str(self):
    if self.get_full_name():
        return '%s [%s]' % (self.get_full_name(), self.username)
    return self.username
auth_models.User.__str__ = user_str


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

    GENDER = Choices(
        ('m', _('Male')),
        ('f', _('Female')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    birth_date = models.DateField()
    gender = models.CharField(max_length=2, choices=GENDER)
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


class Timesheet(BaseModel):

    """Timesheet model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    year = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(2000),
            validators.MaxValueValidator(3000),
        ]
    )
    month = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(12),
        ]
    )
    closed = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'year', 'month'),)

    def __str__(self):
        """Return a string representation."""
        return '%02d-%04d [%s]' % (self.month, self.year, self.user)

    # @classmethod
    # def perform_additional_validation(cls, data, instance=None):
    #     """Perform additional validation on the object."""
    #     instance_id = instance.id if instance else None # noqa
    #     year = data.get('year', getattr(instance, 'year', None))
    #     month = data.get('month', getattr(instance, 'month', None))
    #
    #     if year and month:
    #         # Ensure no timesheet can be created for the future
    #         today = datetime.now().date()
    #
    #         if (year > today.year) or ((year == today.year) and (month > today.month)):
    #             raise ValidationError(
    #                 _('Timesheets cannot be created for future months'),
    #             )
    #
    # def get_validation_args(self):
    #     """Get a dict used for validation based on this instance."""
    #     return {
    #         'year': getattr(self, 'year', None),
    #         'month': getattr(self, 'month', None),
    #     }


class Holiday(BaseModel):

    """Holiday model."""

    name = models.CharField(max_length=255)
    date = models.DateField()
    country = CountryField()

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.name, self.country.name)

    class Meta(BaseModel.Meta):
        unique_together = (('name', 'date', 'country'),)


class LeaveType(BaseModel):

    """Leave type model."""

    label = models.CharField(unique=True, max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class Leave(BaseModel):

    """Leave model."""

    STATUS = Choices(
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=STATUS, default=STATUS.DRAFT)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.leave_type, self.user)


class LeaveDate(BaseModel):

    """Leave date model."""

    leave = models.ForeignKey(Leave, on_delete=models.CASCADE)
    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.starts_at.strftime('%Y-%m-%d %H:%M:%S'), self.ends_at.strftime('%Y-%m-%d %H:%M:%S'))

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        timesheet = data.get('timesheet', getattr(instance, 'timesheet', None))
        starts_at = data.get('starts_at', getattr(instance, 'starts_at', None))
        ends_at = data.get('ends_at', getattr(instance, 'ends_at', None))
        leave = data.get('leave', getattr(instance, 'leave', None))

        if starts_at and ends_at:
            # Verify whether the start datetime of the leave date comes before the end datetime
            if starts_at >= ends_at:
                raise ValidationError(
                    _('The start date should be set before the end date'),
                )

            # Verify whether start and end datetime of the leave date occur on the same date
            if starts_at.date() != ends_at.date():
                raise ValidationError(
                    _('The start date should occur on the same day as the end date'),
                )

            if leave:
                # Check whether the user already has leave planned during this time frame
                existing = cls.objects.filter(
                    models.Q(
                        leave__user=leave.user,
                    ) &
                    models.Q(
                        starts_at__lte=ends_at,
                        ends_at__gte=starts_at,
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
                        _('User already has leave planned during this time'),
                    )

            if timesheet:
                if (starts_at.year != timesheet.year) or (starts_at.month != timesheet.month):
                    raise ValidationError(
                        _('You cannot attach leave dates to a timesheet for a different month')
                    )

        if timesheet:
            if timesheet.closed:
                raise ValidationError(
                    _('You cannot attach leave dates to a closed timesheet'),
                )




    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'timesheet': getattr(self, 'timesheet', None),
            'starts_at': getattr(self, 'starts_at', None),
            'ends_at': getattr(self, 'ends_at', None),
            'leave': getattr(self, 'leave', None),
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
    performance_types = models.ManyToManyField(PerformanceType, blank=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.label, self.company, self.customer)


class ProjectContract(Contract):

    """Project contract model."""


class ConsultancyContract(Contract):

    """Consultancy contract model."""

    day_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999),
        ]
    )
    starts_at = models.DateField()
    ends_at = models.DateField(blank=True, null=True)
    duration = models.PositiveSmallIntegerField(blank=True, null=True)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        starts_at = data.get('starts_at', getattr(instance, 'starts_at', None))
        ends_at = data.get('ends_at', getattr(instance, 'ends_at', None))

        if starts_at and ends_at:
            # Verify whether the start date of the contract comes before the end date
            if starts_at >= ends_at:
                raise ValidationError(
                    _('The start date should be set before the end date'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'starts_at': getattr(self, 'starts_at', None),
            'ends_at': getattr(self, 'ends_at', None),

        }


class SupportContract(Contract):

    """Support contract model."""

    FIXED_FEE_PERIOD = Choices(
        ('DAILY', _('Daily')),
        ('WEEKLY', _('Weekly')),
        ('MONTHLY', _('Monthly')),
        ('YEARLY', _('Yearly')),
    )

    day_rate = models.DecimalField(
        blank=True,
        null=True,
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999),
        ]
    )
    fixed_fee = models.DecimalField(
        blank=True,
        null=True,
        max_digits=9,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999999),
        ]
    )
    fixed_fee_period = models.CharField(blank=True, null=True, max_length=10, choices=FIXED_FEE_PERIOD)
    starts_at = models.DateField()
    ends_at = models.DateField(blank=True, null=True)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        starts_at = data.get('starts_at', getattr(instance, 'starts_at', None))
        ends_at = data.get('ends_at', getattr(instance, 'ends_at', None))
        day_rate = data.get('day_rate', getattr(instance, 'day_rate', None))
        fixed_fee = data.get('fixed_fee', getattr(instance, 'fixed_fee', None))
        fixed_fee_period = data.get('fixed_fee_period', getattr(instance, 'fixed_fee_period', None))

        if starts_at and ends_at:
            # Verify whether the start date of the contract comes before the end date
            if starts_at >= ends_at:
                raise ValidationError(
                    _('The start date should be set before the end date'),
                )

        # Ensure we have either a day rate or a fixed fee + period, but never both
        if day_rate:
            if fixed_fee:
                raise ValidationError(
                    _('A contract can not have both a fixed fee and a day rate'),
                )
        elif fixed_fee:
            if not fixed_fee_period:
                raise ValidationError(
                    _('A contract with a fixed fee requires a fixed fee period'),
                )
        else:
            raise ValidationError(
                _('A contract should have either a fixed fee or a day rate'),
            )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'starts_at': getattr(self, 'starts_at', None),
            'ends_at': getattr(self, 'ends_at', None),
            'day_rate': getattr(self, 'day_rate', None),
            'fixed_fee': getattr(self, 'fixed_fee', None),
            'fixed_fee_period': getattr(self, 'fixed_fee_period', None),
        }


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


class Performance(BaseModel):

    """Performance model."""

    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    day = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(31),
        ]
    )

    def __str__(self):
        """Return a string representation."""
        return '%s-%s' % (self.day, self.timesheet)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        timesheet = data.get('timesheet', getattr(instance, 'timesheet', None))
        day = data.get('day', getattr(instance, 'day', None))

        if timesheet:
            # Ensure no performance is added/modified for a closed timesheet
            if timesheet.closed:
                raise ValidationError(
                    _('Performance attached to a closed timesheet cannot be modified'),
                )

            if day:
                # Verify whether the day is valid for the month/year of the timesheet
                month_days = monthrange(timesheet.year, timesheet.month)[1]

                if day > month_days:
                    raise ValidationError(
                        _('There are only %s days in the month this timesheet is attached to' % month_days),
                    )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'timesheet': getattr(self, 'timesheet', None),
            'day': getattr(self, 'day', None),
        }


class ActivityPerformance(Performance):

    """Activity performance model."""

    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    performance_type = models.ForeignKey(PerformanceType, on_delete=models.PROTECT)
    description = models.TextField(max_length=255, blank=True, null=True)
    duration = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        validators=[
            validators.MinValueValidator(Decimal('0.01')),
            validators.MaxValueValidator(24),
        ]
    )

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.performance_type, super().__str__())

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        super().perform_additional_validation(data, instance=instance)

        instance_id = instance.id if instance else None # noqa
        contract = data.get('contract', getattr(instance, 'contract', None))
        performance_type = data.get('performance_type', getattr(instance, 'performance_type', None))

        if contract and performance_type:
            # Ensure the performance type is valid for the contract
            allowed_types = list(contract.performance_types.all())

            if allowed_types and (performance_type not in allowed_types):
                raise ValidationError(
                    _('The selected performance type is not valid for the selected contract'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return merge_dicts(super().get_validation_args(), {
            'contract': getattr(self, 'contract', None),
            'performance_type': getattr(self, 'performance_type', None),
        })


class StandbyPerformance(Performance):

    """Standby (oncall) performance model."""

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (_('Standby'), super().__str__())
