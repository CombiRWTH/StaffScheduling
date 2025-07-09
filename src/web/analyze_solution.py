import re
from datetime import datetime, timedelta
from collections import defaultdict
from employee import Employee
from shift import Shift


def analyze_solution(
    variables: dict[str, int], employees: list[Employee], shifts: list[Shift]
) -> dict[str, int]:
    parsed = defaultdict(dict)  # employee_id → {date: shift_id}
    shift_duration_map = {s.get_id(): s.duration for s in shifts}
    employee_map = {e.get_key(): e for e in employees}

    stats = {
        "Forward Rotation Violations": 0,
        "Consecutive Working Days > 5": 0,
        "No Free Weekend": 0,
        "Consecutive Night Shifts > 3": 0,
        "Total Overtime Hours": 0,
        "No Free Days Around Weekend": 0,
        "48 Hrs not free after Night Shift": 0,
    }

    # Parse solution variables
    for key, value in variables.items():
        if value != 1:
            continue
        match = re.match(r"\((\d+), '([\d\-]+)', (\d+)\)", key)
        if match:
            e = int(match.group(1))
            d = datetime.strptime(match.group(2), "%Y-%m-%d").date()
            s = int(match.group(3))
            parsed[e][d] = s

    #  Analyze per employee
    for emp_id, schedule in parsed.items():
        emp = employee_map[emp_id]
        days = sorted(schedule)
        shifts_assigned = [schedule[d] for d in days]

        # Forward Rotation Violations
        for i in range(len(days) - 1):
            if shifts_assigned[i + 1] < shifts_assigned[i]:
                stats["Forward Rotation Violations"] += 1

        # Too Many Consecutive Days
        streak = 1
        for i in range(1, len(days)):
            if (days[i] - days[i - 1]).days == 1:
                streak += 1
                if streak > 5:
                    stats["Consecutive Working Days > 5"] += 1
            else:
                streak = 1

        # No Free Weekend (must have Sat or Sun off)
        worked_weekend = [d for d in days if d.weekday() in [5, 6]]
        if worked_weekend and all(d in schedule for d in worked_weekend):
            stats["No Free Weekend"] += 1

        # Consecutive Night Shifts > 3
        night_streak = 0
        for s in shifts_assigned:
            if s == 2:
                night_streak += 1
                if night_streak > 3:
                    stats["Consecutive Night Shifts > 3"] += 1
            else:
                night_streak = 0

        # Overtime: IST - SOLL
        ist_minutes = sum(shift_duration_map.get(s, 450) for s in shifts_assigned)
        soll_minutes = emp._target_working_time
        overtime = ist_minutes - soll_minutes
        if overtime > 0:
            stats["Total Overtime Hours"] += overtime / 60
            stats["Total Overtime Hours"] = round(stats["Total Overtime Hours"], 2)

        # No Free Days Around Weekend (Fri+Sat or Sat+Sun)
        for d in days:
            if d.weekday() == 4 and (d + timedelta(days=1)) in schedule:
                stats["No Free Days Around Weekend"] += 1
            elif d.weekday() == 5 and (d + timedelta(days=1)) in schedule:
                stats["No Free Days Around Weekend"] += 1

        #48 hrs free after night shift
        for d in days:
            if schedule[d] == Shift.NIGHT:
                next_day = d + timedelta(days=1)
                after_next_day = d + timedelta(days=2)
                if next_day in schedule or after_next_day in schedule:
                    stats["48 Hrs not free after Night Shift"] += 1

    return stats
