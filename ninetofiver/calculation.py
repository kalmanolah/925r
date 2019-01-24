"""Calculation."""
from django.db.models import Q
from decimal import Decimal
from datetime import timedelta
import copy
from ninetofiver import models
from ninetofiver.api_v2 import serializers


def get_availability(users, from_date, until_date, serialize=False):
    """Determine and return availability."""
    res = {}

    # Fetch sickness leave type IDs
    sickness_type_ids = list(models.LeaveType.objects.filter(sickness=True).values_list('id', flat=True))

    # Fetch all employment contracts for this period
    employment_contracts = (models.EmploymentContract.objects
                            .filter(
                                (Q(ended_at__isnull=True) & Q(started_at__lte=until_date)) |
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
                   .filter(Q(leave__status=models.STATUS_APPROVED) | Q(leave__status=models.STATUS_PENDING),
                           leave__user__in=users, starts_at__date__gte=from_date, starts_at__date__lte=until_date)
                   .select_related('leave', 'leave__leave_type', 'leave__user'))
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

    # Fetch all whereabouts for this period
    whereabouts = (models.Whereabout.objects
                   .filter(timesheet__user__in=users, starts_at__date__gte=from_date,
                           starts_at__date__lte=until_date)
                   .select_related('timesheet', 'timesheet__user', 'location'))
    # Index whereabouts by day, then by user ID
    whereabout_data = {}
    for whereabout in whereabouts:
        (whereabout_data
            .setdefault(str(whereabout.starts_at.date()), {})
            .setdefault(whereabout.timesheet.user.id, [])
            .append(whereabout))

    # Count days
    day_count = (until_date - from_date).days + 1

    # Iterate over users
    for user in users:
        # Initialize user data
        res[str(user.id)] = user_data = {}

        # Iterate over days
        for i in range(day_count):
            # Determine date for this day
            current_date = copy.deepcopy(from_date) + timedelta(days=i)
            user_data[str(current_date)] = user_day_data = {
                'work_hours': 0,
                'holidays': [],
                'leave': [],
                'sickness': [],
                'whereabouts': [],
            }

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

            # No work occurs when there is no work_schedule, or no hours should be worked that day
            if work_schedule:
                user_day_data['work_hours'] = getattr(work_schedule, current_date.strftime('%A').lower(), 0.00)

            # Holidays
            try:
                if country:
                    user_day_data['holidays'] = holiday_data[str(current_date)][country][0:]
            except KeyError:
                pass

            # Leave & Sickness
            try:
                for leave_date in leave_date_data[str(current_date)][user.id]:
                    if leave_date.leave.leave_type.id in sickness_type_ids:
                        user_day_data['sickness'] += [leave_date]
                    else:
                        user_day_data['leave'] += [leave_date]
            except KeyError:
                pass

            # Whereabouts
            try:
                user_day_data['whereabouts'] = whereabout_data[str(current_date)][user.id][0:]
            except KeyError:
                pass

            if serialize:
                user_day_data['whereabouts'] = serializers.WhereaboutSerializer(user_day_data['whereabouts'], many=True).data
                user_day_data['holidays'] = serializers.HolidaySerializer(user_day_data['holidays'], many=True).data
                user_day_data['leave'] = serializers.LeaveDateSerializer(user_day_data['leave'], many=True).data
                user_day_data['sickness'] = serializers.LeaveDateSerializer(user_day_data['sickness'], many=True).data

    return res


def get_availability_info(users, from_date, until_date):
    """Determine and return availability info."""
    res = {}

    # Fetch sickness leave type IDs
    sickness_type_ids = list(models.LeaveType.objects.filter(sickness=True).values_list('id', flat=True))

    # Fetch all employment contracts for this period
    employment_contracts = (models.EmploymentContract.objects
                            .filter(
                                (Q(ended_at__isnull=True) & Q(started_at__lte=until_date)) |
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
                   .filter(Q(leave__status=models.STATUS_APPROVED) | Q(leave__status=models.STATUS_PENDING),
                           leave__user__in=users, starts_at__date__gte=from_date, starts_at__date__lte=until_date)
                   .select_related('leave', 'leave__leave_type', 'leave__user'))
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

    # Fetch all whereabouts for this period
    whereabouts = (models.Whereabout.objects
                   .filter(timesheet__user__in=users, starts_at__date__gte=from_date,
                           starts_at__date__lte=until_date)
                   .select_related('timesheet', 'timesheet__user', 'location'))
    # Index whereabouts by day, then by user ID
    whereabout_data = {}
    for whereabout in whereabouts:
        (whereabout_data
            .setdefault(str(whereabout.starts_at.date()), {})
            .setdefault(whereabout.timesheet.user.id, [])
            .append(whereabout))

    # Count days
    day_count = (until_date - from_date).days + 1

    # Iterate over users
    for user in users:
        # Initialize user data
        res[str(user.id)] = user_data = {}

        # Iterate over days
        for i in range(day_count):
            # Determine date for this day
            current_date = copy.deepcopy(from_date) + timedelta(days=i)
            user_data[str(current_date)] = user_day_tags = []

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

            # No work occurs when there is no work_schedule, or no hours should be worked that day
            if (not work_schedule) or (getattr(work_schedule, current_date.strftime('%A').lower(), 0.00) <= 0):
                user_day_tags.append('no_work')

            # Holidays
            try:
                if country and holiday_data[str(current_date)][country]:
                    user_day_tags.append('holiday')
            except KeyError:
                pass

            # Leave & Sickness
            try:
                for leave_date in leave_date_data[str(current_date)][user.id]:
                    leave_status = leave_date.leave.status

                    if leave_date.leave.leave_type.id in sickness_type_ids:
                        if leave_status == models.STATUS_APPROVED:
                            user_day_tags.append('sickness')
                        else:
                            user_day_tags.append('sickness_pending')
                    else:
                        if leave_status == models.STATUS_APPROVED:
                            user_day_tags.append('leave')
                        else:
                            user_day_tags.append('leave_pending')
            except KeyError:
                pass

            # Whereabouts
            try:
                for whereabout in whereabout_data[str(current_date)][user.id]:
                    user_day_tags.append('whereabout_%s' % whereabout.location.name.lower().replace(' ', '_'))
            except KeyError:
                pass

    return res


def get_range_info(users, from_date, until_date, daily=False, detailed=False, summary=False, serialize=False):
    """Determine and return range info."""
    res = {}

    # Fetch all employment contracts for this period
    employment_contracts = (models.EmploymentContract.objects
                            .filter(
                                (Q(ended_at__isnull=True) & Q(started_at__lte=until_date)) |
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
                   .filter(leave__user__in=users, leave__status__in=[models.STATUS_PENDING, models.STATUS_APPROVED],
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

    # Fetch all activity performances for this period
    activity_performances = (models.ActivityPerformance.objects
                             .filter(date__gte=from_date, date__lte=until_date, timesheet__user__in=users)
                             .select_related('performance_type', 'contract_role', 'contract',
                                             'contract__customer', 'timesheet', 'timesheet__user'))
    # Index activity performances by day, then by user ID
    activity_performance_data = {}
    for performance in activity_performances:
        (activity_performance_data
            .setdefault(str(performance.date), {})
            .setdefault(performance.timesheet.user.id, [])
            .append(performance))

    # Fetch all standby performances for this period
    standby_performances = (models.StandbyPerformance.objects
                             .filter(date__gte=from_date, date__lte=until_date, timesheet__user__in=users)
                            .select_related('contract', 'contract__customer', 'timesheet', 'timesheet__user'))
    # Index standby performances by day, then by user ID
    standby_performance_data = {}
    for performance in standby_performances:
        (standby_performance_data
            .setdefault(str(performance.date), {})
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
        user_res['pending_leave_hours'] = 0
        user_res['performed_hours'] = 0
        user_res['remaining_hours'] = 0
        user_res['total_hours'] = 0
        user_res['overtime_hours'] = 0
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
            day_res['pending_leave_hours'] = 0
            day_res['performed_hours'] = 0
            day_res['remaining_hours'] = 0
            day_res['total_hours'] = 0
            day_res['overtime_hours'] = 0
            day_res['holidays'] = []
            day_res['leaves'] = []
            day_res['activity_performances'] = []
            day_res['standby_performances'] = []

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
                duration = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal('0.00'))
                user_res['work_hours'] += duration
                day_res['work_hours'] += duration

            # Holidays
            try:
                if country and holiday_data[str(current_date)][country]:
                    duration = getattr(work_schedule, current_date.strftime('%A').lower(), Decimal('0.00'))
                    user_res['holiday_hours'] += duration
                    day_res['holiday_hours'] += duration
                    day_res['holidays'] += holiday_data[str(current_date)][country]
            except KeyError:
                pass

            # Leave
            try:
                for leave_date in leave_date_data[str(current_date)][user.id]:
                    duration = round((leave_date.ends_at - leave_date.starts_at).total_seconds() / 3600, 2)
                    duration = Decimal(str(duration))
                    if leave_date.leave.status == models.STATUS_APPROVED:
                        user_res['leave_hours'] += duration
                        day_res['leave_hours'] += duration
                    else:
                        user_res['pending_leave_hours'] += duration
                        day_res['pending_leave_hours'] += duration
                    day_res['leaves'].append(leave_date.leave)
            except KeyError:
                pass

            # Activity performance
            try:
                for performance in activity_performance_data[str(current_date)][user.id]:
                    duration = performance.normalized_duration
                    user_res['performed_hours'] += duration
                    day_res['performed_hours'] += duration
                    day_res['activity_performances'].append(performance)
                    user_res['summary']['performances'].setdefault(performance.contract.id, {
                        'contract': performance.contract,
                        'duration': 0,
                        'standby_days': 0,
                    })['duration'] += duration
            except KeyError:
                pass

            # Standby performance
            try:
                for performance in standby_performance_data[str(current_date)][user.id]:
                    day_res['standby_performances'].append(performance)
                    user_res['summary']['performances'].setdefault(performance.contract.id, {
                        'contract': performance.contract,
                        'duration': 0,
                        'standby_days': 0,
                    })['standby_days'] += 1
            except KeyError:
                pass

            day_res['total_hours'] = (day_res['holiday_hours'] + day_res['leave_hours'] + day_res['performed_hours'])
            day_res['overtime_hours'] = abs(min(0, day_res['work_hours'] - day_res['total_hours']))
            day_res['remaining_hours'] = max(0, day_res['work_hours'] - day_res['total_hours'])

        user_res['total_hours'] = user_res['holiday_hours'] + user_res['leave_hours'] + user_res['performed_hours']
        user_res['overtime_hours'] = abs(min(0, user_res['work_hours'] - user_res['total_hours']))
        user_res['remaining_hours'] = max(0, user_res['work_hours'] - user_res['total_hours'])
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
                day_data.pop('activity_performances', None)
                day_data.pop('standby_performances', None)
        elif serialize:
            for day, day_data in user_res['details'].items():
                day_data['holidays'] = serializers.HolidaySerializer(day_data['holidays'], many=True).data
                day_data['leaves'] = serializers.LeaveSerializer(day_data['leaves'], many=True).data
                day_data['activity_performances'] = serializers.ActivityPerformanceSerializer(
                    day_data['activity_performances'], many=True).data
                day_data['standby_performances'] = serializers.StandbyPerformanceSerializer(
                    day_data['standby_performances'], many=True).data

        if not daily:
            user_res.pop('details', None)

    return res
