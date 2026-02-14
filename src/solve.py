import logging
import time
from collections.abc import Mapping
from datetime import date

from ortools.sat.python.cp_model import CpSolver

from src.cp import (
    EverySecondWeekendFreeObjective,
    FreeDayAfterNightShiftPhaseConstraint,
    FreeDaysAfterNightShiftPhaseObjective,
    FreeDaysNearWeekendObjective,
    HierarchyOfIntermediateShiftsConstraint,
    MaximizeEmployeeWishesObjective,
    MaxOneShiftPerDayConstraint,
    MinimizeConsecutiveNightShiftsObjective,
    # MinimizeHiddenEmployeeCountObjective,
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
from src.day import Day
from src.employee import Employee
from src.loader import FSLoader
from src.shift import Shift

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

MAX_CONSECUTIVE_DAYS = 5


def solve_with_constraints_only(
    employees: list[Employee], days: list[Day], shifts: list[Shift], min_staffing: dict[str, dict[str, dict[str, int]]]
) -> str:
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

    model = Model(employees, days, shifts)
    for constraint in constraints:
        model.add_constraint(constraint)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 8
    solver.parameters.max_time_in_seconds = 5
    solver.parameters.linearization_level = 0

    start = time.time()
    solver.solve(model.cpModel)
    end = time.time()
    logging.info(f"Wall time: {end - start}")

    return CpSolver.StatusName(solver)


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
    min_staffing = loader.get_min_staffing()

    # minimize hidden employees "manually"

    # phase 1 - find an upper bound
    # increase the hidden employee count raptitly for all classes simultaniously
    logging.info("Minimizing Hidden Employee Count Phase 1")
    status = "INFEASIBLE"
    increase = 5
    num_hidden_employees_per_level = {"Azubi": -increase, "Fachkraft": -increase, "Hilfskraft": -increase}
    while (status == "INFEASIBLE" or status == "UNKNOWN") and sum(num_hidden_employees_per_level.values()) <= 50:
        num_hidden_employees_per_level = {x: y + increase for (x, y) in num_hidden_employees_per_level.items()}
        logging.info(f"Trying to solve with {num_hidden_employees_per_level}")
        status = solve_with_constraints_only(
            employees + FSLoader.get_hidden_employees(num_hidden_employees_per_level), days, shifts, min_staffing
        )
        logging.info(f'Solver returned status = "{status}"')
    logging.info(f"Hidden Employee Upper Bound: {num_hidden_employees_per_level}\n")

    # phase 2 - find tight bounds
    # for each employee level lower the count unti it is tight
    logging.info("Minimizing Hidden Employee Count Phase 2")
    for level, value in num_hidden_employees_per_level.items():
        tmp = num_hidden_employees_per_level
        for i in range(value - 1, -1, -1):
            tmp[level] = i
            logging.info(f"Trying to solve with {tmp}")
            status = solve_with_constraints_only(
                employees + FSLoader.get_hidden_employees(tmp), days, shifts, min_staffing
            )
            logging.info(f'Solver returned status = "{status}"')
            if status == "INFEASIBLE" or status == "UNKNOWN":
                num_hidden_employees_per_level[level] = i + 1
                break
    logging.info(f"Hidden Employee Tight Bound: {num_hidden_employees_per_level}\n")

    employees += FSLoader.get_hidden_employees(num_hidden_employees_per_level)

    if weights is None:
        weights = {
            "free_weekend": 2,
            "consecutive_nights": 2,
            "hidden": 100,
            "hidden_count": 1000000,
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
        # MinimizeHiddenEmployeeCountObjective(weights["hidden_count"], employees, days, shifts),
    ]

    model = Model(employees, days, shifts)

    for constraint in constraints:
        model.add_constraint(constraint)

    for objective in objectives:
        model.add_objective(objective)

    solution = model.solve(timeout)
    wid = weight_id if weight_id is not None else "default"
    solution_name = f"solution_{unit}_{start_date}-{end_date}_w{wid}"
    loader.write_solution(solution, solution_name)

    return employees, days, shifts
