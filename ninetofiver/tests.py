from rest_assured import testcases
from django.utils.timezone import utc
from ninetofiver import factories
from decimal import Decimal
import datetime


class CompanyAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'company'
    factory_class = factories.CompanyFactory
    user_factory = factories.UserFactory
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


class EmploymentContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'employmentcontract'
    factory_class = factories.EmploymentContractFactory
    user_factory = factories.UserFactory
    create_data = {
        'started_at': datetime.date(datetime.date.today().year + 10, 1, 15),
    }
    update_data = {
        'started_at': datetime.date(datetime.date.today().year + 10, 1, 15),
        'ended_at': datetime.date(datetime.date.today().year + 10, 1, 16),
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


class HolidayAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'holiday'
    factory_class = factories.HolidayFactory
    user_factory = factories.UserFactory
    create_data = {
        'name': 'Friday Night Deploy',
        'date': datetime.date(datetime.date.today().year, 1, 15),
        'country': 'BE',
    }
    update_data = {
        'name': 'Saturday Morning Deploy',
        'date': datetime.date(datetime.date.today().year, 1, 16),
        'country': 'BE',
    }


class LeaveTypeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'leavetype'
    factory_class = factories.LeaveTypeFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'ADV',
    }
    update_data = {
        'label': 'Recup',
    }


class LeaveAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'leave'
    factory_class = factories.LeaveFactory
    user_factory = factories.UserFactory
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
        return factory.create(user=self.user, leave_type=self.leave_type)

    def get_create_data(self):
        self.create_data.update({
            'leave_type': self.leave_type.id,
            'user': self.user.id,
        })

        return self.create_data


class LeaveDateAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'leavedate'
    factory_class = factories.LeaveDateFactory
    user_factory = factories.UserFactory
    create_data = {
        'starts_at': datetime.datetime(datetime.date.today().year, 1, 16, 7, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(datetime.date.today().year, 1, 16, 8, 34, 34, tzinfo=utc),
    }
    update_data = {
        'starts_at': datetime.datetime(datetime.date.today().year, 1, 16, 9, 34, 34, tzinfo=utc),
        'ends_at': datetime.datetime(datetime.date.today().year, 1, 16, 10, 34, 34, tzinfo=utc),
    }

    def setUp(self):
        self.leave = factories.LeaveFactory.create(
            user=factories.UserFactory.create(),
            leave_type=factories.LeaveTypeFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(leave=self.leave)

    def get_create_data(self):
        self.create_data.update({
            'leave': self.leave.id,
        })

        return self.create_data


class PerformanceTypeAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'performancetype'
    factory_class = factories.PerformanceTypeFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Regular',
        'multiplier': 1.00,
    }
    update_data = {
        'label': 'Sundays',
        'multiplier': 2.00,
    }


class ContractAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'contract'
    factory_class = factories.ContractFactory
    user_factory = factories.UserFactory

    def setUp(self):
        self.company = factories.InternalCompanyFactory.create()
        self.customer = factories.CompanyFactory.create()
        super().setUp()

    def get_object(self, factory):
        return factory.create(company=self.company, customer=self.customer)


class ProjectContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'projectcontract'
    factory_class = factories.ProjectContractFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Projects & Stuff',
        'active': True,
    }
    update_data = {
        'label': 'More Projects & Stuff',
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


class ConsultancyContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'consultancycontract'
    factory_class = factories.ConsultancyContractFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Consultancy & Stuff',
        'starts_at': datetime.date.today(),
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'label': 'More Consultancy & Stuff',
        'starts_at': datetime.date.today(),
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


class SupportContractAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'supportcontract'
    factory_class = factories.SupportContractFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Support & Stuff',
        'starts_at': datetime.date.today(),
        'day_rate': 600,
        'active': True,
    }
    update_data = {
        'label': 'More Support & Stuff',
        'starts_at': datetime.date.today(),
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


class ContractRoleAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'contractrole'
    factory_class = factories.ContractRoleFactory
    user_factory = factories.UserFactory
    create_data = {
        'label': 'Project Manager',
    }
    update_data = {
        'label': 'Developer',
    }


class ContractUserAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'contractuser'
    factory_class = factories.ContractUserFactory
    user_factory = factories.UserFactory
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


class TimesheetAPITestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'timesheet'
    factory_class = factories.TimesheetFactory
    user_factory = factories.UserFactory
    create_data = {
        'closed': False,
        'year': datetime.date.today().year,
        'month': datetime.date.today().month,
    }
    update_data = {
        'closed': False,
        'year': datetime.date.today().year,
        'month': datetime.date.today().month,
    }

    def get_object(self, factory):
        return factory.create(user=self.user)

    def get_create_data(self):
        self.create_data.update({
            'user': self.user.id,
        })

        return self.create_data


class PerformanceAPITestCase(testcases.ReadRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'performance'
    factory_class = factories.PerformanceFactory
    user_factory = factories.UserFactory

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.UserFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet)


class ActivityPerformanceTestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'activityperformance'
    factory_class = factories.ActivityPerformanceFactory
    user_factory = factories.UserFactory
    create_data = {
        'day': datetime.date.today().day,
        'duration': 12,
        'description': 'Just doing things',
    }
    update_data = {
        'day': datetime.date.today().day,
        'duration': 13,
        'description': 'Not doing all that much',
    }

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.UserFactory.create(),
        )
        self.performance_type = factories.PerformanceTypeFactory.create()
        self.contract = factories.ContractFactory.create(
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


class StandbyPerformanceTestCase(testcases.ReadWriteRESTAPITestCaseMixin, testcases.BaseRESTAPITestCase):
    base_name = 'standbyperformance'
    factory_class = factories.StandbyPerformanceFactory
    user_factory = factories.UserFactory
    create_data = {
        'day': datetime.date.today().day,
    }
    update_data = {
        'day': datetime.date.today().day,
    }

    def setUp(self):
        self.timesheet = factories.OpenTimesheetFactory.create(
            user=factories.UserFactory.create(),
        )
        super().setUp()

    def get_object(self, factory):
        return factory.create(timesheet=self.timesheet)

    def get_create_data(self):
        self.create_data.update({
            'timesheet': self.timesheet.id,
        })

        return self.create_data
