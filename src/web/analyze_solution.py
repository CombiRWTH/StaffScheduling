import re
from datetime import datetime, timedelta

def analyze_solution(variables: dict[str, int]) -> dict[str, int]:
    parsed = {}  # (e, d) → shift_id

    # Step 1: Parse variable keys like "(2, '2024-11-01', 0)"
    for key, value in variables.items():
        if value != 1:
            continue
        match = re.match(r"\((\d+), '([\d\-]+)', (\d+)\)", key)
        if match:
            e = int(match.group(1))
            d = datetime.strptime(match.group(2), "%Y-%m-%d").date()
            s = int(match.group(3))
            parsed.setdefault(e, {})[d] = s

    # Step 2: Count forward rotation violations
    forward_rotation_violations = 0
    for emp, schedule in parsed.items():
        for d in sorted(schedule):
            next_day = d + timedelta(days=1)
            if next_day in schedule:
                if schedule[next_day] < schedule[d]:  # not rotating forward
                    forward_rotation_violations += 1

    # Step 3: Count overtime violations (naive: more than 5 shifts = overtime)
    overtime_violations = sum(1 for shifts in parsed.values() if len(shifts) > 5)

    # Step 4: Count rest violations (naive: consecutive shifts every day)
    rest_violations = 0
    for emp, schedule in parsed.items():
        days = sorted(schedule)
        for i in range(1, len(days)):
            if (days[i] - days[i-1]).days == 1:
                rest_violations += 1

    return {
        "Forward Rotation Violations": forward_rotation_violations,
        "Overtime Violations": overtime_violations,
        "Rest Violations": rest_violations,
    }
