import random
import factory
from faker import Faker
from django.core.files.base import ContentFile
from django.contrib.auth import models as auth_models
from django.utils.timezone import utc
from ninetofiver import models


fake = Faker()


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = auth_models.User

    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    username = factory.LazyFunction(fake.name)
    email = factory.LazyFunction(fake.name)
    is_staff = False
    is_superuser = False


class UserInfoFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.UserInfo

    birth_date = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    gender = factory.LazyFunction(lambda: fake.simple_profile(sex=None)['sex'])
    country = factory.LazyFunction(fake.country_code)


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Company

    vat_identification_number = factory.LazyFunction(
        lambda: '%s%s' % (fake.language_code(), fake.md5()[:10])
    )
    name = factory.LazyFunction(fake.company)
    address = factory.LazyFunction(fake.address)
    country = factory.LazyFunction(fake.country_code)
    internal = factory.LazyFunction(fake.boolean)


class InternalCompanyFactory(CompanyFactory):
    internal = True


class EmploymentContractTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EmploymentContractType

    label = factory.LazyFunction(fake.word)


class EmploymentContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EmploymentContract

    started_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ended_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=False, after_now=True))


class WorkScheduleFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.WorkSchedule

    label = factory.LazyFunction(fake.word)
    monday = factory.LazyFunction(lambda: random.randint(0, 24))
    tuesday = factory.LazyFunction(lambda: random.randint(0, 24))
    wednesday = factory.LazyFunction(lambda: random.randint(0, 24))
    thursday = factory.LazyFunction(lambda: random.randint(0, 24))
    friday = factory.LazyFunction(lambda: random.randint(0, 24))
    saturday = factory.LazyFunction(lambda: random.randint(0, 24))
    sunday = factory.LazyFunction(lambda: random.randint(0, 24))


class UserRelativeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.UserRelative

    name = factory.LazyFunction(fake.name)
    birth_date = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True).date())
    gender = factory.LazyFunction(lambda: fake.simple_profile(sex=None)['sex'])
    relation = factory.LazyFunction(fake.word)


class AttachmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Attachment

    label = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    file = factory.LazyFunction(lambda: ContentFile(fake.text(max_nb_chars=200)))


class HolidayFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Holiday

    name = factory.LazyFunction(fake.word)
    date = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    country = factory.LazyFunction(fake.country_code)


class LeaveTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.LeaveType

    label = factory.LazyFunction(fake.word)


class LeaveFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Leave

    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class LeaveDateFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.LeaveDate

    starts_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-1h', end_date='now', tzinfo=utc))
    ends_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='now', end_date='+1h', tzinfo=utc))


class PerformanceTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.PerformanceType

    label = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    multiplier = factory.LazyFunction(lambda: random.randint(0, 3))


class ContractGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractGroup

    label = factory.LazyFunction(fake.word)


class ContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Contract

    label = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    active = factory.LazyFunction(fake.boolean)


class ProjectContractFactory(ContractFactory):
    class Meta:
        model = models.ProjectContract

    fixed_fee = factory.LazyFunction(lambda: random.randint(0, 9999))
    starts_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ends_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=False, after_now=True))


class ProjectEstimateFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ProjectEstimate

    hours_estimated = factory.LazyFunction(lambda: random.randint(0, 9999))


class ConsultancyContractFactory(ContractFactory):
    class Meta:
        model = models.ConsultancyContract

    starts_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ends_at = None
    duration = factory.LazyFunction(lambda: random.randint(0, 9999))
    day_rate = factory.LazyFunction(lambda: random.randint(0, 9999))


class SupportContractFactory(ContractFactory):
    class Meta:
        model = models.SupportContract

    starts_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ends_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=False, after_now=True))
    day_rate = factory.LazyFunction(lambda: random.randint(0, 9999))


class ContractRoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractRole

    label = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class ContractUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractUser


class TimesheetFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Timesheet

    month = factory.LazyFunction(lambda: random.randint(1, 12))
    year = factory.LazyFunction(lambda: random.randint(2000, 3000))


class OpenTimesheetFactory(TimesheetFactory):
    status= models.Timesheet.STATUS.ACTIVE


class WhereaboutFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Whereabout

    day = factory.LazyFunction(lambda: random.randint(1, 27))
    location = factory.LazyFunction(fake.city)


class PerformanceFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Performance

    day = factory.LazyFunction(lambda: random.randint(1, 27))
    redmine_id = factory.LazyFunction(lambda: random.randint(0, 3000))


class ActivityPerformanceFactory(PerformanceFactory):
    class Meta:
        model = models.ActivityPerformance

    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    duration = factory.LazyFunction(lambda: random.randint(1, 24))


class StandbyPerformanceFactory(PerformanceFactory):
    class Meta:
        model = models.StandbyPerformance
