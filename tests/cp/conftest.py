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
    level="Azubi",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
    planned_shifts=[(1, "N"), (2, "S")],
    target_working_time=960,
)
bob: Employee = Employee(
    key=2,
    surname="B",
    name="Bob",
    level="Fachkraft",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
    planned_shifts=[(1, "N5")],
    target_working_time=1440,
)
carlos: Employee = Employee(
    key=3,
    surname="C",
    name="Carlos",
    level="Fachkraft",
    type="Pflegefachkraft (Krankenpflege) (81302-018)",
    planned_shifts=[(1, "F")],
    qualifications=["rounds"],
    target_working_time=1440,
)
employees: list[Employee] = [alice, bob, carlos]

start_date: Day = datetime(2025, 11, 1)
end_date: Day = datetime(2025, 11, 3)
days: list[Day] = [start_date + timedelta(days=i) for i in range(end_date.day - start_date.day + 1)]

# the base_shifts that are also returned by FSLoader.get_shifts()
shifts: list[Shift] = [
    Shift(Shift.EARLY, "Früh", 360, 820),  # 06:00 – 13:40
    Shift(Shift.INTERMEDIATE, "Zwischen", 480, 940),  # 08:00 – 15:40
    Shift(Shift.LATE, "Spät", 805, 1265),  # 13:25 – 21:05
    Shift(Shift.NIGHT, "Nacht", 1250, 375),  # 20:50 – 06:15 (next day)
    Shift(Shift.MANAGEMENT, "Z60", 480, 840),  # 08:00 – 14:00
    Shift(5, "F2_", 360, 820),  # 06:00 – 13:40
    Shift(6, "S2_", 805, 1265),  # 13:25 – 21:05
    Shift(7, "N5", 1250, 375),  # 20:50 – 06:15 (next day)
]

min_staffing: dict[str, dict[str, dict[str, int]]] = {
    "Azubi": {
        "Mo": {"F": 1, "N": 0, "S": 1},
        "Di": {"F": 1, "N": 0, "S": 1},
        "Do": {"F": 1, "N": 0, "S": 1},
        "Fr": {"F": 1, "N": 0, "S": 1},
        "Mi": {"F": 1, "N": 0, "S": 1},
        "Sa": {"F": 1, "N": 0, "S": 1},
        "So": {"F": 1, "N": 0, "S": 1},
    },
    "Fachkraft": {
        "Di": {"F": 2, "N": 0, "S": 0},
        "Do": {"F": 0, "N": 0, "S": 1},
        "Fr": {"F": 0, "N": 0, "S": 1},
        "Mi": {"F": 0, "N": 0, "S": 0},
        "Mo": {"F": 0, "N": 1, "S": 0},
        "Sa": {"F": 0, "N": 0, "S": 1},
        "So": {"F": 1, "N": 1, "S": 0},
    },
}


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


@pytest.fixture
def setup_with_minstaffing(
    setup: tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift]],
) -> tuple[CpModel, dict[str, IntVar], list[Employee], list[Day], list[Shift], dict[str, dict[str, dict[str, int]]]]:
    global min_staffing
    return *setup, min_staffing
