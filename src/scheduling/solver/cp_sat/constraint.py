from collections.abc import Mapping
from typing import Any, ClassVar, Protocol

from scheduling.solver.audit import AuditFinding
from scheduling.solver.cp_sat.context import AuditContext, SolverContext
from scheduling.solver.diagnostics import SolverDiagnostic


class Constraint(Protocol):
    """Hard CP-SAT model component.

    Constraints define what schedules are allowed. They may be configurable via
    params, but they do not have weights.
    """

    id: ClassVar[str]
    required: ClassVar[bool]

    def add_to_model(
        self,
        ctx: SolverContext,
        params: Mapping[str, Any],
    ) -> tuple[SolverDiagnostic, ...]: ...

    def audit(
        self,
        ctx: AuditContext,
        params: Mapping[str, Any],
    ) -> tuple[AuditFinding, ...]: ...
