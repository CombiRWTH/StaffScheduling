from cp.constraints import FreeDayAfterNightShiftPhaseConstraint
from cp.variables import Variable, EmployeeDayShiftVariable, EmployeeDayVariable
from employee import Employee
from datetime import datetime, timedelta
from day import Day
from shift import Shift
from ortools.sat.python.cp_model import CpModel, CpSolver
from pprint import pprint

alice: Employee = Employee(
    key=1,
    surname="A",
    name="Alice",
    level="Fachkraft",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
)
bob: Employee = Employee(
    key=21,
    surname="B",
    name="Bob",
    level="Fachkraft",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
)
carlos: Employee = Employee(
    key=3,
    surname="C",
    name="Carlos",
    level="Fachkraft",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
)
employees: list[Employee] = [alice, bob, carlos]

start_date: Day = datetime(2025, 11, 1)
end_date: Day = datetime(2025, 11, 30)
days: list[Day] = [
    start_date + timedelta(days=i) for i in range(end_date.day - start_date.day + 1)
]

# the base_shifts that are also returned by FSLoader.get_shifts()
shifts: list[Shift] = [
    Shift(Shift.EARLY, "Früh", 360, 820),
    Shift(Shift.INTERMEDIATE, "Zwischen", 480, 940),
    Shift(Shift.LATE, "Spät", 805, 1265),
    Shift(Shift.NIGHT, "Nacht", 1250, 375),
    Shift(Shift.MANAGEMENT, "Z60", 480, 840),
    Shift(5, "F2_", 360, 820),
    Shift(6, "S2_", 805, 1265),
    Shift(7, "N5", 1250, 375),
]

model: CpModel = CpModel()

variables_list: list[Variable]
variables_dict: dict[str, Variable]


def setup():
    global model
    global variables_list
    global variables_dict

    model = CpModel()

    # here the order of the variables in the list is very important
    variables_list = [
        EmployeeDayShiftVariable(employees, days, shifts),
        EmployeeDayVariable(employees, days, shifts),
    ]
    variables_dict = {}
    for vars in variables_list:
        vars = vars.create(model, variables_dict)
        for var in vars:
            variables_dict[var.name] = var


def find_free_day_after_night_shift_phase_violations(solver) -> list[dict[str, int]]:
    global variables_dict
    global employees
    global days
    global shifts

    var_solution_dict: dict[str, int] = {
        variable.name: solver.value(variable) for variable in variables_dict.values()
    }
    violations: list[dict[str, int]] = []

    for employee in employees:
        for day in days[:-1]:
            current_day_night_shift: int = var_solution_dict[
                EmployeeDayShiftVariable.get_key(employee, day, shifts[Shift.NIGHT])
            ]
            next_day_night_shift: int = var_solution_dict[
                EmployeeDayShiftVariable.get_key(
                    employee, day + timedelta(1), shifts[Shift.NIGHT]
                )
            ]
            next_day_any_shifts: int = var_solution_dict[
                EmployeeDayVariable.get_key(employee, day + timedelta(1))
            ]
            if (
                current_day_night_shift
                and not next_day_night_shift
                and next_day_any_shifts
            ):
                d: dict[str, int] = {}
                d[
                    EmployeeDayShiftVariable.get_key(employee, day, shifts[Shift.NIGHT])
                ] = current_day_night_shift
                d[
                    EmployeeDayShiftVariable.get_key(
                        employee, day + timedelta(1), shifts[Shift.NIGHT]
                    )
                ] = next_day_night_shift
                d[EmployeeDayVariable.get_key(employee, day + timedelta(1))] = (
                    next_day_any_shifts
                )
                violations.append(d)

    return violations


def test_free_day_after_night_shift_phase_1():
    setup()
    constrain: FreeDayAfterNightShiftPhaseConstraint = (
        FreeDayAfterNightShiftPhaseConstraint(employees, days, shifts)
    )
    constrain.create(model, variables_dict)

    solver = CpSolver()
    solver.parameters.num_workers = 1
    solver.parameters.max_time_in_seconds = 10
    solver.parameters.linearization_level = 0
    solver.solve(model)

    violations = find_free_day_after_night_shift_phase_violations(solver)
    assert len(violations) == 0, pprint(violations, width=1)
