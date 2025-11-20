from datetime import datetime, timedelta

import pytest
from ortools.sat.python.cp_model import CpModel, IntVar

from src.cp.variables import EmployeeDayShiftVariable, EmployeeDayVariable, Variable
from src.day import Day
from src.employee import Employee
from src.shift import Shift

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
days: list[Day] = [start_date + timedelta(days=i) for i in range(end_date.day - start_date.day + 1)]

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


@pytest.fixture
def setup() -> tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]]:
    global employees
    global days
    global shifts

    model: CpModel = CpModel()
    variables_list: list[Variable] = []
    variables_dict: dict[str, IntVar] = {}

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

    return model, variables_dict, employees, days, shifts
