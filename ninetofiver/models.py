"""Models."""
import humanize
import uuid
import logging
from datetime import datetime, date
from decimal import Decimal
from django.contrib.auth import models as auth_models
from django.core import validators
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext as _
from django_countries.fields import CountryField
from model_utils import Choices
from polymorphic.models import PolymorphicManager
from polymorphic.models import PolymorphicModel
from dirtyfields import DirtyFieldsMixin
from ninetofiver.utils import days_in_month


log = logging.getLogger(__name__)


# Monkey patch user model to serialize properly
def user_str(self):
    if self.get_full_name():
        return '%s' % (self.get_full_name())
    return self.username


auth_models.User.__str__ = user_str

# Define ordering of the User
auth_models.User._meta.ordering = ['first_name', 'last_name']


# Genders
GENDER_MALE = 'm'
GENDER_FEMALE = 'f'

# Statuses
STATUS_DRAFT = 'draft'
STATUS_ACTIVE = 'active'
STATUS_PENDING = 'pending'
STATUS_CLOSED = 'closed'
STATUS_APPROVED = 'approved'
STATUS_REJECTED = 'rejected'

# Periods
PERIOD_DAILY = 'daily'
PERIOD_WEEKLY = 'weekly'
PERIOD_MONTHLY = 'monthly'
PERIOD_YEARLY = 'yearly'


class BaseManager(PolymorphicManager):
    """Base manager."""


class BaseModel(DirtyFieldsMixin, PolymorphicModel):
    """Abstract base model."""

    objects = BaseManager()

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        pass

    def validate_unique(self, *args, **kwargs):
        """Validate whether the object is unique."""
        super().validate_unique(*args, **kwargs)
        self.perform_additional_validation()

    def get_absolute_url(self):
        """Get an absolute URL for the object."""
        from django.urls import reverse
        # return reverse('%s-detail' % self.__class__._meta.verbose_name.replace(' ', ''), args=[str(self.id)])
        return reverse('%s-detail' % self.__class__.__name__.lower(), args=[str(self.id)])

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Abstract meta class."""

        abstract = True
        ordering = ['id']
        base_manager_name = 'base_objects'


class Company(BaseModel):
    """
    Company model.

    Contracts are made between internal and internal/external companies.

    """

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
    logo_url = models.CharField(max_length=255, blank=True, null=True)

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        """Return a string representation."""
        # return '%s [%s]' % (self.name, self.vat_identification_number)
        return self.name


class WorkSchedule(BaseModel):

    """
    Work schedule model.

    Defines the schedule a user works at.

    """

    name = models.CharField(unique=True, max_length=255)
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
        return self.name


class EmploymentContractType(BaseModel):

    """Employment contract type model."""

    name = models.CharField(unique=True, max_length=255)

    class Meta(BaseModel.Meta):
        ordering = ['name']

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.name


class EmploymentContract(BaseModel):

    """Employment contract model."""

    def company_choices():
        return {'internal': True}

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    employment_contract_type = models.ForeignKey(EmploymentContractType, on_delete=models.PROTECT)
    work_schedule = models.ForeignKey(WorkSchedule, on_delete=models.CASCADE)
    started_at = models.DateField()
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s, %s]' % (self.user, self.company, self.employment_contract_type)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.ended_at and self.started_at:
            # Verify whether the end date of the employment contract comes after the start date
            if self.ended_at < self.started_at:
                raise ValidationError({'ended_at': _('The end date should come before the start date.')})

        # User should work for an internal company
        if not self.company.internal:
            raise ValidationError({'company': _('Employment contracts can only be created for internal companies.')})

        # Verify user doesn't have an active employment contract for the same company/period
        existing = None
        if self.ended_at:
            existing = self.__class__.objects.filter(
                models.Q(user=self.user, company=self.company) &
                (
                    models.Q(ended_at__isnull=True, started_at__lte=self.ended_at) |
                    models.Q(ended_at__isnull=False, started_at__lte=self.ended_at, ended_at__gte=self.started_at)
                )
            )
        else:
            existing = self.__class__.objects.filter(
                models.Q(user=self.user, company=self.company) &
                (
                    models.Q(ended_at__isnull=True) |
                    models.Q(ended_at__isnull=False, started_at__lte=self.started_at, ended_at__gte=self.started_at)
                )
            )

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'user': _('The selected user already has an active employment contract.')})


class UserRelative(BaseModel):

    """User relative model."""

    GENDER_CHOICES = Choices(
        (GENDER_MALE, _('Male')),
        (GENDER_FEMALE, _('Female')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    birth_date = models.DateField()
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES)
    relation = models.CharField(max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.name, self.relation, self.user)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.birth_date > datetime.now().date():
            raise ValidationError({'birth_date': _('A birth date should not be set in the future')})

        if self.birth_date.year < (datetime.now().year - 110):
            raise ValidationError({'birth_date': _('The selected birth date is likely incorrect.')})


class UserInfo(BaseModel):

    """User info model."""

    GENDER_CHOICES = Choices(
        (GENDER_MALE, _('Male')),
        (GENDER_FEMALE, _('Female')),
    )

    user = models.OneToOneField(auth_models.User, on_delete=models.CASCADE)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=2, choices=GENDER_CHOICES, null=True, blank=True)
    country = CountryField(null=True, blank=True)
    redmine_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.user

    def get_join_date(self):
        """Returns the date of the first employmentcontract for this user."""
        try:
            return EmploymentContract.objects.filter(user=self.user).earliest('started_at').started_at
        except BaseException:
            return date.today()

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.birth_date > datetime.now().date():
            raise ValidationError({'birth_date': _('A birth date should not be set in the future')})

        if self.birth_date.year < (datetime.now().year - 110):
            raise ValidationError({'birth_date': _('The selected birth date is likely incorrect.')})

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'user info'


class Timesheet(BaseModel):

    """Timesheet model."""

    STATUS_CHOICES = Choices(
        (STATUS_CLOSED, _('Closed')),
        (STATUS_ACTIVE, _('Active')),
        (STATUS_PENDING, _('Pending')),
    )

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
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_ACTIVE)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'year', 'month'),)

    def __str__(self):
        """Return a string representation."""
        return '%02d-%04d [%s]' % (self.month, self.year, self.user)


class Attachment(BaseModel):

    """Attachment model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField()
    slug = models.SlugField(default=uuid.uuid4, editable=False)

    def __str__(self):
        """Return a string representation."""
        if self.file:
            return '%s (%s - %s) [%s]' % (self.name, self.file.name, humanize.naturalsize(self.file.size), self.user)
        return '- [%s]' % self.user

    def get_file_url(self):
        """Get a URL to the file."""
        return reverse('download_attachment_service', kwargs={'slug': self.slug})


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

    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.name


class Leave(BaseModel):

    """Leave model."""

    STATUS_CHOICES = Choices(
        (STATUS_DRAFT, _('Draft')),
        (STATUS_PENDING, _('Pending')),
        (STATUS_APPROVED, _('Approved')),
        (STATUS_REJECTED, _('Rejected')),
    )

    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    description = models.TextField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    attachments = models.ManyToManyField(Attachment, blank=True)

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

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        # Verify whether the start datetime of the leave date comes before the end datetime
        if self.starts_at >= self.ends_at:
            raise ValidationError({'starts_at': _('The start date should be set before the end date')})

        # Verify whether start and end datetime of the leave date occur on the same date
        if self.starts_at.date() != self.ends_at.date():
            raise ValidationError({'starts_at': _('The start date should occur on the same day as the end date')})

        # Check whether the user already has leave planned during this time frame
        existing = self.__class__.objects.filter(
            models.Q(leave__user=self.leave.user) &
            models.Q(starts_at__lte=self.ends_at, ends_at__gte=self.starts_at)
        )

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'user': _('User already has leave planned during this time')})

        # Verify timesheet this leave date is linked to is for the correct month/year
        if (self.starts_at.year != self.timesheet.year) or (self.starts_at.month != self.timesheet.month):
            raise ValidationError({'timesheet':
                                  _('You cannot attach leave dates to a timesheet for a different month')})

        # Verify timesheet this leave date is attached to isn't closed
        if self.timesheet.status != STATUS_ACTIVE:
            raise ValidationError({'timesheet': _('You can only add leave dates to active timesheets.')})

        # Verify linked timesheet and leave are for the same user
        if self.leave.user != self.timesheet.user:
            raise ValidationError({'leave':
                                  _('You cannot attach leave dates to leaves and timesheets for different users')})

        # # Verify linked leave is in draft mode
        # @TODO Re-enable this, but since leave dates are saved after leaves when using inlines in the admin interface,
        #       we can't ever approve/reject leaves if we do not comment this out
        # if self.leave.status not in [STATUS_DRAFT, STATUS_PENDING]:
        #     raise ValidationError({'leave': _('You can only add leave dates to draft leaves.')})


class PerformanceType(BaseModel):

    """Performance type model."""

    name = models.CharField(unique=True, max_length=255)
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
        return '%s [%s%%]' % (self.name, int(self.multiplier * 100))


class ContractGroup(BaseModel):

    """Contract group model."""

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        """Return a string representation."""
        return self.name


class Contract(BaseModel):

    """Contract model."""

    def company_choices():
        return {'internal': True}

    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    customer = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='customercontact_set')
    company = models.ForeignKey(Company, on_delete=models.PROTECT, limit_choices_to=company_choices)
    starts_at = models.DateField()
    ends_at = models.DateField(blank=True, null=True)
    active = models.BooleanField(default=True)
    performance_types = models.ManyToManyField(PerformanceType, blank=True)
    contract_groups = models.ManyToManyField(ContractGroup, blank=True)
    attachments = models.ManyToManyField(Attachment, blank=True)
    redmine_id = models.CharField(max_length=255, blank=True, null=True)
    external_only = models.BooleanField(default=False)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.name, self.company, self.customer)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.ends_at:
            # Verify whether the start date of the contract comes before the end date
            if self.starts_at >= self.ends_at:
                raise ValidationError({'ends_at': _('The start date should be set before the end date')})


class ProjectContract(Contract):

    """Project contract model."""

    fixed_fee = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999999),
        ]
    )

    def __str__(self):
        """Return a string representation."""
        return '%s: %s' % (_('Project'), self.name)


class ConsultancyContract(Contract):

    """Consultancy contract model."""

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

    def __str__(self):
        """Return a string representation."""
        return '%s: %s' % (_('Consultancy'), self.name)


class SupportContract(Contract):

    """Support contract model."""

    FIXED_FEE_PERIOD_CHOICES = Choices(
        (PERIOD_DAILY, _('Daily')),
        (PERIOD_WEEKLY, _('Weekly')),
        (PERIOD_MONTHLY, _('Monthly')),
        (PERIOD_YEARLY, _('Yearly')),
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
    fixed_fee_period = models.CharField(blank=True, null=True, max_length=10, choices=FIXED_FEE_PERIOD_CHOICES)

    def __str__(self):
        """Return a string representation."""
        return '%s: %s' % (_('Support'), self.name)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.fixed_fee_period and not self.fixed_fee:
            raise ValidationError({'fixed_fee': _('A contract with a fixed fee period requires a fixed fee')})


class ContractRole(BaseModel):

    """Contract role model."""

    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.name


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


class ProjectEstimate(BaseModel):

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
        return '%s [Est: %s]' % (self.role.name, self.hours_estimated)


class Whereabout(BaseModel):

    """Whereabout model."""

    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    day = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(31),
        ]
    )
    location = models.CharField(max_length=255)

    def __str__(self):
        """Retrun a string representation"""
        return '%s (%s - %s)' % (self.location, self.day, self.timesheet)

    def perform_additional_validation(self):
        """Perform additional validation on the object"""
        super().perform_additional_validation()

        if self.timesheet.status != STATUS_ACTIVE:
            raise ValidationError({'timesheet': _('Whereabouts can only be attached to active timesheets.')})

        month_days = days_in_month(self.timesheet.year, self.timesheet.month)

        if self.day > month_days:
            raise ValidationError({'day': _('There are not that many days in the month this timesheet is attached to.'
                                            % month_days)})


class Performance(BaseModel):

    """Performance model."""

    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    day = models.PositiveSmallIntegerField(
        validators=[
            validators.MinValueValidator(1),
            validators.MaxValueValidator(31),
        ]
    )
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, null=True)
    redmine_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s-%s' % (self.day, self.timesheet)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.timesheet.status != STATUS_ACTIVE:
            raise ValidationError({'timesheet': _('Performances can only be attached to active timesheets.')})

        # Verify whether the day is valid for the month/year of the timesheet
        month_days = days_in_month(self.timesheet.year, self.timesheet.month)

        if self.day > month_days:
            raise ValidationError({'day': _('There are not that many days in the month this timesheet is attached to.'
                                            % month_days)})


class ActivityPerformance(Performance):

    """Activity performance model."""

    performance_type = models.ForeignKey(PerformanceType, on_delete=models.PROTECT)
    contract_role = models.ForeignKey(ContractRole, null=True, on_delete=models.PROTECT)
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

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.contract and self.contract_role:
            # Ensure the contract role is valid for the contract and contract_user
            allowed = ContractUser.objects.filter(contract=self.contract, user=self.timesheet.user,
                                                  contract_role=self.contract_role).count()
            if not allowed:
                raise ValidationError({'contract_role':
                                      _('The selected contract role is not valid for that user on that contract.')})

        if self.contract:
            # Ensure the performance type is valid for the contract
            allowed_types = list(self.contract.performance_types.all())

            if allowed_types and (self.performance_type not in allowed_types):
                raise ValidationError({'performance_type':
                                      _('The selected performance type is not valid for the selected contract')})


class StandbyPerformance(Performance):

    """Standby (oncall) performance model."""

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (_('Standby'), super().__str__())

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        # Check whether the user already has a standby planned during this time frame
        existing = self.__class__.objects.filter(contract=self.contract, timesheet=self.timesheet, day=self.day)

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'day':
                                  _('The standby performance is already linked to that contract for that day.')})

        if self.contract:
            # Ensure that contract is a support contract
            if not isinstance(self.contract, SupportContract):
                raise ValidationError({'contract':
                                      _('Standy performances can only be created for support contracts.')})
