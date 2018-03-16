"""Calculation."""
from django.db.models import Q
from decimal import Decimal
from datetime import timedelta
import copy
from ninetofiver import models, serializers


def get_range_info(users, from_date, until_date, daily=False, detailed=False, summary=False, serialize=False):
    """Determine and return range info."""
    res = {}

    # Fetch all employment contracts for this period
    employment_contracts = (models.EmploymentContract.objects
                            .filter(
                                (Q(ended_at__isnull=True) & Q(started_at__lte=from_date)) |
                                (Q(started_at__lte=until_date) & Q(ended_at__gte=from_date)),
                                user__in=users)
                            .order_by('started_at')
                            .select_related('user', 'company', 'work_schedule'))
    # Index employment contracts by user ID
    employment_contract_data = {}
    for employment_contract in employment_contracts:
        (employment_contract_data
            .setdefault(employment_contract.user.id, [])
            .append(employment_contract))

    # Fetch all leave dates for this period
    leave_dates = (models.LeaveDate.objects
                   .filter(leave__user__in=users, leave__status=models.STATUS_APPROVED,
                           starts_at__date__gte=from_date, starts_at__date__lte=until_date)
                   .select_related('leave', 'leave__leave_type', 'leave__user')
                   .prefetch_related('leave__attachments', 'leave__leavedate_set'))
    # Index leave dates by day, then by user ID
    leave_date_data = {}
    for leave_date in leave_dates:
        (leave_date_data
            .setdefault(str(leave_date.starts_at.date()), {})
            .setdefault(leave_date.leave.user.id, [])
            .append(leave_date))

    # Fetch all holidays for this period
    holidays = (models.Holiday.objects
                .filter(date__gte=from_date, date__lte=until_date))
    # Index holidays by day, then by country
    holiday_data = {}
    for holiday in holidays:
        (holiday_data
            .setdefault(str(holiday.date), {})
            .setdefault(holiday.country, [])
            .append(holiday))

    # Fetch all performances for this period
    performances = (models.ActivityPerformance.objects
                    .filter(
                        (Q(timesheet__year__gt=from_date.year) |
                         Q(timesheet__year__exact=from_date.year, timesheet__month__gt=from_date.month) |
                         Q(timesheet__year__exact=from_date.year, timesheet__month__exact=from_date.month,
                           day__gte=from_date.day)),
                        (Q(timesheet__year__lt=until_date.year) |
                         Q(timesheet__year__exact=until_date.year, timesheet__month__lt=until_date.month) |
                         Q(timesheet__year__exact=until_date.year, timesheet__month__exact=until_date.month,
                           day__lte=until_date.day)),
                        timesheet__user__in=users)
                    .select_related('performance_type', 'contract_role', 'contract',
                                    'contract__customer', 'timesheet', 'timesheet__user'))
    # Index performances by day, then by user ID
    performance_data = {}
    for performance in performances:
        (performance_data
            .setdefault(str(performance.get_date()), {})
            .setdefault(performance.timesheet.user.id, [])
            .append(performance))

    # Count days
    day_count = (until_date - from_date).days + 1

    for user in users:
        # Results are indexed by user ID
        user_res = res[user.id] = {}
        user_res['work_hours'] = 0
        user_res['holiday_hours'] = 0
        user_res['leave_hours'] = 0
        user_res['performed_hours'] = 0
        user_res['remaining_hours'] = 0
        user_res['total_hours'] = 0
        user_res['details'] = {}
        user_res['summary'] = {
            'performances': {},
        }

        # Iterate over days
        for i in range(day_count):
            # Determine date for this day
            current_date = copy.deepcopy(from_date) + timedelta(days=i)

            day_res = user_res['details'][str(current_date)] = {}
            day_res['work_hours'] = 0
            day_res['holiday_hours'] = 0
            day_res['leave_hours'] = 0
            day_res['performed_hours'] = 0
            day_res['remaining_hours'] = 0
            day_res['total_hours'] = 0
            day_res['holidays'] = []
            day_res['leaves'] = []
            day_res['performances'] = []

            # Get employment contract for this day
            # This allows us to determine the work schedule and country of the user
            employment_contract = None
            try:
                for ec in employment_contract_data[user.id]:
                    if (ec.started_at <= current_date) and ((not ec.ended_at) or (ec.ended_at >= current_date)):
                        employment_contract = ec
                        break
            except KeyError:
                pass

            work_schedule = employment_contract.work_schedule if employment_contract else None
            country = employment_contract.company.country if employment_contract else None

            # Work hours
            if work_schedule:
                duration = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal(0.00))
                user_res['work_hours'] += duration
                day_res['work_hours'] += duration

            # Holidays
            try:
                if country and holiday_data[str(current_date)][country]:
                    duration = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal(0.00))
                    user_res['holiday_hours'] += duration
                    day_res['holiday_hours'] += duration
                    day_res['holidays'].append(holiday)
            except KeyError:
                pass

            # Leave
            try:
                for leave_date in leave_date_data[str(current_date)][user.id]:
                    duration = Decimal(round((leave_date.ends_at - leave_date.starts_at).total_seconds() / 3600, 2))
                    user_res['leave_hours'] += duration
                    day_res['leave_hours'] += duration
                    day_res['leaves'].append(leave_date.leave)
            except KeyError:
                pass

            # Performance
            try:
                for performance in performance_data[str(current_date)][user.id]:
                    duration = Decimal(performance.duration)
                    user_res['performed_hours'] += duration
                    day_res['performed_hours'] += duration
                    day_res['performances'].append(performance)
                    user_res['summary']['performances'].setdefault(performance.contract.id, {
                        'contract': performance.contract,
                        'duration': 0,
                    })['duration'] += performance.duration
            except KeyError:
                pass

            day_res['total_hours'] = (day_res['holiday_hours'] + day_res['leave_hours'] + day_res['performed_hours'])
            day_res['remaining_hours'] = day_res['work_hours'] - day_res['total_hours']
            day_res['remaining_hours'] = max(0, day_res['remaining_hours'])

        user_res['total_hours'] = user_res['holiday_hours'] + user_res['leave_hours'] + user_res['performed_hours']
        user_res['remaining_hours'] = user_res['work_hours'] - user_res['total_hours']
        user_res['remaining_hours'] = max(0, user_res['remaining_hours'])
        user_res['summary']['performances'] = user_res['summary']['performances'].values()

        if not summary:
            user_res.pop('summary', None)
        elif serialize:
            for performance in user_res['summary']['performances']:
                performance['contract'] = serializers.MinimalContractSerializer(performance['contract']).data

        if not detailed:
            for day, day_data in user_res['details'].items():
                day_data.pop('leaves', None)
                day_data.pop('holidays', None)
                day_data.pop('performances', None)
        elif serialize:
            for day, day_data in user_res['details'].items():
                day_data['holidays'] = serializers.HolidaySerializer(day_data['holidays'], many=True).data
                day_data['leaves'] = serializers.LeaveSerializer(day_data['leaves'], many=True).data
                day_data['performances'] = serializers.ActivityPerformanceSerializer(day_data['performances'],
                                                                                     many=True).data

        if not daily:
            user_res.pop('details', None)

    return res
