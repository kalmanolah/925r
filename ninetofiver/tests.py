from rest_framework.test import APITestCase
from rest_assured import testcases
from ninetofiver import factories
from decimal import Decimal
import datetime


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = factories.UserFactory()
        self.client.force_authenticate(self.user)


class CompanyAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'company'
    factory_class = factories.CompanyFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Foo BVBA',
        'vat_identification_number': 'BE123123123123',
        'internal': False,
        'address': 'Essensteenweg 29, 2930 Brasschaat, België',
    }
    update_data = {
        'label': 'Foo sprl',
        'vat_identification_number': 'BE321321321321',
        'internal': True,
        'address': 'Essensteenweg 31, 2930 Brasschaat, België',
    }


class EmploymentContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'employmentcontract'
    factory_class = factories.EmploymentContractFactory
    user_factory = factories.UserFactory
    create_data = {
        'started_at': datetime.date(datetime.date.today().year + 10, 1, 15),
        'legal_country': 'BE',
    }
    update_data = {
        'started_at': datetime.date(datetime.date.today().year + 10, 1, 15),
        'ended_at': datetime.date(datetime.date.today().year + 10, 1, 16),
        'legal_country': 'BE',
    }

    def setUp(self):
        self.company = factories.CompanyFactory.create()
        self.work_schedule = factories.WorkScheduleFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user, company=self.company, work_schedule=self.work_schedule)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'user': self.user.id,
            'work_schedule': self.work_schedule.id,
        })

        return self.create_data


class WorkScheduleAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'workschedule'
    factory_class = factories.WorkScheduleFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Test schedule #1',
        'monday': Decimal('1.20'),
        'tuesday': Decimal('1.50'),
        'wednesday': Decimal('1.75'),
        'thursday': Decimal('0'),
        'friday': Decimal('2'),
        'saturday': Decimal('0'),
        'sunday': Decimal('0'),
    }
    update_data = {
        'label': 'Test schedule #2',
        'monday': Decimal('2.10'),
        'tuesday': Decimal('5.10'),
        'wednesday': Decimal('7.50'),
        'thursday': Decimal('0'),
        'friday': Decimal('4'),
        'saturday': Decimal('0'),
        'sunday': Decimal('3'),
    }


class UserRelativeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'userrelative'
    factory_class = factories.UserRelativeFactory
    user_factory = factories.UserFactory
    create_data = {
        'birth_date': datetime.date(datetime.date.today().year - 10, 1, 15),
        'name': 'John Doe',
        'gender': 'm',
        'relation': 'Dad',
    }
    update_data = {
        'birth_date': datetime.date(datetime.date.today().year - 10, 1, 15),
        'name': 'Jane Doe',
        'gender': 'f',
        'relation': 'Mom',
    }

    def get_object(self, factory):
        return factory.create(user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'user': self.user.id,
        })

        return self.create_data
