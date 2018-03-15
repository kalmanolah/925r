from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_assured import testcases
from django.utils.timezone import utc
from ninetofiver import factories, models
from decimal import Decimal
from datetime import timedelta
import logging
import tempfile
import datetime


log = logging.getLogger(__name__)
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
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.InternalCompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.user,
            work_schedule=factories.WorkScheduleFactory.create(),
        )
        self.employmentcontract.save()
        response = self.client.get(reverse('my_user_service'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['display_label'], str(self.user))


class ContractUserGroupTests(AuthenticatedAPITestCase):
    """Contract user group tests."""

    def test_automatic_contract_user_handling(self):
        """Test automatic contract user handling."""
        # Initial data setup
        contract = factories.ContractFactory.create()
        user = factories.UserFactory.create()
        group_one = factories.GroupFactory.create()
        group_two = factories.GroupFactory.create()
        contract_role_one = factories.ContractRoleFactory()
        contract_role_two = factories.ContractRoleFactory()

        user.groups.add(group_one)

        # Contract should initially have no contract users
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If a contract user group is created for the user's group,
        # the user should have a contract user created for the contract with the given
        # contract role
        contract_user_group = factories.ContractUserGroupFactory.create(contract=contract, group=group_one,
                                                                        contract_role=contract_role_one)
        self.assertEqual(contract.contractuser_set.count(), 1)
        self.assertEqual(contract.contractuser_set.all()[0].user, user)
        self.assertEqual(contract.contractuser_set.all()[0].contract_role, contract_role_one)

        # If the contract user group's contract role is changed, the contract user's role should change as well
        contract_user_group.contract_role = contract_role_two
        contract_user_group.save()

        self.assertEqual(contract.contractuser_set.count(), 1)
        self.assertEqual(contract.contractuser_set.all()[0].user, user)
        self.assertEqual(contract.contractuser_set.all()[0].contract_role, contract_role_two)

        # If the group is removed from the user, the contract user should be gone
        user.groups.remove(group_one)
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If the group is added to the user, the contract user should exist
        user.groups.add(group_one)
        self.assertEqual(contract.contractuser_set.count(), 1)

        # If the user is removed from the group, the contract user should be gone
        group_one.user_set.remove(user)
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If the user is added to the group, the contract user should exist
        group_one.user_set.add(user)
        self.assertEqual(contract.contractuser_set.count(), 1)

        # If the contract user group's group is changed to one which doesn't contain the user, the contract user should
        # be gone
        contract_user_group.group = group_two
        contract_user_group.save()
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If the contract user group's group is changed to one which contains the user, the contract user should exist
        contract_user_group.group = group_one
        contract_user_group.save()
        self.assertEqual(contract.contractuser_set.count(), 1)

        # If the contract user group is removed, the contract user should be gone
        contract_user_group.delete()
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If we add the second group to the user, no contract user groups should exist
        user.groups.add(group_two)
        self.assertEqual(contract.contractuser_set.count(), 0)

        # If we create two contract user groups for the same contract role, only one contract user should exist
        contract_user_group_one = factories.ContractUserGroupFactory.create(contract=contract, group=group_one,
                                                                            contract_role=contract_role_one)
        contract_user_group_two = factories.ContractUserGroupFactory.create(contract=contract, group=group_two,
                                                                            contract_role=contract_role_one)
        self.assertEqual(contract.contractuser_set.count(), 1)

        # If we change the contract role of the second contract user group, two contract users should exist
        contract_user_group_two.contract_role = contract_role_two
        contract_user_group_two.save()
        self.assertEqual(contract.contractuser_set.count(), 2)

        # If we change the contract role of the first contract user group, one contract user should exist again
        contract_user_group_one.contract_role = contract_role_two
        contract_user_group_one.save()
        self.assertEqual(contract.contractuser_set.count(), 1)

        # If we delete any one of the contract user groups, one contract user should remain
        contract_user_group_two.delete()
        self.assertEqual(contract.contractuser_set.count(), 1)

        # Deleting the final contract user group should remove the final contract user
        contract_user_group_one.delete()
        self.assertEqual(contract.contractuser_set.count(), 0)


class TimesheetTests(AuthenticatedAPITestCase):
    """Timesheet tests."""

    def test_extended_validation(self):
        """Test non active timesheet creation."""
        today = datetime.date.today()

        # Creating a pending timesheet should fail
        res = self.client.post('/api/v1/my_timesheets/', data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_PENDING,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Creating an active timesheet should work
        res = self.client.post('/api/v1/my_timesheets/', data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ts_id = res.data['id']

        # Attempting to update the timesheet to CLOSED should not work
        res = self.client.patch('/api/v1/my_timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_CLOSED,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to update the timesheet to PENDING should work
        res = self.client.patch('/api/v1/my_timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_PENDING,
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Attempting to reopen the timesheet should not work
        res = self.client.patch('/api/v1/my_timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to close the timesheet should not work
        res = self.client.patch('/api/v1/my_timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_CLOSED,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to delete the timesheet should not work
        res = self.client.delete('/api/v1/my_timesheets/%s/' % ts_id)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class CompanyAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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


class EmploymentContractTypeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase,
                                        ModelTestMixin):
    base_name = 'employmentcontracttype'
    factory_class = factories.EmploymentContractTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Temp',
    }
    update_data = {
        'name': 'Perm',
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
        self.user.userinfo.delete()
        self.client.force_authenticate(self.user)

        self.company = factories.CompanyFactory.create()
        self.employmentcontract = factories.EmploymentContractFactory.create(
            company=factories.InternalCompanyFactory.create(),
            employment_contract_type=factories.EmploymentContractTypeFactory.create(),
            user=self.user,
            work_schedule=factories.WorkScheduleFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(user=self.user)


class UserRelativeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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


class HolidayAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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


class LeaveTypeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'leavetype'
    factory_class = factories.LeaveTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'ADV',
    }
    update_data = {
        'name': 'Recup',
    }


class LeaveAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'leave'
    factory_class = factories.LeaveFactory
    user_factory = factories.AdminFactory
    create_data = {
        'description': 'Not going to work',
        'status': 'draft',
    }
    update_data = {
        'description': 'Going to sleep',
        'status': 'pending',
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


class LeaveDateAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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
            company=factories.InternalCompanyFactory.create(),
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


class PerformanceTypeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'performancetype'
    factory_class = factories.PerformanceTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Regular',
        'multiplier': 1.00,
    }
    update_data = {
        'name': 'Sundays',
        'multiplier': 2.00,
    }


class ContractGroupAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contractgroup'
    factory_class = factories.ContractGroupFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Cool contract',
    }
    update_data = {
        'name': 'Lame contract',
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


class ProjectContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'projectcontract'
    factory_class = factories.ProjectContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Projects & Stuff',
        'active': True,

        'fixed_fee': 600.25,
        'starts_at': now,
        'ends_at': now + timedelta(days=365),
    }
    update_data = {
        'name': 'More Projects & Stuff',
        'active': True,

        'fixed_fee': 300.25,
        'starts_at': now - timedelta(days=20),
        'ends_at': now + timedelta(days=730),
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        self.url = reverse('projectcontract-list')
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class ConsultancyContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'consultancycontract'
    factory_class = factories.ConsultancyContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Consultancy & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'name': 'More Consultancy & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        self.url = reverse('consultancycontract-list')
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class SupportContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'supportcontract'
    factory_class = factories.SupportContractFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Support & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'name': 'More Support & Stuff',
        'starts_at': now,
        'day_rate': 600,
        'active': True,
    }

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        self.url = reverse('supportcontract-list')
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)

    def get_create_data(self):
        self.create_data.update({
            'company': self.company.id,
            'customer': self.customer.id,
        })

        return self.create_data


class ContractRoleAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'contractrole'
    factory_class = factories.ContractRoleFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Project Manager',
    }
    update_data = {
        'name': 'Developer',
    }


class ContractUserAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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


class TimesheetAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'timesheet'
    factory_class = factories.TimesheetFactory
    user_factory = factories.AdminFactory
    create_data = {
        'status': 'active',
        'year': now.year,
        'month': now.month,
    }
    update_data = {
        'status': 'active',
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


class ActivityPerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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
        self.user = factories.AdminFactory.create()
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        self.contract_role = factories.ContractRoleFactory.create()
        self.contract_user = factories.ContractUserFactory(user=self.user, contract=self.contract,
                                                           contract_role=self.contract_role)
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, performance_type=self.performance_type, contract=self.contract,
                              contract_role=self.contract_role)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
            'performance_type': self.performance_type.id,
            'contract_role': self.contract_role.id,
        })

        return self.create_data


class StandbyPerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
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


class AttachmentAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'attachment'
    factory_class = factories.AttachmentFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'myfile',
        'description': 'My file\'s description',
    }
    update_data = {
        'name': 'yourfile',
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
        'status': 'draft',
    }
    update_data = {
        'description': 'Going to sleep',
        'status': 'pending',
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
            company=factories.InternalCompanyFactory.create(),
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


class PerformanceImportServiceAPIViewTestCase(APITestCase):
    def setUp(self):
        self.user = factories.AdminFactory.create()
        self.client.force_authenticate(self.user)
        self.url = reverse('performance_import_service')

    def test_success(self):
        """Test scenario where everything goes by the books."""
        success_response = self.client.get(self.url)
        self.assertEqual(success_response.status_code, status.HTTP_200_OK)


class MyTimesheetAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mytimesheet'
    factory_class = factories.OpenTimesheetFactory
    user_factory = factories.AdminFactory
    create_data = {
        'status': 'active',
        'year': now.year,
        'month': now.month,
    }
    update_data = {
        'status': 'active',
        'year': now.year,
        'month': now.month,
    }

    def get_object(self, factory):
        return factory.create(user=self.user)


class MyContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mycontract'
    factory_class = factories.ContractFactory
    create_data = {
        'name': 'Cool contract',
        'description': 'This is a very cool contract. B-)',
        'active': True,
        'starts_at': now
    }
    update_data = {
        'name': 'Stupid contract',
        'description': 'This is a very stupid contract. :(',
        'active': True,
        'starts_at': now,
        'ends_at': datetime.date(now.year + 10, now.month, 1),
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


class MyContractUserAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'mycontractuser'
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
        self.contract_role = factories.ContractRoleFactory.create()
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ContractFactory.create(
            active=True,
            company=factories.InternalCompanyFactory.create(),
            customer=factories.CompanyFactory.create()
        )
        self.contract_user = factories.ContractUserFactory.create(user=self.user, contract=self.contract,
                                                                  contract_role=self.contract_role)
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet, performance_type=self.performance_type, contract=self.contract,
                              contract_role=self.contract_role)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
            'contract': self.contract.id,
            'performance_type': self.performance_type.id,
            'contract_role': self.contract_role.id,
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
        'name': 'myfile',
        'description': 'My file\'s description',
    }
    update_data = {
        'name': 'yourfile',
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


class MyWorkScheduleAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    base_name = 'myworkschedule'
    factory_class = factories.WorkScheduleFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Test schedule #1',
        'monday': Decimal('1.20'),
        'tuesday': Decimal('1.50'),
        'wednesday': Decimal('1.75'),
        'thursday': Decimal('0'),
        'friday': Decimal('2'),
        'saturday': Decimal('0'),
        'sunday': Decimal('0'),
    }
    update_data = {
        'name': 'Test schedule #2',
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
            company=factories.InternalCompanyFactory.create(),
            work_schedule=self.work_schedule,
            employment_contract_type=factories.EmploymentContractTypeFactory.create()
        )
        return work_schedule

    def test_get_current_work_schedule(self):
        response = self.client.get(reverse('myworkschedule-list'), {'current':True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
