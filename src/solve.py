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


def main(unit: int, start_date: date, end_date: date, timeout: int, max_solutions=1):
    loader = FSLoader(unit)
    employees = loader.get_employees()
    days = loader.get_days(start_date, end_date)
    shifts = loader.get_shifts()

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
        FreeDaysNearWeekendObjective(2.0, employees, days),
        MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
        MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts),
        MinimizeOvertimeObjective(4.0, employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
        RotateShiftsForwardObjective(1.0, employees, days, shifts),
        MaximizeEmployeeWishesObjective(3.0, employees, days, shifts),
        FreeDaysAfterNightShiftPhaseObjective(3.0, employees, days, shifts),
        EverySecondWeekendFreeObjective(1.0, employees, days),
    ]

    model = Model(max_solutions=max_solutions)
    for variable in variables:
        model.add_variable(variable)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    solutions = model.solve(timeout)

    for idx, s in enumerate(solutions):
        loader.write_solution(s, f"solution_{unit}_{start_date}-{end_date}_{idx}")

    # solution_name = f"solution_{unit}_{start_date}-{end_date}"
    # loader.write_solution(solution, solution_name)
