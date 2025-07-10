import re
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List
from employee import Employee
from shift import Shift


def calculate_forward_rotation_violations(shifts_assigned: List[int]) -> int:
    return sum(
        1
        for i in range(len(shifts_assigned) - 1)
        if shifts_assigned[i + 1] < shifts_assigned[i]
    )


def calculate_consecutive_working_days(days: List[datetime.date]) -> int:
    streak = 1
    violations = 0
    for i in range(1, len(days)):
        if (days[i] - days[i - 1]).days == 1:
            streak += 1
            if streak > 5:
                violations += 1
        else:
            streak = 1
    return violations


def calculate_no_free_weekend(schedule: Dict[datetime.date, int]) -> int:
    worked_weekend = [d for d in schedule if d.weekday() in [5, 6]]
    if worked_weekend and all(d in schedule for d in worked_weekend):
        return 1
    return 0


def calculate_consecutive_night_shifts(shifts_assigned: List[int]) -> int:
    night_streak = 0
    violations = 0
    for s in shifts_assigned:
        if s == 2:
            night_streak += 1
            if night_streak > 3:
                violations += 1
        else:
            night_streak = 0
    return violations


def calculate_overtime(
    shifts_assigned: List[int], shift_duration_map: Dict[int, int], soll_minutes: int
) -> float:
    ist_minutes = sum(shift_duration_map.get(s, 450) for s in shifts_assigned)
    overtime = ist_minutes - soll_minutes
    return max(overtime / 60, 0)


def calculate_no_free_days_around_weekend(schedule: Dict[datetime.date, int]) -> int:
    violations = 0
    for d in schedule:
        if d.weekday() == 4 and (d + timedelta(days=1)) in schedule:
            violations += 1
        elif d.weekday() == 5 and (d + timedelta(days=1)) in schedule:
            violations += 1
    return violations


def calculate_not_free_after_night_shift(schedule: Dict[datetime.date, int]) -> int:
    violations = 0
    for d in schedule:
        if schedule[d] == Shift.NIGHT:
            next_day = d + timedelta(days=1)
            after_next_day = d + timedelta(days=2)
            if next_day in schedule or after_next_day in schedule:
                violations += 1
    return violations


def calculate_granted_shift_wishes(
    emp: Employee, schedule: Dict[datetime.date, int], shifts: List[Shift]
) -> int:
    count = 0
    for wish_day, wish_shift_abbr in emp.get_wish_shifts:
        for day, assigned_shift_id in schedule.items():
            if day.day == wish_day:
                if shifts[assigned_shift_id].abbreviation == wish_shift_abbr:
                    count += 1
    return count


def analyze_solution(
    variables: Dict[str, int], employees: List[Employee], shifts: List[Shift]
) -> Dict[str, float]:
    parsed = defaultdict(dict)  # employee_id → {date: shift_id}
    shift_duration_map = {s.get_id(): s.duration for s in shifts}
    employee_map = {e.get_key(): e for e in employees}

    forward_rotation_violations = 0
    consecutive_working_days_gt_5 = 0
    no_free_weekend = 0
    consecutive_night_shifts_gt_3 = 0
    total_overtime_hours = 0.0
    no_free_days_around_weekend = 0
    not_free_after_night_shift = 0
    granted_wish_shifts = 0

    for key, value in variables.items():
        if value != 1:
            continue
        match = re.match(r"\((\d+), '([\d\-]+)', (\d+)\)", key)
        if match:
            e = int(match.group(1))
            d = datetime.strptime(match.group(2), "%Y-%m-%d").date()
            s = int(match.group(3))
            parsed[e][d] = s

    for emp_id, schedule in parsed.items():
        emp = employee_map[emp_id]
        days = sorted(schedule)
        shifts_assigned = list(schedule.values())

        forward_rotation_violations += calculate_forward_rotation_violations(
            shifts_assigned
        )
        consecutive_working_days_gt_5 += calculate_consecutive_working_days(days)
        no_free_weekend += calculate_no_free_weekend(schedule)
        consecutive_night_shifts_gt_3 += calculate_consecutive_night_shifts(
            shifts_assigned
        )
        total_overtime_hours += calculate_overtime(
            shifts_assigned, shift_duration_map, emp._target_working_time
        )
        no_free_days_around_weekend += calculate_no_free_days_around_weekend(schedule)
        not_free_after_night_shift += calculate_not_free_after_night_shift(schedule)

        granted_wish_shifts += calculate_granted_shift_wishes(emp, schedule, shifts)

    return {
        "forward_rotation_violations": forward_rotation_violations,
        "consecutive_working_days_gt_5": consecutive_working_days_gt_5,
        "no_free_weekend": no_free_weekend,
        "consecutive_night_shifts_gt_3": consecutive_night_shifts_gt_3,
        "total_overtime_hours": round(total_overtime_hours, 2),
        "no_free_days_around_weekend": no_free_days_around_weekend,
        "not_free_after_night_shift": not_free_after_night_shift,
        "granted_wish_shifts": granted_wish_shifts,
    }
