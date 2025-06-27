from loader import Loader
from cp import (
    Model,
    FreeDayAfterNightShiftPhaseConstraint,
    MinRestTimeConstraint,
    MinStaffingConstraint,
    MaxOneShiftPerDayConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
    EmployeeDayShiftVariable,
    EmployeeDayVariable,
    FreeDaysNearWeekendObjective,
    MinimizeConsecutiveNightShiftsObjective,
    MinimizeHiddenEmployeesObjective,
    MinimizeOvertimeObjective,
    NotTooManyConsecutiveDaysObjective,
    RotateShiftsForwardObjective,
)
from datetime import date
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_CONSECUTIVE_DAYS = 5


def main(loader: Loader, start_date: date, timeout: int):
    employees = loader.get_employees()
    days = loader.get_days(start_date)
    shifts = loader.get_shifts()

    min_staffing = loader.get_min_staffing()

    variables = [
        EmployeeDayShiftVariable(employees, days, shifts),
        EmployeeDayVariable(
            employees, days, shifts
        ),  # Based on EmployeeDayShiftVariable
    ]
    constraints = [
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts),
        MinRestTimeConstraint(employees, days, shifts),
        MinStaffingConstraint(min_staffing, employees, days, shifts),
        MaxOneShiftPerDayConstraint(employees, days, shifts),
        TargetWorkingTimeConstraint(employees, days, shifts),
        VacationDaysAndShiftsConstraint(employees, days, shifts),
    ]
    objectives = [
        FreeDaysNearWeekendObjective(10.0, employees, days),
        MinimizeConsecutiveNightShiftsObjective(2.0, employees, days, shifts),
        MinimizeHiddenEmployeesObjective(100.0, employees, days, shifts),
        MinimizeOvertimeObjective(4.0, employees, days, shifts),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, 1.0, employees, days),
        RotateShiftsForwardObjective(1.0, employees, days, shifts),
    ]

    model = Model()
    for variable in variables:
        model.add_variable(variable)

    for objective in objectives:
        model.add_objective(objective)

    for constraint in constraints:
        model.add_constraint(constraint)

    solution = model.solve(timeout)

    loader.write_solution(
        solution,
    )


if __name__ == "__main__":
    main()
