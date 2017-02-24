"""ninetofiver models."""
import humanize
import uuid

from calendar import monthrange
from datetime import datetime
from decimal import Decimal
from django.contrib.auth import models as auth_models
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _
from django_countries.fields import CountryField
from model_utils import Choices
from ninetofiver.utils import merge_dicts
from polymorphic.models import PolymorphicManager
from polymorphic.models import PolymorphicModel


# Monkey patch user model to serialize properly
def user_str(self):
    if self.get_full_name():
        return '%s' % (self.get_full_name())
    return self.username
auth_models.User.__str__ = user_str

# Define ordering of the User
auth_models.User._meta.ordering = ['first_name', 'last_name']


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



###########################################
# COMPANY
###########################################

class Company(BaseModel):
# Defines the information used for internal and external companies, between whom contracts are made

    """Company model."""

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
    name = models.CharField(unique=True, max_length=255)
    address = models.TextField(max_length=255)
    country = CountryField()
    internal = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        """Return a string representation."""
        # return '%s [%s]' % (self.name, self.vat_identification_number)
        return self.name



###########################################
# WORKSCHEDULE
###########################################

class WorkSchedule(BaseModel):
# Defines the workschedule for a user

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



###########################################
# EMPLOYMENTCONTRACT
###########################################

class EmploymentContractType(BaseModel):
# Defines the type of employmentContract (PM, HR etc.)

    """Employment contract type model."""

    label = models.CharField(unique=True, max_length=255)

    class Meta(BaseModel.Meta):
        ordering = ['label']

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class EmploymentContract(BaseModel):
# Defines an internal contract and binds a user, contractType and workschedule

    """Employment contract model."""

    def company_choices():
        return {'internal': True}

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    employment_contract_type = models.ForeignKey(EmploymentContractType, on_delete=models.PROTECT)
    work_schedule = models.ForeignKey(WorkSchedule, on_delete=models.PROTECT)
    started_at = models.DateField()
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s, %s]' % (self.user, self.company, self.employment_contract_type)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        user = data.get('user', getattr(instance, 'user', None))
        company = data.get('company', getattr(instance, 'company', None))
        started_at = data.get('started_at', getattr(instance, 'started_at', None))
        ended_at = data.get('ended_at', getattr(instance, 'ended_at', None))

        if ended_at:
            """Verify whether the end date of the employment contract comes after the start date"""
            if ended_at < started_at:
                raise ValidationError(
                    _('The end date of an employment contract should always come before the start date'),
                )

        if user and company:
            """Verify whether user has an active employment contract for the same company/period"""
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



###########################################
# USER
###########################################

class UserRelative(BaseModel):
# Defines the information for a relative and binds it to a user

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

            if birth_date.year < (datetime.now().year - 110):
                raise ValidationError(
                    _('There are only a handful of people over the age of 110 in the world, you are not one of them.'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'birth_date': getattr(self, 'birth_date', None),
        }


class UserInfo(BaseModel):
# Defines the extra user information

    """User info model."""

    # Only 2 genders?! it's the current year guys
    GENDER = Choices(
        ('m', _('Male')),
        ('f', _('Female')),
    )

    user = models.OneToOneField(auth_models.User, on_delete=models.CASCADE)        
    birth_date = models.DateField()
    gender = models.CharField(max_length=2, choices=GENDER)
    country = CountryField()

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.birth_date)

    @classmethod
    def perform_additional_validation(cls, data, instance=None):
        """Perform additional validation on the object."""
        instance_id = instance.id if instance else None # noqa
        birth_date = data.get('birth_date', getattr(instance, 'birth_date', None))

        if birth_date:
            if birth_date > datetime.now().date():
                """Verify whether the birth date of user comes before 'now'"""
                raise ValidationError(
                    _('A birth date should not be set in the future'),
                )

            if birth_date.year < (datetime.now().year - 100):
                """Verify whether age of user would be > 100 """
                raise ValidationError(
                    _('There are only a handful of people over the age of 100 in the world, you are not one of them.'),
                )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'birth_date': getattr(self, 'birth_date', None),
        }



###########################################
# TIMESHEET
###########################################

class Timesheet(BaseModel):
# Defines a month, year and activated status for a user

    """Timesheet model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    month = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(12),
        ]
    )
    # Urgent update in 2999
    year = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(2000),
            validators.MaxValueValidator(3000),
        ]
    )
    closed = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'year', 'month'),)

    def __str__(self):
        """Return a string representation."""
        return '%02d-%04d [%s]' % (self.month, self.year, self.user)



###########################################
# LEAVE
###########################################

class Attachment(BaseModel):
# Defines the class that holds attachments and binds them to a user

    """Attachment model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    label = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField()
    slug = models.SlugField(default=uuid.uuid4, editable=False)

    def __str__(self):
        """Return a string representation."""
        if self.file:
            return '%s (%s - %s) [%s]' % (self.label, self.file.name, humanize.naturalsize(self.file.size), self.user)
        return '- [%s]' % self.user

    def get_file_url(self):
        """Get a URL to the file."""
        return reverse('download_attachment_service', kwargs={'slug': self.slug})


class Holiday(BaseModel):
# Defines the national holidays per country

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
# Defines the type of leave (vacation, sickness etc.)

    """Leave type model."""

    label = models.CharField(unique=True, max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class Leave(BaseModel):
# Defines the information for the leave and binds to the user and type of leave

    """Leave model."""

    STATUS = Choices(
        ('DRAFT', _('Draft')),
        ('PENDING', _('Pending')),
        ('APPROVED', _('Approved')),
        ('REJECTED', _('Rejected')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    description = models.TextField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS, default=STATUS.DRAFT)
    attachments = models.ManyToManyField(Attachment, blank=True)

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.leave_type, self.user)


class LeaveDate(BaseModel):
# Binds the leave, the time and the timesheet 

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
                # Verify timesheet this leave date is linked to is for the correct month/year
                if (starts_at.year != timesheet.year) or (starts_at.month != timesheet.month):
                    raise ValidationError(
                        _('You cannot attach leave dates to a timesheet for a different month')
                    )

        if timesheet:
            # Verify timesheet this leave date is attached to isn't closed
            if timesheet.closed:
                raise ValidationError(
                    _('You cannot attach leave dates to a closed timesheet'),
                )

            if leave:
                # Verify linked timesheet and leave are for the same user
                if leave.user != timesheet.user:
                    raise ValidationError(
                        _('You cannot attach leave dates to leaves and timesheets for different users')
                    )

    def get_validation_args(self):
        """Get a dict used for validation based on this instance."""
        return {
            'timesheet': getattr(self, 'timesheet', None),
            'starts_at': getattr(self, 'starts_at', None),
            'ends_at': getattr(self, 'ends_at', None),
            'leave': getattr(self, 'leave', None),
        }



###########################################
# CONTRACTS
###########################################

class PerformanceType(BaseModel):
# Defines the type of Performance, how the activity hours should be calculated

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


class ContractGroup(BaseModel):
# Holds the names for tags/groups that are linked to contracts

    """Project group model."""

    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        """Return a string representation."""
        return self.label


class Contract(BaseModel):
# Defines the basic Contract, Binds customer and company and performance_types and contract_groups

    """Contract model."""

    def company_choices():
        return {'internal': True}

    label = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    customer = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customercontact_set')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    active = models.BooleanField(default=True)
    performance_types = models.ManyToManyField(PerformanceType, blank=True)
    contract_groups = models.ManyToManyField(ContractGroup, blank=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.label, self.company, self.customer)


class ProjectContract(Contract):
# Defines the contract for Project

    """Project contract model."""

    fixed_fee = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999999),
        ]
    )
    starts_at = models.DateField()
    ends_at = models.DateField()

    #To get the contractlabel as a var, doesn't save in model
    label = Contract.label

    def __str__(self):
        """Return a string representation."""
        return 'Project: %s' % (self.label)


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


class ConsultancyContract(Contract):
# Defines the contract for Consultancy

    """Consultancy contract model."""

    starts_at = models.DateField()
    ends_at = models.DateField(blank=True, null=True)
    duration = models.DecimalField(
        blank=True,
        null=True,
        max_digits=6,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999),     
        ]
    )
    day_rate = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999),
        ]
    )

    #To get the contractlabel as a var
    label = Contract.label

    def __str__(self):
        """Return a string representation."""
        return 'Consultancy: %s' % (self.label)

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
# Defines the contract for Support

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

    #To get the contractlabel as a var
    label = Contract.label

    def __str__(self):
        """Return a string representation."""
        return 'Support: %s' % (self.label)

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
# Defines the roles per contract

    """Contract role model (!no pun intended)."""

    label = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.label


class ContractUser(BaseModel):
# Binds the user to a contract and role

    """Contract user model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'contract', 'contract_role'),)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.contract_role)


class ProjectEstimate(BaseModel):
# Binds Role and Project to an estimation and actual

    """Project estimate model."""

    role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)
    project = models.ForeignKey(ProjectContract, on_delete=models.PROTECT)
    hours_estimated = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999999),
        ]
    )

    def __str__(self):
        """Return a string representation"""
        return '%s [Est: %s]' % (self.role.label, self.hours_estimated)



###########################################
# PERFORMANCE
###########################################

class Performance(BaseModel):
# Binds a day to a timesheet

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
# Uses basic Performance to bind a duration & description to a contract

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
# Uses basic Performance to note the user was on standby

    """Standby (oncall) performance model."""

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (_('Standby'), super().__str__())
