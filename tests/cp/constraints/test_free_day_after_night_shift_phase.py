from datetime import timedelta
from pprint import pformat, pprint
from typing import cast

from ortools.sat.python.cp_model import CpModel, CpSolver, IntVar

from src.cp.constraints import FreeDayAfterNightShiftPhaseConstraint
from src.cp.variables import EmployeeDayShiftVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift


def find_free_day_after_night_shift_phase_violations(
    solver: CpSolver, variables_dict: dict[str, IntVar], employees: list[Employee], days: list[Day], shifts: list[Shift]
) -> list[dict[str, int]]:
    var_solution_dict: dict[str, int] = {variable.name: solver.value(variable) for variable in variables_dict.values()}
    print("\n")
    pprint(var_solution_dict)
    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in days[:-1]:
            current_day_night_shift = EmployeeDayShiftVariable.get_key(employee, day, shifts[Shift.NIGHT])
            current_day_night_shift_special = EmployeeDayShiftVariable.get_key(employee, day, shifts[7])

            next_day_night_shift = EmployeeDayShiftVariable.get_key(employee, day + timedelta(1), shifts[Shift.NIGHT])
            next_day_night_shift_special = EmployeeDayShiftVariable.get_key(employee, day + timedelta(1), shifts[7])

            if (
                var_solution_dict[current_day_night_shift] or var_solution_dict[current_day_night_shift_special]
            ) and not (var_solution_dict[next_day_night_shift] or var_solution_dict[next_day_night_shift_special]):
                # next day should be off

                # extract the variables for all other shifts on the next day
                shift_vars_keys_next_day: list[str] = []
                for shift in [shift for shift in shifts if shift.id != 7 and shift.id != Shift.NIGHT]:
                    shift_vars_keys_next_day.append(
                        EmployeeDayShiftVariable.get_key(employee, day + timedelta(1), shift)
                    )

                if max([var_solution_dict[key] for key in shift_vars_keys_next_day]) >= 1:
                    # next day is not off
                    d: dict[str, int] = {
                        current_day_night_shift: var_solution_dict[current_day_night_shift],
                        current_day_night_shift_special: var_solution_dict[current_day_night_shift_special],
                        next_day_night_shift: var_solution_dict[next_day_night_shift],
                        next_day_night_shift_special: var_solution_dict[next_day_night_shift_special],
                    }
                    d = d | {key: var_solution_dict[key] for key in shift_vars_keys_next_day}
                    violations.append(d)

    return violations


def test_free_day_after_night_shift_phase_1(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
):
    model: CpModel
    variables_dict: dict[str, IntVar] = {}
    employees: list[Employee] = []
    days: list[Day] = []
    shifts: list[Shift] = []
    model, variables_dict, employees, days, shifts = setup

    constrain = FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts)
    constrain.create(model, cast(dict[str, Variable], variables_dict))

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_free_day_after_night_shift_phase_violations(solver, variables_dict, employees, days, shifts)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("\nThere is no feasible solution and thus this test is pointless\n")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
