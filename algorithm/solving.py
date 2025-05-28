import StateManager
import argparse
import calendar
import json
from datetime import date, timedelta
from functools import partial
from ortools.sat.python import cp_model
from handlers import UnifiedSolutionHandler

from building_constraints.initial_constraints import (
    create_shift_variables,
    create_work_on_days_variables,
    add_basic_constraints,
)
from building_constraints.free_shifts_and_vacation_days import (
    add_free_shifts_and_vacation_days,
)
from building_constraints.minimal_number_of_staff import add_min_number_of_staff
from building_constraints.minimize_number_of_consecutive_night_shifts import (
    add_minimize_number_of_consecutive_night_shifts,
)
from building_constraints.day_no_shift_after_night_shift import (
    add_day_no_shift_after_night_shift,
)
from building_constraints.free_days_near_weekend import (
    add_free_days_near_weekend,
)
from building_constraints.not_too_many_consecutive_shifts import (
    add_not_too_many_consecutive_shifts,
)
from building_constraints.shift_rotate_forward import add_shift_rotate_forward
from building_constraints.minimum_rest_time import add_minimum_rest_time
from building_constraints.intermediate_phase import (
    add_intermediate_shifts_to_solutions,
)

# ─────────────────────────────────────────────────
# ★★ EIN/AUS‑SCHALTER FÜR ALLE CONSTRAINTS ★★
# ─────────────────────────────────────────────────
SWITCH = {
    # Kern‑Regeln
    "basic": True,
    # Business Rules
    "free_shifts": False,
    "min_staff": True,
    "target_working_min": True,
    "min_night_seq": True,
    "no_shift_after_night": True,
    "free_near_weekend": True,
    "max_consecutive": True,
    "rotate_forward": True,
    "wishes_as_hard_constraint": True,
}
#  HIER EINFACH TRUE ↔ FALSE UMSCHALTEN
# ──────────────────────────────────────────
StateManager.state.switch = SWITCH


def load_json(filename):
    with open(filename, "r") as f:
        return json.load(f)


def solve_cp_problem(
    model: cp_model.CpModel,
    handler: cp_model.CpSolverSolutionCallback,
    enumerate_all_solutions: bool,
) -> None:
    """Solve CP model and output basic statistics."""
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = enumerate_all_solutions
    solver.parameters.linearization_level = 0

    solver.SolveWithSolutionCallback(model, handler)

    print("\nStatistics")
    print(f"  - Conflicts     : {solver.num_conflicts}")
    print(f"  - Branches      : {solver.num_branches}")
    print(f"  - Wall time     : {solver.wall_time:.2f}s")
    print(f"  - Solutions found: {handler.solution_count() if handler else 0}")


def add_objective_function(model: cp_model.CpModel, weights: dict):
    """Add weighted soft-constraint penalties to the objective function."""
    objective_terms = StateManager.state.objectives
    weighted_terms = []
    for penalty_var, constraint_name in objective_terms:
        if constraint_name not in weights:
            raise KeyError(f"The weight of `{constraint_name}` is missing.")
        weighted_terms.append(weights[constraint_name] * penalty_var)

    model.Minimize(sum(weighted_terms))


def add_all_constraints(
    model: cp_model.CpModel,
    shifts: dict[tuple, cp_model.IntVar],
    work_on_day: dict[tuple, cp_model.IntVar],
    employees: list[dict],
    case_id: int,
    num_days: int,
    num_shifts: int,
    first_weekday_of_month: int,
    max_consecutive_work_days: int,
) -> None:
    """Add all *enabled* constraints to the model."""

    # Daten laden, die mehrere Regeln benötigen
    free_shifts_data = load_json(
        f"./cases/{case_id}/free_shifts_and_vacation_days.json"
    )
    min_staff_data = load_json(f"./cases/{case_id}/minimal_number_of_staff.json")
    employee_types_data = load_json(f"./cases/{case_id}/employee_types.json")
    target_min_data = load_json(f"./cases/{case_id}/target_working_minutes.json")

    # Mapping: Schlüssel → Callable (0 Args dank partial)
    CONSTRAINTS = {
        # Kern
        "basic": partial(
            add_basic_constraints, model, employees, shifts, num_days, num_shifts
        ),
        # Business‑Regeln
        "free_shifts": partial(
            add_free_shifts_and_vacation_days,
            model,
            employees,
            shifts,
            free_shifts_data,
            num_shifts,
        ),
        "min_staff": partial(
            add_min_number_of_staff,
            model,
            employees,
            shifts,
            min_staff_data,
            employee_types_data,
            first_weekday_of_month,
            num_days,
        ),
        "min_night_seq": partial(
            add_minimize_number_of_consecutive_night_shifts,
            model,
            employees,
            shifts,
            num_days,
        ),
        "no_shift_after_night": partial(
            add_day_no_shift_after_night_shift,
            model,
            employees,
            shifts,
            num_days,
        ),
        "free_near_weekend": partial(
            add_free_days_near_weekend,
            model,
            employees,
            work_on_day,
            num_days,
            start_weekday=first_weekday_of_month,
        ),
        "max_consecutive": partial(
            add_not_too_many_consecutive_shifts,
            model,
            employees,
            work_on_day,
            num_days,
            max_consecutive_work_days,
        ),
        "rotate_forward": partial(
            add_shift_rotate_forward,
            model,
            employees,
            shifts,
            num_days,
        ),
        "no_night_to_early": partial(
            add_minimum_rest_time,
            model,
            employees,
            num_days,
            shifts,
        ),
        "target_working_min": partial(
            add_target_working_minutes,
            model,
            employees,
            shifts,
            num_days,
            num_shifts,
            target_min_data,
            free_shifts_data,
        ),
    }

    # Ausführen, wenn SWITCH[key] == True
    SWITCH = StateManager.state.switch
    for key, func in CONSTRAINTS.items():
        if SWITCH.get(key, True):
            func()


def main():
    parser = argparse.ArgumentParser(
        description="Staff scheduling for a given month and year."
    )
    parser.add_argument(
        "--case_id", "-c", type=int, default=2, help="ID of the cases folder to load"
    )
    parser.add_argument(
        "--month",
        "-m",
        type=int,
        choices=range(1, 13),
        default=11,
        help="Month to plan (1-12)",
    )
    parser.add_argument("--year", "-y", type=int, default=2024, help="Year to plan")
    parser.add_argument(
        "--output",
        "-o",
        nargs="+",
        default=["json"],
        help="Output formats (json, plot, print)",
    )
    parser.add_argument(
        "--switch",
        "-s",
        nargs="+",
        choices=[
            "B",
            "FreeS",
            "Staff",
            "Tar",
            "MinN",
            "NSAN",
            "FreeW",
            "MFNW",
            "MaxC",
            "Rot",
            "Wish",
        ],
        default=None,
        help=(
            "List of Constraints to switch on. Allowed values: "
            "B, FreeS, Staff, Tar, MinN, NSAN, FreeW, MFNW, MaxC, Rot, Wish"
        ),
    )
    args = parser.parse_args()

    if args.switch is not None:
        constraints_short_to_long = {
            "B": "basic",
            "FreeS": "free_shifts",
            "Staff": "min_staff",
            "Tar": "target_working_min",
            "MinN": "min_night_seq",
            "NSAN": "no_shift_after_night",
            "FreeW": "free_near_weekend",
            "MaxC": "max_consecutive",
            "Rot": "rotate_forward",
            "Wish": "wishes_as_hard_constraint",
        }
        NEW_SWITCH = {key: False for key in SWITCH.keys()}
        for c_short in args.switch:
            NEW_SWITCH[constraints_short_to_long[c_short]] = True
        StateManager.state.switch = NEW_SWITCH

    # Parameter
    SOLUTION_DIR = "found_solutions"
    NUM_SHIFTS = 3
    SOLUTION_LIMIT = 10
    MAX_CONSECUTIVE_WORK_DAYS = 5

    year = args.year
    month = args.month
    start_date = date(year, month, 1)
    NUM_DAYS = calendar.monthrange(year, month)[1]
    first_weekday_idx_of_month = start_date.weekday()

    dates = [start_date + timedelta(days=i) for i in range(NUM_DAYS)]

    # Modell aufbauen
    model = cp_model.CpModel()
    employees = load_json(f"./cases/{args.case_id}/employees.json")["employees"]

    shifts = create_shift_variables(model, employees, NUM_DAYS, NUM_SHIFTS)
    work_on_day = create_work_on_days_variables(
        model, employees, NUM_DAYS, NUM_SHIFTS, shifts
    )
    # Get shift_durations From targetworkingminutes.json
    shift_durations = {}
    try:
        shift_durations = load_json(
            f"./cases/{args.case_id}/target_working_minutes.json"
        )["shift_durations"]
    except FileNotFoundError:
        print("Warning: target_working_minutes.json not found.")
    add_all_constraints(
        model=model,
        shifts=shifts,
        work_on_day=work_on_day,
        employees=employees,
        case_id=args.case_id,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
        first_weekday_of_month=first_weekday_idx_of_month,
        max_consecutive_work_days=MAX_CONSECUTIVE_WORK_DAYS,
    )

    unified = UnifiedSolutionHandler(
        shifts=shifts,
        employees=employees,
        num_days=NUM_DAYS,
        num_shifts=NUM_SHIFTS,
        dates=dates,
        limit=SOLUTION_LIMIT,
        case_id=args.case_id,
        shift_durations=shift_durations,
        solution_dir=SOLUTION_DIR,
    )

    # Objective
    if StateManager.state.objectives:
        weights = {
            "Shifts rotate fowards": 1,
            "Not to long shifts": 1,
            "Minimize number of consecutive night shifts": 1,
            "free day near weekend": 1,
            "Not too many Consecutive Shifts": 1,
        }
        add_objective_function(model, weights)
        enumerate_all_solutions = False
    else:
        print("No objective function.")
        enumerate_all_solutions = True

    solve_cp_problem(model, unified, enumerate_all_solutions)

    # ──────────────────────────────────────────────────────────
    # Phase 2 – insert intermediate shifts (Z)
    # ──────────────────────────────────────────────────────────
    unified._solutions = add_intermediate_shifts_to_solutions(
        unified._solutions,
        employees,
        dates,
        args.case_id,
    )

    # Output
    if "json" in args.output:
        unified.json()
    if "print" in args.output:
        unified.print()
    if "plot" in args.output:
        unified.plot()


if __name__ == "__main__":
    main()
