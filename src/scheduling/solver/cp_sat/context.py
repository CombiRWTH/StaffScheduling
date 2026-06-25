from dataclasses import dataclass

from ortools.sat.python import cp_model

from scheduling.domain import SchedulingDataset
from scheduling.domain.assignment import Assignment
from scheduling.solver.cp_sat.keys import AssignmentVariableKey
from scheduling.solver.diagnostics import SolverDiagnostic
from scheduling.solver.index import SolverIndex, build_schedule_index


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
