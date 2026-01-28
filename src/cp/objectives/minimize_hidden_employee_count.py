from typing import cast

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntVar, LinearExpr

from src.day import Day
from src.employee import Employee
from src.shift import Shift

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class MinimizeHiddenEmployeeCountObjective(Objective):
    @property
    def KEY(self) -> str:
        return "minimize-hidden-employees"

    def __init__(
        self,
        weight: float,
        employees: list[Employee],
        days: list[Day],
        shifts: list[Shift],
    ):
        """
        Initializes the objective to minimize overtime for employees.
        Overtime is calculated as the difference between the total working time and the target working time.
        """
        super().__init__(weight, employees, days, shifts)

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        hidden_vars: list[IntVar] = []

        for employee in self._employees:
            if not employee.hidden:
                continue

            vars: list[BoolVarT] = []
            for day in self._days:
                for shift in self._shifts:
                    var = shift_assignment_variables[employee][day][shift]
                    vars += [var]

            true_if_not_working = model.new_bool_var(f"hidden_e_is_working:{employee.get_key()}")
            model.AddBoolOr(vars + [true_if_not_working])

            hidden_vars.append(true_if_not_working)

        return cast(LinearExpr, sum(hidden_vars)) * (-1) * self._weight
