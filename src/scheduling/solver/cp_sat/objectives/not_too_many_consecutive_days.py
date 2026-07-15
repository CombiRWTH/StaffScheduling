from collections import defaultdict
from collections.abc import Mapping
from datetime import date as Date
from datetime import timedelta
from typing import Any, ClassVar

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class NotTooManyConsecutiveDays:
    """
    Adds a penalty to the solver for each consecutive day that an employee works.
    """

    id: ClassVar[str] = "not_too_many_consecutive_days"

    # This seems to be a hard coded variable in the legacy version
    MAX_CONSECUTIVE_DAYS: int = 5

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        # First check which days every employee is assigned to
        days_by_employee: defaultdict[int, list[Date]] = defaultdict(list)
        for key, _variable in ctx.assignment_variables.items():
            employee_id, _, date, _, _ = key
            days_by_employee[employee_id].append(date)

        # Find out how many times an employee works five days or more consecutively
        too_many_consecutive_days: int = 0
        for employee_id in days_by_employee.keys():
            # Make sure the lsit of days is sorted
            days_by_employee[employee_id] = sorted(days_by_employee[employee_id])
            block_length: int = 1
            for i in range(len(days_by_employee[employee_id]) - 1):
                if days_by_employee[employee_id][i + 1] - days_by_employee[employee_id][i] == timedelta(days=1):
                    block_length += 1
                else:
                    if block_length > self.MAX_CONSECUTIVE_DAYS:
                        too_many_consecutive_days += 1
                    block_length = 1

        total_too_many_consecutive_days = ctx.model.new_int_var(
            0, too_many_consecutive_days, "not_too_many_consecutive_days"
        )

        ctx.model.add(total_too_many_consecutive_days == too_many_consecutive_days).with_name(
            "not_too_many_consecutive_days__total_too_many_consecutive_daays"
        )

        return (
            Penalty(
                objective_id=self.id,
                name="total_too_many_consecutive_days",
                expression=total_too_many_consecutive_days,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
