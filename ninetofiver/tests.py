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

    user_factory = factories.UserFactory

    def setUp(self):
        super().setUp()
        self.user = self.user_factory()
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


class AdminReportViewTests(AuthenticatedAPITestCase):
    """Admin report view tests."""

    user_factory = factories.AdminFactory

    def setUp(self):
        super().setUp()

    def test_report_index_view(self):
        """Test the report index view."""
        response = self.client.get(reverse('admin_report_index'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_timesheet_contract_overview_report_view(self):
        """Test the timesheet contract overview report view."""
        response = self.client.get(reverse('admin_report_timesheet_contract_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_timesheet_overview_report_view(self):
        """Test the timesheet overview report view."""
        response = self.client.get(reverse('admin_report_timesheet_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_range_info_report_view(self):
        """Test the user range info report view."""
        response = self.client.get(reverse('admin_report_user_range_info'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_leave_overview_report_view(self):
        """Test the user leave overview report view."""
        response = self.client.get(reverse('admin_report_user_leave_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_work_ratio_overview_report_view(self):
        """Test the user work ratio overview report view."""
        response = self.client.get(reverse('admin_report_user_work_ratio_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_overtime_overview_report_view(self):
        """Test the user overtime overview report view."""
        response = self.client.get(reverse('admin_report_user_overtime_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_resource_availability_overview_report_view(self):
        """Test the resource availability overview report view."""
        response = self.client.get(reverse('admin_report_resource_availability_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expiring_consultancy_contract_overview_report_view(self):
        """Test the expiring consultancy contract overview report view."""
        response = self.client.get(reverse('admin_report_expiring_consultancy_contract_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_expiring_support_contract_overview_report_view(self):
        """Test the expiring support contract overview report view."""
        response = self.client.get(reverse('admin_report_expiring_support_contract_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_contract_overview_report_view(self):
        """Test the project contract overview report view."""
        response = self.client.get(reverse('admin_report_project_contract_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_project_contract_budget_overview_report_view(self):
        """Test the project contract budget overview report view."""
        response = self.client.get(reverse('admin_report_project_contract_budget_overview'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)