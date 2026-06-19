from scheduling.domain.dataset import SchedulingDataset
from scheduling.solver.tmp import SolverResult


class SolverService:
    """Thin solver boundary.

    Currently fake. Later this class can delegate to OR-Tools without changing
    the API integration contract.
    """

    def solve(self, dataset: SchedulingDataset) -> SolverResult:
        return SolverResult(
            status="succeeded",
            message=(
                "Fake solve completed for "
                f"{len(dataset.employees)} employees, "
                f"{len(dataset.planning_units)} planning units, "
                f"{len(dataset.demand_requirements)} demand requirements."
            ),
            assignments_created=0,
        )
