import random
import factory
from faker import Faker
from django.contrib.auth import models as auth_models
from ninetofiver import models


fake = Faker()


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = auth_models.User

    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    is_staff = False


class AdminFactory(UserFactory):
    is_staff = True


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.Company

    label = factory.LazyFunction(fake.company)
    vat_identification_number = factory.LazyFunction(lambda: '%s%s' % (fake.language_code(), fake.md5()[:10]))
    internal = factory.LazyFunction(fake.boolean)
    address = factory.LazyFunction(fake.address)


class EmploymentContractFactory(factory.DjangoModelFactory):
    class Meta:
        model = models.EmploymentContract

    legal_country = factory.LazyFunction(fake.country_code)
    started_at = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    ended_at = factory.LazyFunction(lambda: fake.date_time_this_decade(after_now=True))


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
    birth_date = factory.LazyFunction(lambda: fake.date_time_this_decade(before_now=True))
    gender = factory.LazyFunction(lambda: fake.simple_profile(sex=None)['sex'])
    relation = factory.LazyFunction(fake.word)
