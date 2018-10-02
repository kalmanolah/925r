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
    """"Authenticated API test case."""

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
    """Generic view tests."""

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

    def test_api_docs_view(self):
        """Test the API docs view."""
        response = self.client.get(reverse('api_docs'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_docs_redoc_view(self):
        """Test the API docs redoc view."""
        response = self.client.get(reverse('api_docs_redoc'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_docs_swagger_ui_view(self):
        """Test the API docs swagger ui view."""
        response = self.client.get(reverse('api_docs_swagger_ui'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


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


# class LeaveAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
#     base_name = 'leave'
#     factory_class = factories.LeaveFactory
#     user_factory = factories.AdminFactory
#     create_data = {
#         'description': 'Not going to work',
#         'status': 'draft',
#     }
#     update_data = {
#         'description': 'Going to sleep',
#         'status': 'pending',
#     }

#     def setUp(self):
#         self.leave_type = factories.LeaveTypeFactory.create()
#         super().setUp()

#     def get_object(self, factory):
#         return factory.create(
#             user=self.user,
#             leave_type=self.leave_type,
#         )

#     def get_create_data(self):
#         self.create_data.update({
#             'user': self.user.id,
#             'leave_type': self.leave_type.id,
#         })

#         return self.create_data


# class ContractUserAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
#     base_name = 'contractuser'
#     factory_class = factories.ContractUserFactory
#     user_factory = factories.AdminFactory
#     create_data = {}
#     update_data = {}

#     def setUp(self):
#         self.contract = factories.ContractFactory.create(
#             company=factories.InternalCompanyFactory.create(),
#             customer=factories.CompanyFactory.create()
#         )
#         self.contract_role = factories.ContractRoleFactory.create()
#         super().setUp()

#     def get_object(self, factory):
#         return factory.create(contract=self.contract, contract_role=self.contract_role, user=self.user)

#     def get_create_data(self):
#         self.create_data.update({
#             'contract': self.contract.id,
#             'contract_role': factories.ContractRoleFactory.create().id,
#             'user': self.user.id,
#         })

#         return self.create_data


# class PerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
#     base_name = 'performance'
#     factory_class = factories.PerformanceFactory
#     user_factory = factories.AdminFactory

#     def setUp(self):
#         self.timesheet = factories.OpenTimesheetFactory.create(
#             user=factories.AdminFactory.create(),
#         )
#         self.contract = factories.ContractFactory.create(
#             active=True,
#             company=factories.CompanyFactory.create(),
#             customer=factories.CompanyFactory.create()
#         )
#         super().setUp()

#     def get_object(self, factory):
#         return factory.create(timesheet=self.timesheet, contract=self.contract)


# class ActivityPerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
#     base_name = 'activityperformance'
#     factory_class = factories.ActivityPerformanceFactory
#     user_factory = factories.AdminFactory
#     create_data = {
#         'day': 6,
#         'duration': 12,
#         'description': 'Just doing things',
#     }
#     update_data = {
#         'day': 7,
#         'duration': 13,
#         'description': 'Not doing all that much',
#     }

#     def setUp(self):
#         self.user = factories.AdminFactory.create()
#         self.timesheet = factories.OpenTimesheetFactory.create(
#             user=self.user,
#         )
#         self.performance_type = factories.PerformanceTypeFactory.create()
#         self.contract = factories.ContractFactory.create(
#             active=True,
#             company=factories.InternalCompanyFactory.create(),
#             customer=factories.CompanyFactory.create()
#         )
#         self.contract_role = factories.ContractRoleFactory.create()
#         self.contract_user = factories.ContractUserFactory(user=self.user, contract=self.contract,
#                                                            contract_role=self.contract_role)
#         super().setUp()

#     def get_object(self, factory):
#         return factory.create(timesheet=self.timesheet, performance_type=self.performance_type, contract=self.contract,
#                               contract_role=self.contract_role)

#     def get_create_data(self):
#         self.create_data.update({
#             'timesheet': self.timesheet.id,
#             'contract': self.contract.id,
#             'performance_type': self.performance_type.id,
#             'contract_role': self.contract_role.id,
#         })

#         return self.create_data


# class StandbyPerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
#     base_name = 'standbyperformance'
#     factory_class = factories.StandbyPerformanceFactory
#     user_factory = factories.AdminFactory
#     create_data = {
#         'day': 9,
#     }
#     update_data = {
#         'day': 10,
#     }

#     def setUp(self):
#         self.timesheet = factories.OpenTimesheetFactory.create(
#             user=factories.AdminFactory.create(),
#         )
#         self.contract = factories.SupportContractFactory(
#             active=True,
#             company=factories.CompanyFactory.create(),
#             customer=factories.CompanyFactory.create()
#         )
#         super().setUp()

#     def get_object(self, factory):
#         return factory.create(timesheet=self.timesheet, contract=self.contract)

#     def get_create_data(self):
#         self.create_data.update({
#             'timesheet': self.timesheet.id,
#             'contract': self.contract.id,
#         })

#         return self.create_data