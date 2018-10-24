"""925r API v2 tests."""
from rest_framework import status
from rest_framework.test import APITestCase
from rest_assured import testcases
from ninetofiver import factories, models
from ninetofiver.tests import ModelTestMixin, AuthenticatedAPITestCase
from django.utils import timezone
from django.shortcuts import reverse
import tempfile
import datetime


class GenericViewTests(AuthenticatedAPITestCase):
    """Generic view tests."""

    def setUp(self):
        super().setUp()

    def test_me_view(self):
        """Test me view."""
        response = self.client.get(reverse('ninetofiver_api_v2:me'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)

    def test_range_info_view(self):
        """Test range info view."""
        response = self.client.get('/api/v2/range_info/', {
            'from': str(datetime.date.today()),
            'until': str(datetime.date.today()),
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_range_availability_view(self):
        """Test range availability view."""
        response = self.client.get('/api/v2/range_availability/', {
            'from': str(datetime.date.today()),
            'until': str(datetime.date.today()),
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ApiKeyAuthenticationTests(APITestCase):
    """API key authentication tests."""

    def test_missing_api_key(self):
        """Test with missing query API key."""
        res = self.client.get(reverse('ninetofiver_api_v2:me'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_only_query_api_key(self):
        """Test with read-only API key."""
        user = factories.UserFactory()
        api_key = models.ApiKey.objects.create(user=user, read_only=True)

        res = self.client.get('/api/v2/me/?api_key=%s' % api_key.key)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], user.id)

        res = self.client.post('/api/v2/timesheets/?api_key=%s' % api_key.key, data={
            'year': datetime.date.today().year,
            'month': datetime.date.today().month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_write_query_api_key(self):
        """Test with read-write query API key."""
        user = factories.UserFactory()
        api_key = models.ApiKey.objects.create(user=user, read_only=False)

        res = self.client.get('/api/v2/me/?api_key=%s' % api_key.key)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], user.id)

        res = self.client.post('/api/v2/timesheets/?api_key=%s' % api_key.key, data={
            'year': datetime.date.today().year,
            'month': datetime.date.today().month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_read_only_header_api_key(self):
        """Test with read-only header API key."""
        user = factories.UserFactory()
        api_key = models.ApiKey.objects.create(user=user, read_only=True)

        res = self.client.get('/api/v2/me/', HTTP_AUTHORIZATION='Token %s' % api_key.key)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], user.id)

        res = self.client.post('/api/v2/timesheets/', HTTP_AUTHORIZATION='Token %s' % api_key.key, data={
            'year': datetime.date.today().year,
            'month': datetime.date.today().month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_read_write_header_api_key(self):
        """Test with read-write header API key."""
        user = factories.UserFactory()
        api_key = models.ApiKey.objects.create(user=user, read_only=False)

        res = self.client.get('/api/v2/me/', HTTP_AUTHORIZATION='Token %s' % api_key.key)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['id'], user.id)

        res = self.client.post('/api/v2/timesheets/', HTTP_AUTHORIZATION='Token %s' % api_key.key, data={
            'year': datetime.date.today().year,
            'month': datetime.date.today().month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_invalid_header_api_key(self):
        """Test with invalid header API key."""
        user = factories.UserFactory()
        api_key = models.ApiKey.objects.create(user=user, read_only=False)

        res = self.client.get('/api/v2/me/', HTTP_AUTHORIZATION='Token')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        res = self.client.get('/api/v2/me/', HTTP_AUTHORIZATION='Token %s %s' % (api_key.key, api_key.key))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class AttachmentAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Attachment API test case."""

    base_name = 'ninetofiver_api_v2:attachment'
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


class TimesheetAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Timesheet API test case."""

    base_name = 'ninetofiver_api_v2:timesheet'
    factory_class = factories.TimesheetFactory
    user_factory = factories.AdminFactory
    create_data = {
        'status': 'active',
        'year': datetime.date.today().year,
        'month': datetime.date.today().month,
    }
    update_data = {
        'status': 'active',
        'year': datetime.date.today().year,
        'month': datetime.date.today().month,
    }

    def get_object(self, factory):
        return factory.create(user=self.user)


class TimesheetTests(AuthenticatedAPITestCase):
    """Timesheet tests."""

    def test_extended_validation(self):
        """Test non active timesheet creation."""
        today = datetime.date.today()

        # Creating a pending timesheet should fail
        res = self.client.post('/api/v2/timesheets/', data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_PENDING,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Creating an active timesheet should work
        res = self.client.post('/api/v2/timesheets/', data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        ts_id = res.data['id']

        # Attempting to update the timesheet to CLOSED should not work
        res = self.client.patch('/api/v2/timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_CLOSED,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to update the timesheet to PENDING should work
        res = self.client.patch('/api/v2/timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_PENDING,
        })
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Attempting to reopen the timesheet should not work
        res = self.client.patch('/api/v2/timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_ACTIVE,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to close the timesheet should not work
        res = self.client.patch('/api/v2/timesheets/%s/' % ts_id, data={
            'year': today.year,
            'month': today.month,
            'status': models.STATUS_CLOSED,
        })
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Attempting to delete the timesheet should not work
        res = self.client.delete('/api/v2/timesheets/%s/' % ts_id)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class HolidayAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Holiday API test case."""

    base_name = 'ninetofiver_api_v2:holiday'
    factory_class = factories.HolidayFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Friday Night Deploy',
        'date': datetime.date(2018, 1, 15),
        'country': 'BE',
    }
    update_data = {
        'name': 'Saturday Morning Deploy',
        'date': datetime.date(2018, 1, 16),
        'country': 'BE',
    }


class LeaveTypeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Leave type API test case."""

    base_name = 'ninetofiver_api_v2:leavetype'
    factory_class = factories.LeaveTypeFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'ADV',
    }
    update_data = {
        'name': 'Recup',
    }


class LocationAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Location API test case."""

    base_name = 'ninetofiver_api_v2:location'
    factory_class = factories.LocationFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Loc#1',
    }
    update_data = {
        'name': 'Loc#2',
    }


class PerformanceTypeAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Performance type API test case."""

    base_name = 'ninetofiver_api_v2:performancetype'
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


class ContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Contract API test case."""

    base_name = 'ninetofiver_api_v2:contract'
    factory_class = factories.ProjectContractFactory
    user_factory = factories.AdminFactory

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        obj = factory.create(company=self.company, customer=self.customer)
        self.contract_user = factories.ContractUserFactory.create(user=self.user, contract=obj)

        return obj


class ContractRoleAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Contract role API test case."""

    base_name = 'ninetofiver_api_v2:contractrole'
    factory_class = factories.ContractRoleFactory
    user_factory = factories.AdminFactory
    create_data = {
        'name': 'Project Manager',
    }
    update_data = {
        'name': 'Developer',
    }


class ContractUserAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Contract user API test case."""

    base_name = 'ninetofiver_api_v2:contractuser'
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


class WhereaboutAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Whereabout API test case."""

    base_name = 'ninetofiver_api_v2:whereabout'
    factory_class = factories.WhereaboutFactory
    # user_factory = factories.AdminFactory
    create_data = {
        'starts_at': timezone.make_aware(datetime.datetime(2018, 3, 20, 13, 50)),
        'ends_at': timezone.make_aware(datetime.datetime(2018, 3, 20, 14, 50)),
    }
    update_data = {
        'starts_at': timezone.make_aware(datetime.datetime(2018, 3, 20, 12, 50)),
        'ends_at': timezone.make_aware(datetime.datetime(2018, 3, 20, 13, 50)),
    }

    def setUp(self):
        self.user = factories.AdminFactory()
        self.client.force_authenticate(self.user)
        self.timesheet = factories.OpenTimesheetFactory.create(user=self.user, year=2018, month=3)
        self.location = factories.LocationFactory.create()

        super().setUp()

    def get_object(self, factory):
        obj = factory.create(location=self.location, timesheet=self.timesheet,
                             starts_at=timezone.make_aware(datetime.datetime(2018, 3, 20, 16, 50)),
                             ends_at=timezone.make_aware(datetime.datetime(2018, 3, 20, 17, 50),))

        return obj


class PerformanceAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase, ModelTestMixin):
    """Performance API test case."""

    base_name = 'ninetofiver_api_v2:performance'
    factory_class = factories.ActivityPerformanceFactory
    # user_factory = factories.AdminFactory
    create_data = {
        'date': datetime.date(2018, 3, 15),
        'duration': 12,
        'description': 'Just doing things',
    }
    update_data = {
        'date': datetime.date(2018, 3, 17),
        'duration': 13,
        'description': 'Not doing all that much',
    }

    def setUp(self):
        self.user = factories.AdminFactory()
        self.client.force_authenticate(self.user)
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=self.user,
        )
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ProjectContractFactory.create(
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
                              contract_role=self.contract_role, date=datetime.date(self.timesheet.year, self.timesheet.month, 3))

    def get_create_data(self):
        self.create_data.update({
            'contract': self.contract.id,
            'performance_type': self.performance_type.id,
            'contract_role': self.contract_role.id,
            'type': 'ActivityPerformance',
        })

        return self.create_data

    def get_update_data(self):
        self.update_data.update({
            'contract': str(self.contract.id),
            'performance_type': str(self.performance_type.id),
            'contract_role': str(self.contract_role.id),
            'type': 'ActivityPerformance',
        })

        return self.update_data

    def _update_check_db(self, obj, data=None, results=None):
        setattr(obj, 'type', 'ActivityPerformance')
        super()._update_check_db(obj, data=data, results=results)
