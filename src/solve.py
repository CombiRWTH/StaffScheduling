import logging
from collections.abc import Mapping
from datetime import date

from src.cp import (
    EverySecondWeekendFreeObjective,
    FreeDayAfterNightShiftPhaseConstraint,
    FreeDaysAfterNightShiftPhaseObjective,
    FreeDaysNearWeekendObjective,
    HierarchyOfIntermediateShiftsConstraint,
    MaximizeEmployeeWishesObjective,
    MaxOneShiftPerDayConstraint,
    MinimizeConsecutiveNightShiftsObjective,
    MinimizeHiddenEmployeesObjective,
    MinimizeOvertimeObjective,
    MinRestTimeConstraint,
    MinStaffingConstraint,
    Model,
    NotTooManyConsecutiveDaysObjective,
    PlannedShiftsConstraint,
    RotateShiftsForwardObjective,
    RoundsInEarlyShiftConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
)
from src.loader import FSLoader

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MAX_CONSECUTIVE_DAYS = 5


def main(
    unit: int,
    start_date: date,
    end_date: date,
    timeout: int,
    weights: Mapping[str, int | float] | None = None,
    weight_id: int | None = None,
):
    loader = FSLoader(unit, start_date=start_date, end_date=end_date)
    employees = loader.get_employees()
    days = loader.get_days(start_date, end_date)
    shifts = loader.get_shifts()

    if weights is None:
        weights = {
            "free_weekend": 2,
            "consecutive_nights": 2,
            "hidden": 100,
            "hidden_count": 100000,
            "overtime": 4,
            "consecutive_days": 1,
            "rotate": 1,
            "wishes": 3,
            "after_night": 3,
            "second_weekend": 1,
        }

    logging.info("General information:")
    logging.info(f"  - planning unit: {unit}")
    logging.info(f"  - start date: {start_date}")
    logging.info(f"  - end date: {end_date}")
    logging.info(f"  - number of employees: {len(employees)}")
    logging.info(f"  - number of days: {len(days)}")
    logging.info(f"  - number of shifts: {len(shifts)}")

    min_staffing = loader.get_min_staffing()

    constraints = [
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts),
        MinRestTimeConstraint(employees, days, shifts),
        MinStaffingConstraint(min_staffing, employees, days, shifts),
        RoundsInEarlyShiftConstraint(employees, days, shifts),
        MaxOneShiftPerDayConstraint(employees, days, shifts),
        TargetWorkingTimeConstraint(employees, days, shifts),
        VacationDaysAndShiftsConstraint(employees, days, shifts),
        HierarchyOfIntermediateShiftsConstraint(employees, days, shifts),
        PlannedShiftsConstraint(employees, days, shifts),
    ]
    objectives = [
        FreeDaysNearWeekendObjective(weights["free_weekend"], employees, days),
        MinimizeConsecutiveNightShiftsObjective(weights["consecutive_nights"], employees, days, shifts),
        MinimizeHiddenEmployeesObjective(weights["hidden"], employees, days, shifts),
        MinimizeOvertimeObjective(weights["overtime"], employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, weights["consecutive_days"], employees, days),
        RotateShiftsForwardObjective(weights["rotate"], employees, days, shifts),
        MaximizeEmployeeWishesObjective(weights["wishes"], employees, days, shifts),
        FreeDaysAfterNightShiftPhaseObjective(weights["after_night"], employees, days, shifts),
        EverySecondWeekendFreeObjective(weights["second_weekend"], employees, days),
        # MinimizeHiddenEmployeeCountObjective(weights["hidden_count"], employees, days, shifts)
    ]

    model = Model(employees, days, shifts)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    solution = model.solve(timeout)
    wid = weight_id if weight_id is not None else "default"
    solution_name = f"solution_{unit}_{start_date}-{end_date}_w{wid}"
    loader.write_solution(solution, solution_name)
