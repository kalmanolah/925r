from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from rest_assured import testcases
from django.utils.timezone import utc
from ninetofiver import factories
from decimal import Decimal
from datetime import timedelta
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from ninetofiver.settings import REDMINE_URL, REDMINE_API_KEY
from ninetofiver.redmine.choices import get_redmine_project_choices, get_redmine_user_choices
from ninetofiver.redmine.views import get_redmine_user_time_entries
from redminelib import exceptions, Redmine

from ninetofiver import models

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(filemode='w', filename='BONARRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR.log', level=logging.WARNING)

import tempfile
import datetime

now = datetime.date.today()


class AuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = factories.UserFactory()
        self.user.set_password('password')
        self.user.save()
        self.client.login(username=self.user.username, password='password')
        # self.client.force_authenticate(self.user)


class ModelTestMixin:

    """This test case mixin provides some additional tests for model instances."""

    def test_absolute_url(self):
        """Test whether the absolute URL for an object can be generated."""
        self.assertIsNotNone(self.object.get_absolute_url())

    def test_extended_validation(self):
        """Test extended validation for an object."""
        self.object.validate_unique()


class GenericViewTests(AuthenticatedAPITestCase):
    def setUp(self):
        super().setUp()

    def test_home_view(self):
        """Test the home view."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_account_view(self):
        """Test the account view."""
        response = self.client.get(reverse('account'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_schema_view(self):
        """Test the API schema view."""
        response = self.client.get(reverse('api_docs'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_my_user_service_api_view(self):
        """Test the 'My User' service API view."""
        # self.employmentcontract = factories.EmploymentContractFactory.create(
        #     company=factories.CompanyFactory.create(),
        #     employment_contract_type=factories.EmploymentContractTypeFactory.create(),
        #     user=self.user,
        #     work_schedule=factories.WorkScheduleFactory.create(),
        # )
        # self.employmentcontract.save()
        # self.user_info = factories.UserInfoFactory.create(user=self.user)
        # self.user_info.save()
        response = self.client.get(reverse('my_user_service'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_label'], str(self.user))


class CompanyAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'company'
    factory_class = factories.CompanyFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Foo BVBA',
        'vat_identification_number': 'BE123123123123',
        'internal': False,
        'address': 'Essensteenweg 29, 2930 Brasschaat, België',
        'country': 'BE',
    }
    update_data = {
        'name': 'Foo sprl',
        'vat_identification_number': 'BE321321321321',
        'internal': True,
        'address': 'Essensteenweg 31, 2930 Brasschaat, België',
        'country': 'BE',
    }


class EmploymentContractTypeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase,
                                        ModelTestMixin):
    base_name = 'employmentcontracttype'
    factory_class = factories.EmploymentContractTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Temp',
    }
    update_data = {
        'label': 'Perm',
    }


class EmploymentContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'employmentcontract'
    factory_class = factories.EmploymentContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'started_at': datetime.date(now.year + 10, 1, 15),
    }
    update_data = {
        'started_at': datetime.date(now.year + 10, 1, 15),
        'ended_at': datetime.date(now.year + 10, 1, 16),
    }

    def setUp(self):
        self.company = factories.CompanyFactory.create()
        self.work_schedule = factories.WorkScheduleFactory.create()
        self.employment_contract_type = factories.EmploymentContractTypeFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user, company=self.company, work_schedule=self.work_schedule,
                              employment_contract_type=self.employment_contract_type)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'user': self.user.id,
            'work_schedule': self.work_schedule.id,
            'employment_contract_type': self.employment_contract_type.id,
        })

        return self.create_data


class WorkScheduleAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'workschedule'
    factory_class = factories.WorkScheduleFactory
    user_factory = factories.AdminFactory
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


class UserInfoAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'userinfo'
    factory_class = factories.UserInfoFactory
    update_data = {
        'birth_date': datetime.date(now.year - 10, 1, 15),
        'gender': 'f',
        'country': 'UA'
    }

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.company = factories.CompanyFactory.create()
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.CompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.user,
            work_schedule=factories.WorkScheduleFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user)


class UserRelativeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'userrelative'
    factory_class = factories.UserRelativeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'birth_date': datetime.date(now.year - 10, 1, 15),
        'name': 'John Doe',
        'gender': 'm',
        'relation': 'Dad',
    }
    update_data = {
        'birth_date': datetime.date(now.year - 10, 1, 15),
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


class HolidayAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'holiday'
    factory_class = factories.HolidayFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Friday Night Deploy',
        'date': datetime.date(now.year, 1, 15),
        'country': 'BE',
    }
    update_data = {
        'name': 'Saturday Morning Deploy',
        'date': datetime.date(now.year, 1, 16),
        'country': 'BE',
    }


class LeaveTypeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'leavetype'
    factory_class = factories.LeaveTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'ADV',
    }
    update_data = {
        'label': 'Recup',
    }


class LeaveAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'leave'
    factory_class = factories.LeaveFactory
    user_factory = factories.AdminFactory
    create_data = {
        'description': 'Not going to work',
        'status': 'DRAFT',
    }
    update_data = {
        'description': 'Going to sleep',
        'status': 'PENDING',
    }

    def setUp(self):
        self.leave_type = factories.LeaveTypeFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(
            user=self.user,
            leave_type=self.leave_type,
        )

    def get_create_data(self):
        self.create_data.update({
            'user': self.user.id,
            'leave_type': self.leave_type.id,
        })

        return self.create_data


class LeaveDateAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'leavedate'
    factory_class = factories.LeaveDateFactory
    user_factory = factories.AdminFactory

    create_data = {
        'starts_at': datetime.datetime(now.year, now.month, 1, 7, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(now.year, now.month, 1, 8, 34, 34, tzinfo=utc),
    }
    update_data = {
        'starts_at': datetime.datetime(now.year, now.month, 7, 9, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(now.year, now.month, 7, 10, 34, 34, tzinfo=utc),
    }

    def setUp(self):
        user = factories.AdminFactory.create()
        self.leave = factories.LeaveFactory.create(
            user=user,
            leave_type=factories.LeaveTypeFactory.create(),
        )
        self.workschedule = factories.WorkScheduleFactory.create()
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.CompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=user,
            work_schedule=self.workschedule,
        )
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=user,
        )
        self.timesheet.year = now.year
        self.timesheet.month = now.month
        self.timesheet.save()

        super().setUp()

    def get_object(self, factory):
        return factory.create(leave=self.leave, timesheet=self.timesheet)

    def get_create_data(self):
        self.create_data.update({
            'leave': self.leave.id,
            'timesheet': self.timesheet.id,
        })

        return self.create_data


class PerformanceTypeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'performancetype'
    factory_class = factories.PerformanceTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Regular',
        'multiplier': 1.00,
    }
    update_data = {
        'label': 'Sundays',
        'multiplier': 2.00,
    }


class ContractGroupAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contractgroup'
    factory_class = factories.ContractGroupFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Cool contract',
    }
    update_data = {
        'label': 'Lame contract',
    }


class ContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contract'
    factory_class = factories.ContractFactory
    user_factory = factories.AdminFactory

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)


class ProjectContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'projectcontract'
    factory_class = factories.ProjectContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Projects & Stuff',
        'active': True,

        'fixed_fee': 600.25,
        'starts_at': now,
        'ends_at': now + timedelta(days=365),
    }
    update_data = {
        'label': 'More Projects & Stuff',
        'active': True,

        'fixed_fee': 300.25,
        'starts_at': now - timedelta(days=20),
        'ends_at': now + timedelta(days=730),
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class ProjectEstimateAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'projectestimate'
    factory_class = factories.ProjectEstimateFactory
    user_factory = factories.AdminFactory
    create_data = {
        'hours_estimated': 725
    }
    update_data = {
        'hours_estimated': 625
    }

    def setUp(self):
        self.role = factories.ContractRoleFactory.create()
        self.project = factories.ProjectContractFactory.create(
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(role=self.role, project=self.project)

    def get_create_data(self):
        self.create_data.update({
            'role': self.role.id,
            'project': self.project.id,
        })

        return self.create_data


class ConsultancyContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'consultancycontract'
    factory_class = factories.ConsultancyContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Consultancy & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'label': 'More Consultancy & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class SupportContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'supportcontract'
    factory_class = factories.SupportContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Support & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'label': 'More Support & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class ContractRoleAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contractrole'
    factory_class = factories.ContractRoleFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'Project Manager',
    }
    update_data = {
        'label': 'Developer',
    }


class ContractUserAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contractuser'
    factory_class = factories.ContractUserFactory
    user_factory = factories.AdminFactory
    create_data = {}
    update_data = {}

    def setUp(self):
        self.contract = factories.ContractFactory.create(
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        self.contract_role = factories.ContractRoleFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(contract=self.contract, contract_role=self.contract_role, user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'contract': self.contract.id,
            'contract_role': factories.ContractRoleFactory.create().id,
            'user': self.user.id,
        })

        return self.create_data


class TimesheetAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'timesheet'
    factory_class = factories.TimesheetFactory
    user_factory = factories.AdminFactory
    create_data = {
        'status': 'ACTIVE',
        'year': now.year,
        'month': now.month,
    }
    update_data = {
        'status': 'ACTIVE',
        'year': now.year,
        'month': now.month,
    }

    def get_object(self, factory):
        return factory.create(user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'user': self.user.id,
        })

        return self.create_data


class WhereaboutAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'whereabout'
    factory_class = factories.WhereaboutFactory
    user_factory = factories.AdminFactory
    create_data = {
        'day': 12,
        'location': 'Brasschaat',
    }
    update_data = {
        'day': 13,
        'location': 'Home'
    }

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.AdminFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id
        })

        return self.create_data


class PerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'performance'
    factory_class = factories.PerformanceFactory
    user_factory = factories.AdminFactory

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.AdminFactory.create(),
        )
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.CompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, contract=self.contract)


class ActivityPerformanceAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'activityperformance'
    factory_class = factories.ActivityPerformanceFactory
    user_factory = factories.AdminFactory
    create_data = {
        'day': 6,
        'duration': 12,
        'description': 'Just doing things',
    }
    update_data = {
        'day': 7,
        'duration': 13,
        'description': 'Not doing all that much',
    }

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.AdminFactory.create(),
        )
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, performance_type=self.performance_type, contract=self.contract)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
            'performance_type': self.performance_type.id,
        })

        return self.create_data


class StandbyPerformanceAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'standbyperformance'
    factory_class = factories.StandbyPerformanceFactory
    user_factory = factories.AdminFactory
    create_data = {
        'day': 9,
    }
    update_data = {
        'day': 10,
    }

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.AdminFactory.create(),
        )
        self.contract = factories.SupportContractFactory(
            active=True,
            company=factories.CompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, contract=self.contract)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
        })

        return self.create_data


class AttachmentAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'attachment'
    factory_class = factories.AttachmentFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'myfile',
        'description': 'My file\'s description',
    }
    update_data = {
        'label': 'yourfile',
        'description': 'Your file\'s description',
    }

    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        self.tmp_file.write(bytes('foo', 'UTF-8'))
        self.tmp_file.seek(0)
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'user': self.user.id,
            'file': self.tmp_file,
        })

        return self.create_data

    def get_create_response(self, data=None, **kwargs):
        return super().get_create_response(data=data, format='multipart', **kwargs)

    def get_update_response(self, data=None, results=None, use_patch=None, **kwargs):
        return super().get_update_response(data=data, results=results, use_patch=True, format='multipart', **kwargs)


class MyLeaveAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myleave'
    factory_class = factories.LeaveFactory
    user_factory = factories.AdminFactory
    create_data = {
        'description': 'Not going to work',
        'status': 'DRAFT',
    }
    update_data = {
        'description': 'Going to sleep',
        'status': 'PENDING',
    }

    def setUp(self):
        self.leave_type = factories.LeaveTypeFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(
            user=self.user,
            leave_type=self.leave_type,
        )

    def get_create_data(self):
        self.create_data.update({
            'leave_type': self.leave_type.id,
        })

        return self.create_data


class MyLeaveDateAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myleavedate'
    factory_class = factories.LeaveDateFactory
    # user_factory = factories.AdminFactory
    create_data = {
        'starts_at': datetime.datetime(now.year, now.month, 10, 7, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(now.year, now.month, 10, 8, 34, 34, tzinfo=utc),
    }
    update_data = {
        'starts_at': datetime.datetime(now.year, now.month, 14, 9, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(now.year, now.month, 14, 10, 34, 34, tzinfo=utc),
    }

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.workschedule = factories.WorkScheduleFactory.create()
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.CompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.user,
            work_schedule=self.workschedule,
        )
        self.leave = factories.LeaveFactory.create(
            user=self.user,
            leave_type=factories.LeaveTypeFactory.create(),
        )
        self.leave.save()
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.timesheet.year = now.year
        self.timesheet.month = now.month
        self.timesheet.save()
        super().setUp()

    def get_object(self, factory):
        return factory.create(leave=self.leave, timesheet=self.timesheet)

    def get_create_data(self):
        self.create_data.update({
            'leave': self.leave.id,
            'timesheet': self.timesheet.id,
        })

        return self.create_data


class TimeEntryImportServiceAPIViewTestCase(APITestCase):
    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.url = reverse('time_entry_import_service')

    def test_user_info_not_found(self):
        """Test scenario where contractuser's info is not found."""
        user_info_error = self.client.get(self.url)
        self.assertEqual(user_info_error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_redmine_id_not_found(self):
        """Test scenario where redmine_id for contractuser's info is not found."""
        self.user_info = factories.UserInfoFactory(
            user=self.user
        ).save()

        with self.assertRaises(Exception):
            redmine_error = self.client.get(self.url)
            self.assertEqual(redmine_error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_success(self):
        """Test scenario where everything goes by the books."""
        redm_users = get_redmine_user_choices()
        redm_user = next(iter(redm_users))
        redm_user_id = redm_user[0]
        user_info = factories.UserInfoFactory(
            user=self.user,
            redmine_id=redm_user[0]
        )
        success_response = self.client.get(self.url, {'filter_imported': 'true'})
        self.assertEqual(success_response.status_code, status.HTTP_200_OK)


class MonthInfoServiceAPIViewTestcase(APITestCase): 

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.CompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.user,
            work_schedule=factories.WorkScheduleFactory.create(),
        )
        self.userinfo = factories.UserInfoFactory.create(
            user=self.user
        )
        self.timesheet = factories.TimesheetFactory.create(
            user=self.user,
            month=now.month
        )

        self.second_user = factories.UserFactory.create()
        self.second_userinfo = factories.UserInfoFactory.create(
            user=self.second_user
        )
        self.second_employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.CompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.second_user,
            work_schedule=factories.WorkScheduleFactory.create(),
        )
        self.contract = factories.ContractFactory.create(
            company=factories.CompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        self.activityperformance = factories.ActivityPerformanceFactory.create(
            timesheet=self.timesheet,
            contract=self.contract,
            performance_type=factories.PerformanceTypeFactory.create()
        )

        self.url = reverse('month_info_service')
        super().setUp()

    def test_get_required_hours(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_get_required_hours_without_employmentcontract(self):
        self.employmentcontract.delete()
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_required_hours_without_userinfo(self):
        self.userinfo.delete()
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_get_required_hours_with_leave(self):
        leave = factories.LeaveFactory.create(
            user=self.user,
            leave_type=factories.LeaveTypeFactory.create()
        )
        leavedate = factories.LeaveDateFactory(
            leave=leave,
            timesheet=self.timesheet,
            starts_at=timezone.make_aware(datetime.datetime(now.year, now.month, 5, 0, 0, 0), timezone.get_current_timezone()),
            ends_at=timezone.make_aware(datetime.datetime(now.year, now.month, 5, 12, 30, 0), timezone.get_current_timezone())
        )
        leave.status = 'APPROVED'
        leavedate.save()
        leave.save()
        
        get_response = self.client.get(self.url, {'month':now.month})
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_get_required_hours_of_user(self):
        get_response = self.client.get(self.url, {'user_id':self.second_user.id})
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_get_hours_performed(self):
        get_response = self.client.get(self.url)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_get_hours_performed_of_user(self):
        get_response = self.client.get(self.url, {'user_id': self.second_user.id})
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
  
    def test_get_hours_performed_month(self):
        get_response = self.client.get(self.url, {'month': now.month})
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
    
    def test_get_hours_performed_month_year(self):
        get_response = self.client.get(self.url, {'month': now.month, 'year': now.year})
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

    def test_get_required_hours_with_invalid_user(self):
        get_response = self.client.get(self.url, {'user_id': '999999999'})
        self.assertEqual(get_response.status_code, status.HTTP_400_BAD_REQUEST)

        
class MyLeaveRequestsServiceAPITestcase(APITestCase):
    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        workschedule = factories.WorkScheduleFactory.create()
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company = factories.CompanyFactory.create(),
            employment_contract_type = factories.EmploymentContractTypeFactory.create(),
            user = self.user,
            work_schedule = workschedule
        )

        self.create_url = reverse('my_leave_request_service')
        self.update_url = reverse('my_leave_request_update_service')
        super().setUp()

    #Success 
    #   Full day
    def test_normal_create_success(self):
        """Test normal scenario where leave dates can be created."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 2, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 5, 0, 0, 0)
        }

        # Check for normal creation success
        post_normal_response = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_normal_response.status_code, status.HTTP_201_CREATED)

    def test_normal_create_full_day_string_success(self):
        """Test normal scenario where leave dates can be created with full_day param as a string instead of a boolean."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': 'true',
            'starts_at': datetime.datetime(now.year, now.month, 2, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 5, 0, 0, 0)
        }

        # Check for normal creation success
        post_normal_response = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_normal_response.status_code, status.HTTP_201_CREATED)

    def test_create_cross_year_success(self):
        """Test a scenario where leave dates can be created from one year into the next."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, 12, 25, 0, 0, 0),
            'ends_at': datetime.datetime(now.year + 1, 1, 5, 0, 0, 0)
        }

        # Check for normal creation success
        post_create_cross_year_success = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_create_cross_year_success.status_code, status.HTTP_201_CREATED)

    def test_patch_leave_dates_success(self):
        """Test scenario where a pre-existing leave is patched."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        update_data = {
            'leave_id': temp_post.data['leave'],
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 5, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 15, 0, 0, 0)
        }
        patch_leave_dates_success = self.client.patch(self.update_url, update_data, format='json')
        self.assertEqual(patch_leave_dates_success.status_code, status.HTTP_201_CREATED)

    def test_put_leave_dates_success(self):
        """Test scenario where a pre-existing leave is putted."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        update_data = {
            'leave_id': temp_post.data['leave'],
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        put_leave_dates_success = self.client.put(self.update_url, update_data, format='json')
        self.assertEqual(put_leave_dates_success.status_code, status.HTTP_201_CREATED)

    #   Single day with time
    def test_normal_single_day_create_success(self):
        """Test normal scenario where leave dates can be created for a single day with time."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': False,
            'starts_at': datetime.datetime(now.year, now.month, 2, 9, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 2, 14, 30, 0)
        }

        # Check for normal creation success
        post_normal_single_day_response = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_normal_single_day_response.status_code, status.HTTP_201_CREATED)

    def test_patch_leave_dates_single_day_success(self):
        """Test scenario where a pre-existing leave is patched for a single day with time."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': False,
            'starts_at': datetime.datetime(now.year, now.month, 1, 9, 30, 0),
            'ends_at': datetime.datetime(now.year, now.month, 1, 11, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        update_data = {
            'leave_id': temp_post.data['leave'],
            'full_day': False,
            'starts_at': datetime.datetime(now.year, now.month, 2, 14, 30, 0),
            'ends_at': datetime.datetime(now.year, now.month, 2, 15, 0, 0)
        }
        patch_leave_dates_single_day_success = self.client.patch(self.update_url, update_data, format='json')
        self.assertEqual(patch_leave_dates_single_day_success.status_code, status.HTTP_201_CREATED)

    def test_put_leave_dates_single_day_success(self):
        """Test scenario where a pre-existing leave is putted for a single day with time."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': False,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 1, 23, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        update_data = {
            'leave_id': temp_post.data['leave'],
            'full_day': False,
            'starts_at': datetime.datetime(now.year, now.month, 18, 12, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 16, 30, 0)
        }
        put_leave_dates_single_day_success = self.client.put(self.update_url, update_data, format='json')
        self.assertEqual(put_leave_dates_single_day_success.status_code, status.HTTP_201_CREATED)


    #Error
    #   Full day
    def test_inactive_employment_contract_error(self):
        """Test alternative scenario where a user no longer has an active employmentcontract."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 9, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 11, 0, 0, 0)
        }

        with self.assertRaises(Exception):
            self.employmentcontract.ended_at = datetime.datetime(now.year - 1, now.month, 1, 0, 0, 0)
            self.employmentcontract.save()
            post_inactive_employmentcontract_response = self.client.post(self.create_url, create_data, format='json')
            self.assertEqual(post_inactive_employmentcontract_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_leave_creation_error(self):
        """Test scenario where leaves are requested, yet overlap"""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 2, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 17, 0, 0, 0)
        }
        post_duplicate_leave_response = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_duplicate_leave_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_overlapping_leave_creation_error(self):
        """Test scenario where leaves are requested, yet overlap"""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 2, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 17, 0, 0, 0)
        }
        post_overlapping_leave_response = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_overlapping_leave_response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_put_invalid_leave_error(self):
        """Test scenario where a non-existant leave is putted."""

        update_data = {
            'leave_id': 420,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }

        with self.assertRaises(ObjectDoesNotExist):
            put_leave_dates_error = self.client.put(self.update_url, update_data, format='json')
            self.assertEqual(put_leave_dates_error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_invalid_leave_type_error(self):
        """Test scenario where a non-existant leave_type is posted."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': int(ltype.id) + 1,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        with self.assertRaises(ObjectDoesNotExist):
            post_leave_type_error = self.client.post(self.create_url, create_data, format='json')

    def test_patch_leave_error(self):
        """Test scenario where a newly created leave_request is updated with a new leave_id."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 1, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 18, 0, 0, 0)
        }
        temp_post = self.client.post(self.create_url, create_data, format='json')

        newLType = factories.LeaveTypeFactory.create()
        newLeave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data['leave_id'] = newLeave.id

        patch_leave_error = self.client.patch(self.update_url, create_data, format='json')
        self.assertRaises(ObjectDoesNotExist)
        self.assertEqual(patch_leave_error.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_start_end_error(self):
        """Test scenario where the end happens before the start."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )
        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 5, 0, 0, 0),
            'ends_at': datetime.datetime(now.year, now.month, 2, 0, 0, 0)
        }

        post_invalid_start_end = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_invalid_start_end.status_code, status.HTTP_400_BAD_REQUEST)

    #   Single day with time
    def test_single_day_full_day_error(self):
        """Test a scenario where the start and end are on the same day but the full_day flag is active."""
        ltype = factories.LeaveTypeFactory.create()
        leave = factories.LeaveFactory.create(
            user = self.user,
            leave_type = ltype
        )

        create_data = {
            'description' : leave.description,
            'status': leave.status,
            'leave_type': ltype.id,
            'full_day': True,
            'starts_at': datetime.datetime(now.year, now.month, 9, 10, 30, 0),
            'ends_at': datetime.datetime(now.year, now.month, 9, 12, 30, 0)
        }

        post_single_day_full_day = self.client.post(self.create_url, create_data, format='json')
        self.assertEqual(post_single_day_full_day.status_code, status.HTTP_400_BAD_REQUEST)


class MyTimesheetAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mytimesheet'
    factory_class = factories.OpenTimesheetFactory
    update_url = reverse('mytimesheet-list')
    user_factory = factories.AdminFactory
    create_data = {
        'status': "ACTIVE",
        'year': now.year,
        'month': now.month,
    }
    update_data = {
        'status': "ACTIVE",
        'year': now.year,
        'month': now.month,
    }

    def get_object(self, factory):
        return factory.create(user=self.user)

    def test_pending_to_active_update(self):
        user = factories.UserFactory()
        timesheet = factories.TimesheetFactory(
            status="PENDING",
            year=now.year,
            month=now.month,
            user=user
        )
        update_data = {
            'status': "ACTIVE",
            'year': now.year,
            'month': now.month
        }
        patch_invalid_status = self.client.patch(self.update_url, self.update_data, format='json')
        # patch_invalid_status = self.client.patch('/api/v1/my_timesheets/', self.update_data, format='json')
        self.assertEqual(patch_invalid_status.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

class MyContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mycontract'
    factory_class = factories.ContractFactory
    create_data = {
        'label': 'Cool contract',
        'description': 'This is a very cool contract. B-)',
        'active': True,
    }
    update_data = {
        'label': 'Stupid contract',
        'description': 'This is a very stupid contract. :(',
        'active': True,
    }

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()

        super().setUp()

    def get_object(self, factory):
        contract = factory.create(company=self.company, customer=self.customer)
        factories.ContractUserFactory.create(user=self.user, contract=contract, contract_role=factories.ContractRoleFactory.create())
        return contract

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class MyPerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myperformance'
    factory_class = factories.PerformanceFactory
    # user_factory = factories.AdminFactory

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.CompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, contract=self.contract)


class MyActivityPerformanceAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myactivityperformance'
    factory_class = factories.ActivityPerformanceFactory
    # user_factory = factories.AdminFactory
    create_data = {
        'day': 12,
        'duration': 12,
        'description': 'Just doing things',
    }
    update_data = {
        'day': 13,
        'duration': 13,
        'description': 'Not doing all that much',
    }

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, performance_type=self.performance_type, contract=self.contract)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
            'performance_type': self.performance_type.id,
        })

        return self.create_data


class MyStandbyPerformanceAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mystandbyperformance'
    factory_class = factories.StandbyPerformanceFactory
    # user_factory = factories.AdminFactory
    create_data = {
        'day': 14,
    }
    update_data = {
        'day': 17,
    }

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.contract = factories.SupportContractFactory.create(
            active=True,
            company=factories.CompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, contract=self.contract)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
        })

        return self.create_data


class MyAttachmentAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myattachment'
    factory_class = factories.AttachmentFactory
    user_factory = factories.AdminFactory
    create_data = {
        'label': 'myfile',
        'description': 'My file\'s description',
    }
    update_data = {
        'label': 'yourfile',
        'description': 'Your file\'s description',
    }

    def setUp(self):
        self.tmp_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        self.tmp_file.write(bytes('foo', 'UTF-8'))
        self.tmp_file.seek(0)
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'file': self.tmp_file,
        })

        return self.create_data

    def get_create_response(self, data=None, **kwargs):
        return super().get_create_response(data=data, format='multipart', **kwargs)

    def get_update_response(self, data=None, results=None, use_patch=None, **kwargs):
        return super().get_update_response(data=data, results=results, use_patch=True, format='multipart', **kwargs)


class MyWorkScheduleAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myworkschedule'
    factory_class = factories.WorkScheduleFactory
    user_factory = factories.AdminFactory
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

    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)

        self.work_schedule = factories.WorkScheduleFactory.create()

        super().setUp()

    def get_object(self, factory):
        work_schedule = self.work_schedule
        factories.EmploymentContractFactory.create(
            user=self.user, 
            company=factories.CompanyFactory.create(),
            work_schedule=self.work_schedule,
            employment_contract_type=factories.EmploymentContractTypeFactory.create()
        )
        return work_schedule

    def test_get_current_work_schedule(self):
        response = self.client.get(reverse('myworkschedule-list'), {'current':True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

class RedmineAPITestCase(APITestCase):
    def test_empty_redmine_url(self):
        redmine = Redmine('', key=REDMINE_API_KEY)
        self.assertRaises(exceptions.ResourceError)

    def test_redmine_project_choices(self):
        project_choices = get_redmine_project_choices()
        self.assertIsNotNone(project_choices)

    def test_redmine_user_choices(self):
        user_choices = get_redmine_user_choices()
        self.assertIsNotNone(user_choices)

    def test_redmine_user_time_entry_import(self):
        users = get_redmine_user_choices()
        user = next(iter(users))
        params = {
            'filter_imported': 'false'
        }
        time_entries = get_redmine_user_time_entries(user[0], params)
        self.assertIsNotNone(time_entries)

    def test_redmine_user_time_entry_import_filter_imported(self):
        users = get_redmine_user_choices()
        user = next(iter(users))
        params = {
            'filter_imported': 'true'
        }
        time_entries = get_redmine_user_time_entries(user[0], params)
        self.assertIsNotNone(time_entries)
