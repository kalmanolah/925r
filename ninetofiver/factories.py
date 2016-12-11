import factory
from faker import Faker
from django.contrib.auth import models as auth_models


fake = Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = auth_models.User

    first_name = factory.LazyFunction(fake.first_name)
    last_name = factory.LazyFunction(fake.last_name)
    is_staff = False


class AdminFactory(UserFactory):
    is_staff = True
