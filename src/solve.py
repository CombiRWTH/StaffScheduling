import logging
import time
from collections.abc import Callable, Mapping
from datetime import date
from itertools import combinations

from ortools.sat.python.cp_model import CpSolver

from src.cp import (
    EverySecondWeekendFreeObjective,
    FreeDayAfterNightShiftPhaseConstraint,
    FreeDaysAfterNightShiftPhaseObjective,
    FreeDaysNearWeekendObjective,
    HierarchyOfIntermediateShiftsConstraint,
    MaximizeEmployeeWishesObjective,
    MaximizePreferredStationObjective,
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
    PreferredBlockLengthObjective,
    RotateShiftsForwardObjective,
    RoundsInEarlyShiftConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
)
from src.cp.constants import MAX_CONSECUTIVE_DAYS
from src.day import Day
from src.employee import Employee
from src.loader import FSLoader
from src.shift import Shift
from src.solution import Solution
from src.station import Station

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class SolveResult:
    """Return type of main() that supports both 3-tuple unpacking (for CLI) and .solution attribute access."""

    def __init__(
        self,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
        solution: Solution,
    ) -> None:
        self.employees = employees
        self.days = days
        self.shifts = shifts
        self.solution = solution

    def __iter__(self):
        yield self.employees
        yield self.days
        yield self.shifts


def solve_with_constraints_only(
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    stations: list[str],
    min_staffing: dict[str, dict[str, dict[str, int]]],
    status_callback: Callable[[str], None] | None = None,
) -> str:
    constraints = [
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts, stations),
        MinRestTimeConstraint(employees, days, shifts, stations),
        MinStaffingConstraint(min_staffing, employees, days, shifts, stations),
        RoundsInEarlyShiftConstraint(employees, days, shifts, stations),
        MaxOneShiftPerDayConstraint(employees, days, shifts, stations),
        TargetWorkingTimeConstraint(employees, days, shifts, stations),
        VacationDaysAndShiftsConstraint(employees, days, shifts, stations),
        HierarchyOfIntermediateShiftsConstraint(employees, days, shifts, stations),
        PlannedShiftsConstraint(employees, days, shifts, stations),
    ]

    model = Model(employees, days, shifts, stations)
    for constraint in constraints:
        model.add_constraint(constraint)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 8
    solver.parameters.max_time_in_seconds = 4000
    solver.parameters.linearization_level = 0

    start = time.time()

    solver.solve(model.cpModel)
    end = time.time()
    logging.info(f"Wall time: {end - start}")

    return CpSolver.StatusName(solver)


def _solve_constraint_subset(
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    stations: list[Station],
    constraints: list,
    timeout: int = 4000,
    loader: FSLoader | None = None,
    analyzer_log: str | None = None,
) -> str:
    model = Model(employees, days, shifts, stations)

    for constraint in constraints:
        model.add_constraint(constraint)

    solver = CpSolver()
    solver.parameters.num_workers = 8
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.linearization_level = 0

    status = solver.solve(model.cpModel)
    """if solver.StatusName(status) == "OPTIMAL":

        solution = model.solve(timeout, analyzer_log=analyzer_log)
        solution_name = f"solution_constraints_{'_'.join(constraint.KEY for constraint in constraints)}"
        if loader:
            loader.write_solution(solution, solution_name)"""
    return solver.StatusName(status)


def build_constraint_registry(
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    stations: list[Station],
    min_staffing: dict[str, dict[str, dict[str, int]]],
) -> list[tuple[str, object]]:
    return [
        (
            "FreeDayAfterNightShiftPhaseConstraint",
            FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts, stations),
        ),
        ("MinRestTimeConstraint", MinRestTimeConstraint(employees, days, shifts, stations)),
        ("MinStaffingConstraint", MinStaffingConstraint(min_staffing, employees, days, shifts, stations)),
        ("RoundsInEarlyShiftConstraint", RoundsInEarlyShiftConstraint(employees, days, shifts, stations)),
        ("MaxOneShiftPerDayConstraint", MaxOneShiftPerDayConstraint(employees, days, shifts, stations)),
        ("TargetWorkingTimeConstraint", TargetWorkingTimeConstraint(employees, days, shifts, stations)),
        ("VacationDaysAndShiftsConstraint", VacationDaysAndShiftsConstraint(employees, days, shifts, stations)),
        (
            "HierarchyOfIntermediateShiftsConstraint",
            HierarchyOfIntermediateShiftsConstraint(employees, days, shifts, stations),
        ),
        ("PlannedShiftsConstraint", PlannedShiftsConstraint(employees, days, shifts, stations)),
    ]


def diagnose_constraint_conflicts_with_max_hidden(
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    stations: list[Station],
    min_staffing: dict[str, dict[str, dict[str, int]]],
    max_hidden_per_level: int = 50,
    timeout: int = 4000,
    loader: FSLoader | None = None,
    analyzer_log: str | None = None,
) -> list[tuple[str, ...]]:
    hidden_counts = {
        "Azubi": max_hidden_per_level,
        "Fachkraft": max_hidden_per_level,
        "Hilfskraft": max_hidden_per_level,
    }

    test_employees = employees + FSLoader.get_hidden_employees(hidden_counts, start=len(employees))

    registry = build_constraint_registry(test_employees, days, shifts, stations, min_staffing)

    logging.info("Testing each constraint individually with maximum hidden employees...")

    for name, constraint in registry:
        status = _solve_constraint_subset(
            test_employees, days, shifts, stations, [constraint], timeout, loader, analyzer_log
        )
        logging.info(f"{name}: {status}")

    logging.info("Testing constraint combinations...")

    infeasible_combinations: list[tuple[str, ...]] = []

    for size in range(2, len(registry) + 1):
        logging.info(f"Testing combinations of size {size}...")

        for combo in combinations(registry, size):
            names = tuple(name for name, _ in combo)
            constraints = [constraint for _, constraint in combo]

            status = _solve_constraint_subset(
                test_employees, days, shifts, stations, constraints, timeout, loader, analyzer_log
            )

            if status in {"INFEASIBLE", "UNKNOWN"}:
                logging.warning(f"Conflict found: {names} -> {status}")
                infeasible_combinations.append(names)

        if infeasible_combinations:
            logging.warning("Smallest infeasible combinations found. Stopping search.")
            break

    return infeasible_combinations


def main(
    unit: int,
    start_date: date,
    end_date: date,
    timeout: int,
    weights: Mapping[str, int | float] | None = None,
    weight_id: int | None = None,
    employees: list[Employee] | None = None,
    status_callback: Callable[[str], None] | None = None,
    analyzer_log: str | None = None,
) -> SolveResult:
    loader = FSLoader(unit, start_date=start_date, end_date=end_date)
    days = loader.get_days(start_date, end_date)
    shifts = loader.get_shifts()
    stations = loader.get_stations()
    min_staffing = loader.get_min_staffing()

    conflicts = diagnose_constraint_conflicts_with_max_hidden(
        employees=loader.get_employees(),
        days=days,
        shifts=shifts,
        stations=stations,
        min_staffing=min_staffing,
        max_hidden_per_level=50,
        timeout=4000,
        loader=loader,
        analyzer_log=analyzer_log,
    )

    logging.warning(f"Minimal infeasible constraint combinations: {conflicts}")

    if employees is None:
        employees = loader.get_employees()
        # minimize hidden employees "manually"

        # phase 1 - find an upper bound
        # increase the hidden employee count raptitly for all classes simultaniously
        logging.info("Minimizing Hidden Employee Count Phase 1")
        if status_callback is not None:
            status_callback("phase_1_upper_bound")
        status = "INFEASIBLE"
        increase = 5
        num_hidden_employees_per_level = {"Azubi": -increase, "Fachkraft": -increase, "Hilfskraft": -increase}
        while (status == "INFEASIBLE" or status == "UNKNOWN") and sum(num_hidden_employees_per_level.values()) <= 50:
            num_hidden_employees_per_level = {x: y + increase for (x, y) in num_hidden_employees_per_level.items()}
            logging.info(f"Trying to solve with {num_hidden_employees_per_level}")
            status = solve_with_constraints_only(
                employees + FSLoader.get_hidden_employees(num_hidden_employees_per_level),
                days,
                shifts,
                stations,
                min_staffing,
            )
            logging.info(f'Solver returned status = "{status}"')
        logging.info(f"Hidden Employee Upper Bound: {num_hidden_employees_per_level}\n")

        # phase 2 - find tight bounds
        # for each employee level lower the count unti it is tight
        logging.info("Minimizing Hidden Employee Count Phase 2")
        if status_callback is not None:
            status_callback("phase_2_tight_bound")
        for level, value in num_hidden_employees_per_level.items():
            tmp = num_hidden_employees_per_level
            for i in range(value - 1, -1, -1):
                tmp[level] = i
                logging.info(f"Trying to solve with {tmp}")
                status = solve_with_constraints_only(
                    employees + FSLoader.get_hidden_employees(tmp), days, shifts, stations, min_staffing
                )
                logging.info(f'Solver returned status = "{status}"')
                if status == "INFEASIBLE" or status == "UNKNOWN":
                    num_hidden_employees_per_level[level] = i + 1
                    break
        logging.info(f"Hidden Employee Tight Bound: {num_hidden_employees_per_level}\n")

        employees += FSLoader.get_hidden_employees(num_hidden_employees_per_level)

    default_weights = {
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
        "preferred_block": 1,
        "preferred_station": 1,
    }

    # 2. Sicheres Mergen: Überschreibt Defaults mit Nutzer-Inputs,
    # füllt aber alle fehlenden Schlüssel auf.
    if weights is None:
        weights = default_weights
    else:
        # Merge-Operator: Kombiniert beide Dictionaries
        weights = default_weights | weights

    logging.info("General information:")
    logging.info(f"  - planning unit: {unit}")
    logging.info(f"  - start date: {start_date}")
    logging.info(f"  - end date: {end_date}")
    logging.info(f"  - number of employees: {len(employees)}")
    logging.info(f"  - number of days: {len(days)}")
    logging.info(f"  - number of shifts: {len(shifts)}")

    constraints = [
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts, stations),
        MinRestTimeConstraint(employees, days, shifts, stations),
        MinStaffingConstraint(min_staffing, employees, days, shifts, stations),
        RoundsInEarlyShiftConstraint(employees, days, shifts, stations),
        MaxOneShiftPerDayConstraint(employees, days, shifts, stations),
        TargetWorkingTimeConstraint(employees, days, shifts, stations),
        VacationDaysAndShiftsConstraint(employees, days, shifts, stations),
        HierarchyOfIntermediateShiftsConstraint(employees, days, shifts, stations),
        PlannedShiftsConstraint(employees, days, shifts, stations),
    ]

    if "preferred_block" not in weights.keys():
        prefered_block_size = 1
    else:
        prefered_block_size = weights["preferred_block"]
    objectives = [
        FreeDaysNearWeekendObjective(weights["free_weekend"], employees, days),
        MinimizeConsecutiveNightShiftsObjective(weights["consecutive_nights"], employees, days, shifts, stations),
        MinimizeHiddenEmployeesObjective(weights["hidden"], employees, days, shifts, stations),
        MinimizeOvertimeObjective(weights["overtime"], employees, days, shifts, stations),
        NotTooManyConsecutiveDaysObjective(MAX_CONSECUTIVE_DAYS, weights["consecutive_days"], employees, days),
        RotateShiftsForwardObjective(weights["rotate"], employees, days, shifts, stations),
        MaximizeEmployeeWishesObjective(weights["wishes"], employees, days, shifts, stations),
        FreeDaysAfterNightShiftPhaseObjective(weights["after_night"], employees, days, shifts, stations),
        EverySecondWeekendFreeObjective(weights["second_weekend"], employees, days),
        PreferredBlockLengthObjective(
            target_block_length=3,
            max_block_length=7,
            weight=prefered_block_size,
            employees=employees,
            days=days,
        ),
        MaximizePreferredStationObjective(weights["preferred_station"], employees, days, shifts, stations),
        # MinimizeHiddenEmployeeCountObjective(weights["hidden_count"], employees, days, shifts),
    ]

    model = Model(employees, days, shifts, stations)

    for constraint in constraints:
        model.add_constraint(constraint)

    for objective in objectives:
        model.add_objective(objective)

    if status_callback is not None:
        status_callback("phase_3_optimizing")
    solution = model.solve(timeout, analyzer_log=analyzer_log)
    wid = weight_id if weight_id is not None else "default"
    solution_name = f"solution_{unit}_{start_date}-{end_date}_w{wid}"
    loader.write_solution(solution, solution_name)

    return SolveResult(employees, days, shifts, solution)
