from datetime import timedelta
from pprint import pformat
from typing import cast

from ortools.sat.python.cp_model import CpSolver, IntVar

from src.cp.constraints import FreeDayAfterNightShiftPhaseConstraint
from src.cp.model import Model
from src.cp.variables import Variable
from src.shift import Shift


def find_free_day_after_night_shift_phase_violations(
    assignment: dict[Variable, int], model: Model
) -> list[dict[str, int]]:
    shift_assignment_variables = model.shift_assignment_variables
    employees = model.employees
    days = model.days
    shifts = model.shifts

    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in days[:-1]:
            current_day_night_shift = shift_assignment_variables[employee][day][shifts[Shift.NIGHT]]
            current_day_night_shift_special = shift_assignment_variables[employee][day][shifts[7]]

            next_day_night_shift = shift_assignment_variables[employee][day + timedelta(1)][shifts[Shift.NIGHT]]
            next_day_night_shift_special = shift_assignment_variables[employee][day + timedelta(1)][shifts[7]]

            if (assignment[current_day_night_shift] or assignment[current_day_night_shift_special]) and not (
                assignment[next_day_night_shift] or assignment[next_day_night_shift_special]
            ):
                shift_vars_keys_next_day: list[Variable] = []
                for shift in [shift for shift in shifts if shift.id != 7 and shift.id != Shift.NIGHT]:
                    shift_vars_keys_next_day.append(shift_assignment_variables[employee][day + timedelta(1)][shift])

                if max([assignment[var] for var in shift_vars_keys_next_day]) >= 1:
                    d: dict[str, int] = {
                        cast(IntVar, current_day_night_shift).name: assignment[current_day_night_shift],
                        cast(IntVar, current_day_night_shift_special).name: assignment[current_day_night_shift_special],
                        cast(IntVar, next_day_night_shift).name: assignment[next_day_night_shift],
                        cast(IntVar, next_day_night_shift_special).name: assignment[next_day_night_shift_special],
                    }
                    d = d | {cast(IntVar, var).name: assignment[var] for var in shift_vars_keys_next_day}
                    violations.append(d)

    return violations


def test_free_day_after_night_shift_phase_1(setup: Model):
    model = setup

    constrain = FreeDayAfterNightShiftPhaseConstraint(model.employees, model.days, model.shifts)
    model.add_constraint(constrain)

    solver: CpSolver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model.cpModel)

    assignment = {var: solver.Value(var) for var in model.variables}

    violations = find_free_day_after_night_shift_phase_violations(assignment, model)
    if CpSolver.StatusName(solver) == "INFEASIBLE":
        raise Exception("There is no feasible solution and thus this test is pointless")
    else:
        assert len(violations) == 0, "\n\n There were violations: \n" + pformat(violations, width=1) + "\n"
