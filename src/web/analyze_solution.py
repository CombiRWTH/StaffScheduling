import re
from datetime import datetime, timedelta
from collections import defaultdict


def analyze_solution(variables: dict[str, int]) -> dict[str, int]:
    # Build: parsed[e][d] = s where e=employee, d=date, s=shift_id
    parsed = defaultdict(dict)
    shift_durations = {0: 450, 1: 450, 2: 600, 3: 300}  # Früh, Spät, Nacht, Zwischen

    for key, value in variables.items():
        if value != 1:
            continue
        match = re.match(r"\((\d+), '([\d\-]+)', (\d+)\)", key)
        if match:
            emp = int(match.group(1))
            date = datetime.strptime(match.group(2), "%Y-%m-%d").date()
            shift = int(match.group(3))
            parsed[emp][date] = shift

    stats = {
        "Forward Rotation Violations": 0,
        "Consecutive Working Days > 5": 0,
        "No Free Weekend": 0,
        "Consecutive Night Shifts > 3": 0,
        "Overtime Minutes (over 2250)": 0,
        "No Free Days Around Weekend": 0,
    }

    for emp, schedule in parsed.items():
        days = sorted(schedule)
        shifts = [schedule[d] for d in days]

        # 1. Rotate forward (next shift ID ≥ current)
        for i in range(len(days) - 1):
            if shifts[i + 1] < shifts[i]:
                stats["Forward Rotation Violations"] += 1

        # 2. Working > 5 consecutive days
        streak = 1
        for i in range(1, len(days)):
            if (days[i] - days[i - 1]).days == 1:
                streak += 1
                if streak > 5:
                    stats["Consecutive Working Days > 5"] += 1
            else:
                streak = 1

        # 3. Free Weekend (Sat or Sun must be free)
        worked_weekend = [d for d in days if d.weekday() in [5, 6]]
        if len(worked_weekend) > 0 and all(d in schedule for d in worked_weekend):
            stats["No Free Weekend"] += 1

        # 4. Consecutive night shifts (shift ID 2)
        night_streak = 0
        for s in shifts:
            if s == 2:
                night_streak += 1
                if night_streak > 3:
                    stats["Consecutive Night Shifts > 3"] += 1
            else:
                night_streak = 0

        # 5. Overtime Minutes (expected ≤ 2250 min = 37.5h/month)
        total_minutes = sum(shift_durations.get(s, 450) for s in shifts)
        if total_minutes > 2250:
            stats["Overtime Minutes (over 2250)"] += (total_minutes - 2250)

        # 6. No Free Days Around Weekend
        for d in days:
            if d.weekday() == 4 and (d + timedelta(days=1)) in schedule:
                stats["No Free Days Around Weekend"] += 1
            elif d.weekday() == 5 and (d + timedelta(days=1)) in schedule:
                stats["No Free Days Around Weekend"] += 1

    return stats