from typing import Any

import pytest

from legacy.src.services.solve_service import execute_solve
from tests.integration.helpers.smoke_fixtures import SMOKE_TEST_WEIGHTS, SmokeSolveFixture, make_smoke_solve_fixture


def inject_smoke_fixture(
    monkeypatch: pytest.MonkeyPatch,
    fixture: SmokeSolveFixture,
) -> None:
    """Replace data loading with fixed sanitized data."""
    monkeypatch.setattr("src.solve.FSLoader.get_days", lambda self, start_date, end_date: fixture.days)
    monkeypatch.setattr("src.solve.FSLoader.get_shifts", lambda self: fixture.shifts)
    monkeypatch.setattr("src.solve.FSLoader.get_employees", lambda self, start=0: fixture.employees)
    monkeypatch.setattr("src.solve.FSLoader.get_min_staffing", lambda self: fixture.min_staffing)
    monkeypatch.setattr("src.solve.FSLoader.write_solution", lambda self, solution, solution_name: None)

    monkeypatch.setattr(
        "src.services.solve_service.load_weights",
        lambda unit, start_date: SMOKE_TEST_WEIGHTS,
    )


@pytest.mark.integration
def test_solve_service_generates_output_for_clean_smoke_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = make_smoke_solve_fixture()
    inject_smoke_fixture(monkeypatch, fixture)

    generated_outputs: list[dict[str, Any]] = []

    def fake_process_solution(
        *,
        loader: Any,
        employees: Any,
        output_filename: str,
        solution_file_name: str,
    ) -> dict[str, Any]:
        generated_outputs.append(
            {
                "output_filename": output_filename,
                "solution_file_name": solution_file_name,
                "employee_count": len(employees),
            }
        )
        return {"generated": True}

    monkeypatch.setattr("src.services.solve_service.process_solution", fake_process_solution)

    result = execute_solve(
        unit=fixture.unit,
        start_date=fixture.start_date,
        end_date=fixture.end_date,
        timeout=10,
    )

    assert result["status"] in {"FEASIBLE", "OPTIMAL"}
    assert result["solution_data"] == {"generated": True}
    assert len(generated_outputs) == 1
