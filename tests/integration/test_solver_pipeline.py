import pytest

from src.solve import main as run_solver
from tests.integration.helpers.solution_assertions import (
    active_shift_assignments,
    assert_min_staffing_is_covered,
    assert_no_exclusive_shift_assigned,
    assert_no_more_than_one_shift_per_employee_day,
    assert_only_known_employees_assigned,
    assert_solution_found,
    assert_unavailable_employees_not_assigned,
)
from tests.integration.helpers.solver_fixtures import (
    TEST_SOLVER_WEIGHTS,
    CleanSolverFixture,
    make_one_week_two_level_reference_fixture,
    make_two_day_fachkraft_early_fixture,
)


def inject_fixture_at_solver_loader_boundary(
    monkeypatch: pytest.MonkeyPatch,
    fixture: CleanSolverFixture,
) -> None:
    """Inject clean test data while keeping the real solver/model path."""
    monkeypatch.setattr("src.solve.FSLoader.get_days", lambda self, start_date, end_date: fixture.days)
    monkeypatch.setattr("src.solve.FSLoader.get_shifts", lambda self: fixture.shifts)
    monkeypatch.setattr("src.solve.FSLoader.get_min_staffing", lambda self: fixture.min_staffing)
    monkeypatch.setattr("src.solve.FSLoader.write_solution", lambda self, solution, solution_name: None)


@pytest.mark.integration
def test_two_day_fachkraft_early_fixture_solves_successfully(monkeypatch: pytest.MonkeyPatch) -> None:
    fixture = make_two_day_fachkraft_early_fixture()
    inject_fixture_at_solver_loader_boundary(monkeypatch, fixture)

    result = run_solver(
        unit=fixture.unit,
        start_date=fixture.start_date,
        end_date=fixture.end_date,
        timeout=10,
        employees=fixture.employees,
        weights=TEST_SOLVER_WEIGHTS,
    )

    assert_solution_found(result.solution.status_name)

    assignments = active_shift_assignments(result.solution.variables)

    assert_only_known_employees_assigned(assignments, fixture.employees)
    assert_no_more_than_one_shift_per_employee_day(assignments)
    assert_min_staffing_is_covered(
        assignments=assignments,
        employees=fixture.employees,
        shifts=fixture.shifts,
        days=fixture.days,
        min_staffing=fixture.min_staffing,
    )


@pytest.mark.integration
def test_one_week_two_level_reference_fixture_satisfies_basic_invariants(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_one_week_two_level_reference_fixture()
    inject_fixture_at_solver_loader_boundary(monkeypatch, fixture)

    result = run_solver(
        unit=fixture.unit,
        start_date=fixture.start_date,
        end_date=fixture.end_date,
        timeout=10,
        employees=fixture.employees,
        weights=TEST_SOLVER_WEIGHTS,
    )

    assert_solution_found(result.solution.status_name)

    assignments = active_shift_assignments(result.solution.variables)

    assert_only_known_employees_assigned(assignments, fixture.employees)
    assert_no_more_than_one_shift_per_employee_day(assignments)
    assert_unavailable_employees_not_assigned(assignments, fixture.employees)
    assert_no_exclusive_shift_assigned(assignments, fixture.shifts)
    assert_min_staffing_is_covered(
        assignments=assignments,
        employees=fixture.employees,
        shifts=fixture.shifts,
        days=fixture.days,
        min_staffing=fixture.min_staffing,
    )
