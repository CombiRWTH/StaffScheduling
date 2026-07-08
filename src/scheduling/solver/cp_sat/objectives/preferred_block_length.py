from datetime import date, timedelta
from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from ortools.sat.python import cp_model

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class PreferredBlockLength:
    """
    Adds a reward for each time an employee works exactly three days in a row.
    """

    id: ClassVar[str] = "preferred_block_length"

    #This seems to be a hard coded variable in the legacy version
    PREFERRED_BLOCK_LENGTH: int = 3

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        #First check which days every employee is assigned to
        days_by_employee: defaultdict[int, date] = defaultdict(list)
        for key, variable in ctx.assignment_variables.items():
            employee_id, _, date, _, _ = key
            days_by_employee[employee_id].append(date)
        
        #Find out how many times an employee works exactly three days consecutively
        num_preferred_blocks: int = 0
        for employee_id in days_by_employee.keys():
            #Make sure the lsit of days is sorted
            days_by_employee[employee_id] = sorted(days_by_employee[employee_id])
            block_length: int = 1
            for i in range(len(days_by_employee[employee_id]) - 1):
                if days_by_employee[employee_id][i+1] - days_by_employee[employee_id][i] == timedelta(days=1):
                    block_length += 1
                else:
                    if block_length == self.PREFERRED_BLOCK_LENGTH:
                        num_preferred_blocks +=1
                    block_length = 1

                    

        total_preferred_blocks = ctx.model.new_int_var(
            0,
            num_preferred_blocks,
            "total_preferred_blocks"
        )

        ctx.model.add(total_preferred_blocks == num_preferred_blocks).with_name("preferred_block_length__total_preferred_blocks")

        return (
            Penalty(
                objective_id=self.id,
                name="total_preferred_blocks",
                expression=total_preferred_blocks,
                multiplier=-1 #This should make sure that this objective gives a reward instead of a penalty
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
