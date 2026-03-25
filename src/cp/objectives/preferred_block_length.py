from collections.abc import Iterable
from typing import cast

from ortools.sat.python.cp_model import CpModel, IntVar, LinearExpr, LiteralT

from src.day import Day
from src.employee import Employee

from ..variables import EmployeeWorksOnDayVariables, ShiftAssignmentVariables
from .objective import Objective


class PreferredBlockLengthObjective(Objective):
    @property
    def KEY(self) -> str:
        return "preferred-block-length"

    def __init__(
        self,
        target_block_length: int,
        max_block_length: int,
        weight: float,
        employees: list[Employee],
        days: list[Day],
    ):
        """
        Encourage consecutive work blocks close to a target length `k`.

        Blocks longer than `max_block_length` fall into a catch-all bucket with a penalty
        corresponding to `max_block_length + 1`.
        """
        super().__init__(weight, employees, days, [])
        self._target_block_length = target_block_length
        self._max_block_length = max_block_length

    def create(
        self,
        model: CpModel,
        shift_assignment_variables: ShiftAssignmentVariables,
        employee_works_on_day_variables: EmployeeWorksOnDayVariables,
    ) -> LinearExpr:
        penalties: list[LinearExpr] = []

        for employee in self._employees:
            for day_index, day in enumerate(self._days):
                start_of_block = model.NewBoolVar(f"start_block_e:{employee.get_key()}_d:{day}")
                today_work = employee_works_on_day_variables[employee][day]
                if day_index == 0:
                    model.Add(start_of_block >= today_work)
                    model.Add(start_of_block <= today_work)
                else:
                    yesterday_work = employee_works_on_day_variables[employee][self._days[day_index - 1]]
                    model.Add(start_of_block <= today_work)
                    model.Add(start_of_block <= 1 - yesterday_work)
                    model.Add(start_of_block >= today_work - yesterday_work)

                block_length_vars: list[tuple[int, LiteralT]] = []
                remaining_days = len(self._days) - day_index
                max_len_here = min(self._max_block_length, remaining_days)

                for length in range(1, max_len_here + 1):
                    block_var = model.NewBoolVar(f"block_len_{length}_e:{employee.get_key()}_d:{day}")
                    block_length_vars.append((length, block_var))

                    model.Add(block_var <= start_of_block)
                    for offset in range(length):
                        model.Add(
                            block_var <= employee_works_on_day_variables[employee][self._days[day_index + offset]]
                        )

                    if day_index + length < len(self._days):
                        model.Add(
                            block_var <= 1 - employee_works_on_day_variables[employee][self._days[day_index + length]]
                        )

                literals_list: Iterable[LiteralT] = [var for _, var in block_length_vars]
                model.add_at_most_one(literals_list)

                unmatched_block = model.NewBoolVar(f"block_unmatched_e:{employee.get_key()}_d:{day}")
                model.Add(sum(cast(IntVar, var) for _, var in block_length_vars) + unmatched_block == start_of_block)

                for length, var in [(len, cast(IntVar, var)) for (len, var) in block_length_vars]:
                    k: int = abs(length - self._target_block_length)
                    penalties.append(k * var)
                penalties.append(
                    abs((self._max_block_length + 1) - self._target_block_length) * unmatched_block,
                )

        return cast(LinearExpr, sum(penalties)) * self._weight
