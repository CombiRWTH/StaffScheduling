from dataclasses import dataclass

from ortools.sat.python import cp_model

from scheduling.domain import SchedulingDataset
from scheduling.solver.cp_sat.index import SolverIndex, build_schedule_index
from scheduling.solver.cp_sat.keys import AssignmentVariableKey


@dataclass(slots=True)
class SolverContext:
    dataset: SchedulingDataset
    index: SolverIndex
    model: cp_model.CpModel
    assignment_variables: dict[AssignmentVariableKey, cp_model.IntVar]
    objective_terms: list[cp_model.LinearExpr]
    diagnostics: list[str]


def create_context(dataset: SchedulingDataset) -> SolverContext:
    """Create the mutable CP-SAT build context for a scheduling dataset."""
    index = build_schedule_index(dataset)

    return SolverContext(
        dataset=dataset,
        index=index,
        model=cp_model.CpModel(),
        assignment_variables={},
        objective_terms=[],
        diagnostics=[],
    )


def add_objective_term(ctx: SolverContext, *, expression: cp_model.LinearExpr, weight: int = 1) -> None:
    """Register one weighted objective term for minimization."""
    if weight == 0:
        return

    ctx.objective_terms.append(expression * weight)
