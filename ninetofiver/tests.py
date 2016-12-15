from rest_framework.test import APITestCase
from rest_assured import testcases
from ninetofiver import factories
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
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user, company=self.company)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'user': self.user.id,
        })

        return self.create_data
