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
    username = factory.Sequence(lambda n: 'UserName%d' % n)
    email = factory.LazyFunction(fake.name)
    is_staff = False
    is_superuser = False


class AdminFactory(UserFactory):
    is_staff = True
    is_superuser = True


class GroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = auth_models.Group

    name = factory.Sequence(lambda n: 'Group%d' % n)


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Company

    vat_identification_number = factory.LazyFunction(
        lambda: '%s%s' % (fake.language_code(), fake.md5()[:10])
    )
    name = factory.Sequence(lambda n: 'CompanyName%d' % n)
    address = factory.LazyFunction(fake.address)
    country = factory.LazyFunction(fake.country_code)
    internal = factory.LazyFunction(fake.boolean)


class InternalCompanyFactory(CompanyFactory):
    internal = True


class EmploymentContractTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EmploymentContractType

    name = factory.Sequence(lambda n: 'EmploymentContractType%d' % n)


class EmploymentContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EmploymentContract

    started_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ended_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=False, after_now=True))


class WorkScheduleFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.WorkSchedule

    name = factory.Sequence(lambda n: 'WorkSchedule%d' % n)
    monday = factory.LazyFunction(lambda: random.randint(0, 10))
    tuesday = factory.LazyFunction(lambda: random.randint(0, 10))
    wednesday = factory.LazyFunction(lambda: random.randint(0, 10))
    thursday = factory.LazyFunction(lambda: random.randint(0, 10))
    friday = factory.LazyFunction(lambda: random.randint(0, 10))
    saturday = factory.LazyFunction(lambda: random.randint(0, 10))
    sunday = factory.LazyFunction(lambda: random.randint(0, 10))


class UserInfoFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.UserInfo

    birth_date = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True).date())
    gender = factory.LazyFunction(lambda: fake.simple_profile(sex=None)['sex'])
    country = factory.LazyFunction(fake.country_code)


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

    name = factory.LazyFunction(fake.word)
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

    name = factory.Sequence(lambda n: 'LeaveType%d' % n)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class LocationFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Location

    name = factory.Sequence(lambda n: 'Location%d' % n)


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

    name = factory.Sequence(lambda n: 'PerformanceType%d' % n)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    multiplier = factory.LazyFunction(lambda: random.randint(0, 3))


class ContractGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractGroup

    name = factory.Sequence(lambda n: 'ContractGroup%d' % n)


class ContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Contract

    name = factory.LazyFunction(fake.word)
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    active = factory.LazyFunction(fake.boolean)
    starts_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ends_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=False, after_now=True))
    company = factory.SubFactory(InternalCompanyFactory)
    customer = factory.SubFactory(CompanyFactory)


class ProjectContractFactory(ContractFactory):
    class Meta:
        model = models.ProjectContract

    fixed_fee = factory.LazyFunction(lambda: random.randint(0, 9999))


class ConsultancyContractFactory(ContractFactory):
    class Meta:
        model = models.ConsultancyContract

    duration = factory.LazyFunction(lambda: random.randint(0, 9999))
    day_rate = factory.LazyFunction(lambda: random.randint(0, 9999))


class SupportContractFactory(ContractFactory):
    class Meta:
        model = models.SupportContract

    day_rate = factory.LazyFunction(lambda: random.randint(0, 9999))


class ContractRoleFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractRole

    name = factory.Sequence(lambda n: 'ContractRole%d%s' % (n, fake.text(max_nb_chars=200)))
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))


class ContractUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractUser

    contract_role = factory.SubFactory(ContractRoleFactory)


class ContractUserGroupFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.ContractUserGroup


class TimesheetFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Timesheet

    month = factory.LazyFunction(lambda: random.randint(1, 12))
    year = factory.LazyFunction(lambda: random.randint(2000, 3000))


class OpenTimesheetFactory(TimesheetFactory):
    status = models.STATUS_ACTIVE


class WhereaboutFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Whereabout

    starts_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='-1h', end_date='now', tzinfo=utc))
    ends_at = factory.LazyFunction(lambda: fake.date_time_between(start_date='now', end_date='+1h', tzinfo=utc))
    location = factory.SubFactory(LocationFactory)
    timesheet = factory.SubFactory(OpenTimesheetFactory)


class PerformanceFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Performance

    date = factory.LazyFunction(lambda: fake.date_time_this_decade().date())
    redmine_id = factory.LazyFunction(lambda: random.randint(0, 3000))


class ActivityPerformanceFactory(PerformanceFactory):
    class Meta:
        model = models.ActivityPerformance

    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    duration = factory.LazyFunction(lambda: random.randint(1, 24))
    contract_role = ContractRoleFactory


class StandbyPerformanceFactory(PerformanceFactory):
    class Meta:
        model = models.StandbyPerformance
