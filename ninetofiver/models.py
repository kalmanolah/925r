"""Models."""
import humanize
import uuid
import logging
import datetime
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
from dateutil.relativedelta import relativedelta
from phonenumber_field.modelfields import PhoneNumberField
from adminsortable.models import SortableMixin
from ninetofiver.utils import days_in_month


log = logging.getLogger(__name__)


# Monkey patch user model to serialize properly
def user_str(self):
    """Get a string representation for the given user."""
    if self.get_full_name():
        return '%s' % (self.get_full_name())
    return self.username


auth_models.User.__str__ = user_str

# Define ordering of the User
user_ordering = ['first_name', 'last_name']
auth_models.User.Meta.ordering = user_ordering
auth_models.User._meta.ordering = user_ordering


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

# Permissions
PERMISSION_RECEIVE_PENDING_LEAVE_REMINDER = 'receive_pending_leave_reminder'
PERMISSION_RECEIVE_MODIFIED_ATTACHMENT_NOTIFICATION = 'receive_modified_attachment_notification'


class BaseManager(PolymorphicManager):
    """Base manager."""


class BaseModel(DirtyFieldsMixin, PolymorphicModel):
    """Abstract base model."""

    objects = BaseManager()

    def save(self, validate=True, **kwargs):
        """Save the object."""
        if validate:
            self.perform_additional_validation()

        super().save(**kwargs)

    def delete(self, validate=True, **kwargs):
        """Delete the object."""
        if validate:
            self.perform_additional_validation()

        super().delete(**kwargs)

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
        return reverse(self.get_absolute_url_view_name(), args=[str(self.id)])

    def get_absolute_url_view_name(self, cls=None):
        """Get the view name used for generating an absolute URL."""
        cls = cls if cls else self.__class__
        return 'ninetofiver_api_v2:%s-detail' % cls.__name__.lower()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Abstract meta class."""

        abstract = True
        ordering = ['id']
        base_manager_name = 'base_objects'


class ApiKey(BaseModel):
    """
    API key model.

    API keys provide simpler (read-only) access to the API.
    This is useful when a user wants to add iCal feeds to other applications
    without giving up their credentials, for example.
    For complex operations or full-fledged clients, OAuth2 is still the recommended
    authentication method.

    """

    def generate_key():
        """Generate a key."""
        return str(uuid.uuid4()).replace('-', '')

    key = models.CharField(db_index=True, max_length=32, default=generate_key, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(auth_models.User, on_delete=models.CASCADE)
    read_only = models.BooleanField(default=True)

    def __str__(self):
        """Return a string representation."""
        return '%s - %s... [%s]' % (self.name,
                                    self.key[:12] if self.key else 'New API key', 'RO' if self.read_only else 'RW')


class Company(BaseModel):
    """
    Company model.

    Contracts are made between internal and internal/external companies.

    """

    def generate_file_path(instance, filename):
        """Generate a file path."""
        return 'companies/company_%s/%s' % (instance.id, filename)

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
    logo = models.FileField(upload_to=generate_file_path, blank=True, null=True)

    class Meta(BaseModel.Meta):
        verbose_name_plural = 'companies'
        ordering = ['name']

    def __str__(self):
        """Return a string representation."""
        # return '%s [%s]' % (self.name, self.vat_identification_number)
        return self.name

    def get_logo_url(self):
        """Get a URL to the logo."""
        return reverse('ninetofiver_api_v2:download_company_logo', kwargs={'pk': self.pk})


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
    birth_date = models.DateField(blank=True, null=True)
    gender = models.CharField(null=True, blank=True, max_length=2, choices=GENDER_CHOICES)
    relation = models.CharField(max_length=255)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s → %s]' % (self.name, self.relation, self.user)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.birth_date:
            if self.birth_date > datetime.datetime.now().date():
                raise ValidationError({'birth_date': _('A birth date should not be set in the future')})

        if self.birth_date:
            if self.birth_date.year < (datetime.datetime.now().year - 110):
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
    phone_number = PhoneNumberField(blank=True)
    redmine_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.user

    def get_join_date(self):
        """Return the date of the first employmentcontract for this user."""
        try:
            return EmploymentContract.objects.filter(user=self.user).earliest('started_at').started_at
        except BaseException:
            return datetime.date.today()

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.birth_date:
            if self.birth_date > datetime.datetime.now().date():
                raise ValidationError({'birth_date': _('A birth date should not be set in the future')})

            if self.birth_date.year < (datetime.datetime.now().year - 110):
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
    attachments = models.ManyToManyField('Attachment', blank=True)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'year', 'month'),)

    def __str__(self):
        """Return a string representation."""
        return '%02d-%04d [%s]' % (self.month, self.year, self.user)

    def get_date_range(self):
        """Get the date range for this timesheet."""
        from_date = datetime.date.today().replace(year=self.year, month=self.month, day=1)
        until_date = from_date.replace() + relativedelta(months=1) - relativedelta(days=1)
        return [from_date, until_date]

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        # New timesheet creation
        if not self.pk:
            if self.status != STATUS_ACTIVE:
                raise ValidationError({'status': _('Timesheets must be set to active when created.')})

            existing = self.__class__.objects.filter(user=self.user, year=self.year, month=self.month).count()
            if existing:
                raise ValidationError({'year': _('A timesheet for this user, year and month already exists.')})

        dirty = self.get_dirty_fields()
        old_status = dirty.get('status', None)

        # Deal with status changes
        if old_status and (old_status != self.status):
            if (old_status == STATUS_ACTIVE) and (self.status != STATUS_PENDING):
                raise ValidationError({'status': _('Active timesheets can only be made pending.')})
            elif (old_status == STATUS_PENDING) and (self.status not in [STATUS_CLOSED, STATUS_ACTIVE]):
                raise ValidationError({'status': _('Pending timesheets can only be closed, reactivated.')})


class Attachment(BaseModel):

    """Attachment model."""

    def generate_file_path(instance, filename):
        """Generate a file path."""
        return 'attachments/user_%s/%s/%s' % (instance.user.id, instance.slug, filename)

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    name = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    file = models.FileField(upload_to=generate_file_path)
    slug = models.SlugField(default=uuid.uuid4, editable=False)

    class Meta(BaseModel.Meta):
        permissions = (
            (PERMISSION_RECEIVE_MODIFIED_ATTACHMENT_NOTIFICATION, "Can receive modified attachment notifications"),
        )

    def __str__(self):
        """Return a string representation."""
        if self.file:
            return '%s (%s - %s) [%s]' % (self.name, self.file.name.split('.')[-1].upper(),
                                          humanize.naturalsize(self.file.size), self.user)
        return '- [%s]' % self.user

    def get_file_url(self):
        """Get a URL to the file."""
        return reverse('ninetofiver_api_v2:download_attachment', kwargs={'slug': self.slug})


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


class LeaveType(SortableMixin, BaseModel):

    """Leave type model."""

    name = models.CharField(unique=True, max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)
    overtime = models.BooleanField(default=False)
    sickness = models.BooleanField(default=False)

    class Meta(BaseModel.Meta):
        ordering = ['order']

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

    class Meta(BaseModel.Meta):
        permissions = (
            (PERMISSION_RECEIVE_PENDING_LEAVE_REMINDER, "Can receive pending leave reminders"),
        )

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
        if self.starts_at.date() != self.ends_at.date():
            dt_format = '%a %d %B %Y %H:%M %Z'
            return '%s - %s' % (self.starts_at.strftime(dt_format), self.ends_at.strftime(dt_format))

        return '%s, %s - %s %s' % (self.starts_at.strftime('%a %d %B %Y'), self.starts_at.strftime('%H:%M'),
                                   self.ends_at.strftime('%H:%M'), self.starts_at.strftime('%Z'))

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
        existing = (self.__class__.objects
                    .exclude(leave__status=STATUS_REJECTED)
                    .filter(
                        models.Q(leave__user=self.leave.user) &
                        models.Q(starts_at__lte=self.ends_at, ends_at__gte=self.starts_at)
                    ))

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

    def requested_up_front(self):
        """Whether or not the leave date was requested up front."""
        return self.starts_at.date() > self.created_at.date()

    def html_label(self):
        """Get the HTML label for this leave date."""
        label = str(self)

        if not self.requested_up_front():
            label = '<span style="color:#f02311;font-weight:bold;" title="%s">(!)&nbsp;</span>%s' % (_('Not requested up front'), label)

        return label


class PerformanceType(BaseModel):

    """Performance type model."""

    name = models.CharField(max_length=255)
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

    class Meta(BaseModel.Meta):
        ordering = ['multiplier']

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
        return '[%s/%s] %s' % (self.get_real_instance_class().__name__[0], self.customer, self.name)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.ends_at:
            # Verify whether the start date of the contract comes before the end date
            if self.starts_at >= self.ends_at:
                raise ValidationError({'ends_at': _('The start date should be set before the end date')})

    def get_absolute_url_view_name(self):
        """Get the view name used for generating an absolute URL."""
        return super().get_absolute_url_view_name(Contract)


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
        ],
        verbose_name='Duration (hours)'
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


class ContractUserGroup(BaseModel):
    """Contract user group model."""

    group = models.ForeignKey(auth_models.Group, on_delete=models.CASCADE)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)

    class Meta(BaseModel.Meta):
        unique_together = (('group', 'contract', 'contract_role'),)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.group, self.contract_role)


class ContractUser(BaseModel):
    """Contract user model."""

    user = models.ForeignKey(auth_models.User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)
    contract_user_group = models.ForeignKey(ContractUserGroup, on_delete=models.CASCADE, editable=False, blank=True,
                                            null=True)

    class Meta(BaseModel.Meta):
        unique_together = (('user', 'contract', 'contract_role'),)

    def __str__(self):
        """Return a string representation."""
        return '%s [%s]' % (self.user, self.contract_role)


class ContractUserWorkSchedule(BaseModel):

    """
    Contract user work schedule model.

    Defines the schedule a user works at for a given contract, for a given date range.

    """

    contract_user = models.ForeignKey(ContractUser, on_delete=models.CASCADE)
    starts_at = models.DateField()
    ends_at = models.DateField(blank=True, null=True)
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
        return '%s - %s' % (self.contract_user, self.starts_at)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.ends_at and self.starts_at:
            # Verify whether the end date of the contract user work schedule comes after the start date
            if self.ends_at < self.starts_at:
                raise ValidationError({'ends_at': _('The end date should come before the start date.')})

        # Contract user work schedules can't overlap for the same contract user/period
        existing = None
        if self.ends_at:
            existing = self.__class__.objects.filter(
                models.Q(contract_user=self.contract_user) &
                (
                    models.Q(ends_at__isnull=True, starts_at__lte=self.ends_at) |
                    models.Q(ends_at__isnull=False, starts_at__lte=self.ends_at, ends_at__gte=self.starts_at)
                )
            )
        else:
            existing = self.__class__.objects.filter(
                models.Q(contract_user=self.contract_user) &
                (
                    models.Q(ends_at__isnull=True) |
                    models.Q(ends_at__isnull=False, starts_at__lte=self.starts_at, ends_at__gte=self.starts_at)
                )
            )

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'starts_at':
                                   _('The given contract user already has a work schedule for this period.')})


class ContractEstimate(BaseModel):

    """Contract estimate model."""

    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT, blank=True, null=True)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    duration = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        validators=[
            validators.MinValueValidator(0),
            validators.MaxValueValidator(9999999),
        ],
        verbose_name='Duration (hours)'
    )

    def __str__(self):
        """Return a string representation"""
        return '%s [Est: %s]' % (str(self.contract_role) if self.contract_role else '-', self.duration)

    class Meta(BaseModel.Meta):
        unique_together = (('contract', 'contract_role'),)


class Location(SortableMixin, BaseModel):

    """Location model."""

    name = models.CharField(unique=True, max_length=255)
    order = models.PositiveIntegerField(default=0, editable=False, db_index=True)

    class Meta(BaseModel.Meta):
        ordering = ['order']

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.name


class Whereabout(BaseModel):

    """Whereabout model."""

    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    description = models.TextField(max_length=255, blank=True, null=True)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (self.location, self.timesheet.user)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        # Verify whether the start datetime of the whereabout comes before the end datetime
        if self.starts_at >= self.ends_at:
            raise ValidationError({'starts_at': _('The start date should be set before the end date')})

        # Verify whether start and end datetime of the whereabout occur on the same date
        if self.starts_at.date() != self.ends_at.date():
            raise ValidationError({'starts_at': _('The start date should occur on the same day as the end date')})

        # Check whether the user already has a whereabout during this time frame
        existing = self.__class__.objects.filter(
            models.Q(timesheet__user=self.timesheet.user) &
            models.Q(starts_at__lt=self.ends_at, ends_at__gt=self.starts_at)
        )

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'user': _('User already has a whereabout during this time')})

        # Verify timesheet this whereabout is linked to is for the correct month/year
        if (self.starts_at.year != self.timesheet.year) or (self.starts_at.month != self.timesheet.month):
            raise ValidationError({'timesheet':
                                  _('You cannot attach whereabouts to a timesheet for a different month')})

        # Verify timesheet this whereabout is attached to isn't closed
        if self.timesheet.status != STATUS_ACTIVE:
            raise ValidationError({'timesheet': _('You can only add whereabouts to active timesheets.')})


class Performance(BaseModel):

    """Performance model."""

    timesheet = models.ForeignKey(Timesheet, on_delete=models.PROTECT)
    date = models.DateField()
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, null=True)
    redmine_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % (self.date,)

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        if self.timesheet.status != STATUS_ACTIVE:
            raise ValidationError({'timesheet': _('Performances can only be attached to active timesheets.')})

        # Verify whether the day is valid for the month/year of the timesheet
        if (self.date.month != self.timesheet.month) or (self.date.year != self.timesheet.year):
            raise ValidationError({'date': _('This date is not part of the given timesheet.')})

    def get_absolute_url_view_name(self):
        """Get the view name used for generating an absolute URL."""
        return super().get_absolute_url_view_name(Performance)


class ActivityPerformance(Performance):

    """Activity performance model."""

    performance_type = models.ForeignKey(PerformanceType, on_delete=models.PROTECT)
    contract_role = models.ForeignKey(ContractRole, on_delete=models.PROTECT)
    description = models.TextField(max_length=4096, blank=True, null=True)
    duration = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        validators=[
            validators.MinValueValidator(Decimal('0.01')),
            validators.MaxValueValidator(24),
        ],
        verbose_name='Duration (hours)'
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

    @property
    def normalized_duration(self):
        """Get the normalized duration, taking into account the performance type multiplier."""
        return round(self.duration * self.performance_type.multiplier, 2)


class StandbyPerformance(Performance):
    """Standby (oncall) performance model."""

    def __str__(self):
        """Return a string representation."""
        return '%s - %s' % (_('Standby'), super().__str__())

    def perform_additional_validation(self):
        """Perform additional validation on the object."""
        super().perform_additional_validation()

        # Check whether the user already has a standby planned during this time frame
        existing = self.__class__.objects.filter(contract=self.contract, timesheet=self.timesheet, date=self.date)

        if self.pk:
            existing = existing.exclude(id=self.pk)

        existing = existing.count()

        if existing:
            raise ValidationError({'date':
                                  _('The standby performance is already linked to that contract for that date.')})

        if self.contract:
            # Ensure that contract is a support contract
            if self.contract.get_real_instance_class() != SupportContract:
                raise ValidationError({'contract':
                                      _('Standy performances can only be created for support contracts.')})


class Invoice(BaseModel):
    """Invoice model."""

    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    period_starts_at = models.DateField(default=datetime.date.today)
    period_ends_at = models.DateField(default=datetime.date.today)
    date = models.DateField(default=datetime.date.today)
    reference = models.CharField(max_length=255)
    description = models.TextField(max_length=255, blank=True, null=True)

    def __str__(self):
        """Return a string representation."""
        return '%s' % self.reference


class InvoiceItem(BaseModel):
    """Invoice item."""

    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=0.00,
        validators=[
            validators.MinValueValidator(-9999999),
            validators.MaxValueValidator(9999999),
        ]
    )
    amount = models.PositiveIntegerField(default=1)
    description = models.TextField(max_length=255, blank=True, null=True)