from dataclasses import dataclass

from ortools.sat.python import cp_model

from app.domain import SchedulingDataset
from app.domain.assignment import Assignment
from app.solver.cp_sat.keys import AssignmentVariableKey
from app.solver.diagnostics import SolverDiagnostic
from app.solver.index import SolverIndex, build_schedule_index


@dataclass(slots=True)
class SolverContext:
    dataset: SchedulingDataset
    index: SolverIndex
    model: cp_model.CpModel
    assignment_variables: dict[AssignmentVariableKey, cp_model.IntVar]
    diagnostics: list[SolverDiagnostic]


def create_context(dataset: SchedulingDataset) -> SolverContext:
    """Create the mutable CP-SAT build context for a scheduling dataset."""
    index = build_schedule_index(dataset)

    return SolverContext(
        dataset=dataset,
        index=index,
        model=cp_model.CpModel(),
        assignment_variables={},
        diagnostics=[],
    )


@dataclass(frozen=True, slots=True)
class AuditContext:
    """Post-solve context passed to constraints and objectives for audit."""

    dataset: SchedulingDataset
    index: SolverIndex
    assignments: tuple[Assignment, ...]
