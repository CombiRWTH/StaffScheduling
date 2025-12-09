import logging
from datetime import date

from src.cp import (
    EmployeeDayShiftVariable,
    EmployeeDayVariable,
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
    max_solutions=1,
    weights: dict | None = None,
    weight_id=None,
):
    loader = FSLoader(unit)
    employees = loader.get_employees()
    days = loader.get_days(start_date, end_date)
    shifts = loader.get_shifts()

    if weights is None:
        weights = {
            "free_weekend": 2.0,
            "consecutive_nights": 2.0,
            "hidden": 100.0,
            "overtime": 4.0,
            "consecutive_days": 1.0,
            "rotate": 1.0,
            "wishes": 3.0,
            "after_night": 3.0,
            "second_weekend": 1.0,
        }

    logging.info("General information:")
    logging.info(f"  - planning unit: {unit}")
    logging.info(f"  - start date: {start_date}")
    logging.info(f"  - end date: {end_date}")
    logging.info(f"  - number of employees: {len(employees)}")
    logging.info(f"  - number of days: {len(days)}")
    logging.info(f"  - number of shifts: {len(shifts)}")

    min_staffing = loader.get_min_staffing()

    # bad formatting
    variables = [
        EmployeeDayShiftVariable(employees, days, shifts),
        EmployeeDayVariable(employees, days, shifts),  # Based on EmployeeDayShiftVariable
    ]
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
    ]

    model = Model(max_solutions=max_solutions)
    for variable in variables:
        model.add_variable(variable)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    solutions = model.solve(timeout)

    wid = weight_id if weight_id is not None else "default"

    if solutions:
        for idx, s in enumerate(solutions):
            loader.write_solution(s, f"solution_{unit}_{start_date}-{end_date}_w{wid}_{idx}")
    else:
        logging.info(f"No solution found for weight set {weight_id}, nothing saved.")

    # solution_name = f"solution_{unit}_{start_date}-{end_date}"
    # loader.write_solution(solution, solution_name)
