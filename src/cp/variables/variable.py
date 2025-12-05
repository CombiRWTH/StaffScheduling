from ortools.sat.python.cp_model import BoolVarT, CpModel

from src.day import Day
from src.employee import Employee
from src.shift import Shift

type Variable = BoolVarT


class ShiftAssignmentVariables:
    """A dictionary wrapper that allows indexing with Employee, Day, and Shift objects.

    Usage: shift_dict[employee][day][shift] -> Variable
    """

    def __init__(self, internal_dict: dict[int, dict[Day, dict[int, Variable]]]):
        self._data = internal_dict

    def __getitem__(self, employee: Employee) -> "DayShiftDict":
        return DayShiftDict(self._data[employee.get_key()])

    def __len__(self) -> int:
        count = 0
        for day_dict in self._data.values():
            for shift_dict in day_dict.values():
                count += len(shift_dict)
        return count


class DayShiftDict:
    """Intermediate dictionary for Day -> Shift -> Variable mapping."""

    def __init__(self, day_dict: dict[Day, dict[int, Variable]]):
        self._data = day_dict

    def __getitem__(self, day: Day) -> "ShiftDict":
        return ShiftDict(self._data[day])


class ShiftDict:
    """Final dictionary for Shift -> Variable mapping."""

    def __init__(self, shift_dict: dict[int, Variable]):
        self._data = shift_dict

    def __getitem__(self, shift: Shift) -> Variable:
        return self._data[shift.get_id()]


class EmployeeWorksOnDayVariables:
    """A dictionary wrapper that allows indexing with Employee and Day objects.

    Usage: works_dict[employee][day] -> Variable
    """

    def __init__(self, internal_dict: dict[int, dict[Day, Variable]]):
        self._data = internal_dict

    def __getitem__(self, employee: Employee) -> "DayVariableDict":
        return DayVariableDict(self._data[employee.get_key()])

    def __len__(self) -> int:
        count = 0
        for day_dict in self._data.values():
            count += len(day_dict)
        return count


class DayVariableDict:
    """Dictionary for Day -> Variable mapping."""

    def __init__(self, day_dict: dict[Day, Variable]):
        self._data = day_dict

    def __getitem__(self, day: Day) -> Variable:
        return self._data[day]


def create_shift_assignment_variables(
    employees: list[Employee], days: list[Day], shifts: list[Shift], model: CpModel
) -> ShiftAssignmentVariables:
    vars: dict[int, dict[Day, dict[int, Variable]]] = {}
    for employee in employees:
        e_key = employee.get_key()
        vars[e_key] = {}
        for day in days:
            vars[e_key][day] = {}
            for shift in shifts:
                vars[e_key][day][shift.get_id()] = model.new_bool_var(
                    f"({e_key}, '{day.strftime('%Y-%m-%d')}', {shift.get_id()})"
                )
    return ShiftAssignmentVariables(vars)


def create_employee_works_on_day_variables(
    employees: list[Employee], days: list[Day], model: CpModel
) -> EmployeeWorksOnDayVariables:
    vars: dict[int, dict[Day, Variable]] = {}
    for employee in employees:
        e_key = employee.get_key()
        vars[e_key] = {}
        for day in days:
            vars[e_key][day] = model.new_bool_var(f"e:{e_key}_d:{day}")
    return EmployeeWorksOnDayVariables(vars)


def setup_employee_works_on_day_variables(
    shift_assignment_vars: ShiftAssignmentVariables,
    employee_works_on_day_vars: EmployeeWorksOnDayVariables,
    employees: list[Employee],
    days: list[Day],
    shifts: list[Shift],
    model: CpModel,
) -> None:
    for employee in employees:
        for day in days:
            model.add_max_equality(
                employee_works_on_day_vars[employee][day],
                [shift_assignment_vars[employee][day][shift] for shift in shifts],
            )
