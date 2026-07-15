from collections import defaultdict
from collections.abc import Mapping
from typing import Any, ClassVar

from scheduling.domain.planning_unit import PlanningUnitId
from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.cp_sat.objective import Penalty


class PreferOwnPlanningUnit:
    """
    Adds a penalty every time an employee is assigned to the planning unit that is not his
    preferred planning unit.
    """

    id: ClassVar[str] = "prefer_own_planning_unit"

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[Penalty, ...]:
        if not ctx.assignment_variables:
            return ()

        # Dictionary with employee as key and planning unit
        employees_PU_dict: defaultdict[int, PlanningUnitId] = defaultdict(list)
        # First assign a planning unit to every employee, read from the dataset
        for membership in ctx.dataset.planning_unit_memberships:
            employee_id = membership.employee_id
            planning_unit_id = membership.planning_unit_id

        # Then find out the id of any shared pool stations
        # shared_pool_type = PlanningUnitType("shared_pool")
        shared_pool_ids: list[PlanningUnitId] = list[PlanningUnitId]()
        for pu in ctx.dataset.planning_units:
            if pu.planning_unit_id in shared_pool_ids:
                shared_pool_ids.append(pu.planning_unit_id)

        # Now check in the assignments whether an employee (who is not in the shared pool!!!)
        # was assigned to a planning unit that is not his own
        num_not_preferred_planning_unit: int = 0
        for key, _variable in ctx.assignment_variables.items():
            employee_id, planning_unit_id, _, _, _ = key
            if (
                employees_PU_dict[employee_id] != planning_unit_id
                and employees_PU_dict[employee_id] not in shared_pool_ids
            ):
                num_not_preferred_planning_unit += 1

        prefer_own_planning_unit_penalty = ctx.model.new_int_var(0, 100000, "not_preferred_planning_unit")

        ctx.model.add(prefer_own_planning_unit_penalty == num_not_preferred_planning_unit).with_name(
            "prefer_own_planning_unit__penalty"
        )

        return (
            Penalty(
                objective_id=self.id,
                name="prefer_own_planning_unit_penalty",
                expression=prefer_own_planning_unit_penalty,
            ),
        )

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]:
        return ()
