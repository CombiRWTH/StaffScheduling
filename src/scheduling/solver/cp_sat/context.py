from dataclasses import dataclass

from ortools.sat.python import cp_model

from scheduling.domain import SchedulingDataset
from scheduling.solver.cp_sat.index import SolverIndex, build_schedule_index
from scheduling.solver.cp_sat.keys import AssignmentVariableKey


@dataclass(frozen=True, slots=True)
class ObjectiveTerm:
    name: str
    expression: cp_model.LinearExpr
    weight: int


@dataclass(slots=True)
class SolverContext:
    dataset: SchedulingDataset
    index: SolverIndex
    model: cp_model.CpModel
    assignment_variables: dict[AssignmentVariableKey, cp_model.IntVar]
    objective_terms: list[ObjectiveTerm]
    diagnostics: list[str]


def create_context(dataset: SchedulingDataset) -> SolverContext:
    """Create the mutable CP-SAT build context for a scheduling dataset."""
    index = build_schedule_index(dataset)

    return SolverContext(
        dataset=dataset,
        index=index,
        model=cp_model.CpModel(),
        assignment_variables={},
        diagnostics=[],
        objective_terms=[],
    )
