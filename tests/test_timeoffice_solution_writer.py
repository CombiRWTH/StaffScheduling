import json
from datetime import date
from pathlib import Path

from scheduling.domain import (
    Assignment,
    AssignmentType,
    Employee,
    PlanningMonth,
    PlanningUnit,
    PlanningUnitType,
    SchedulingDataset,
    Shift,
    ShiftType,
    StaffingDemandRole,
    StaffLevel,
)
from scheduling.solver.models import Solution, SolutionStatus
from scheduling.timeoffice.facts import EARLY_SHIFT_ID, LATE_SHIFT_ID
from scheduling.timeoffice.writing.solution import TimeOfficeSolutionWriter, build_legacy_solution_data


def test_build_legacy_solution_data_uses_dense_legacy_variable_format() -> None:
    dataset = _dataset()
    solution = Solution(
        status=SolutionStatus.OPTIMAL,
        assignments=(
            Assignment(
                employee_id=102,
                planning_unit_id=77,
                date=date(2024, 11, 2),
                shift_id=LATE_SHIFT_ID,
                assignment_type=AssignmentType.GENERATED,
            ),
        ),
    )

    data = build_legacy_solution_data(dataset=dataset, solution=solution)

    assert data["objective"] == 0.0
    assert len(data["variables"]) == 2 * 30 * 9
    assert data["variables"]["(101, '2024-11-01', 0)"] == 1
    assert data["variables"]["(102, '2024-11-02', 2)"] == 1
    assert data["variables"]["(102, '2024-11-02', 0)"] == 0
    assert data["variables"]["(102, '2024-11-02', 7)"] == 0
    assert data["variables"]["e:101_d:2024-11-01"] == 1
    assert data["variables"]["e:101_d:2024-11-02"] == 0
    assert data["variables"]["e:102_d:2024-11-02"] == 1
    assert f"(102, '2024-11-02', {LATE_SHIFT_ID})" not in data["variables"]


def test_write_legacy_format_writes_legacy_solution_json(tmp_path: Path) -> None:
    writer = TimeOfficeSolutionWriter(
        legacy_solution_dir=tmp_path / "found_solutions",
        processed_solution_dir=tmp_path / "processed_solutions",
    )
    solution = Solution(status=SolutionStatus.FEASIBLE)

    output_paths = writer.write_legacy_format(
        dataset=_dataset(),
        solution=solution,
        solution_name="solution_77_2024-11-01-2024-11-30_wdefault",
    )

    assert output_paths is not None
    assert output_paths.solution_path == (
        tmp_path / "found_solutions" / "solution_77_2024-11-01-2024-11-30_wdefault.json"
    )
    assert output_paths.processed_solution_path == (
        tmp_path / "processed_solutions" / "solution_77_2024-11-01-2024-11-30_wdefault_processed.json"
    )
    with output_paths.solution_path.open() as file:
        solution_data = json.load(file)

    with output_paths.processed_solution_path.open() as file:
        processed_data = json.load(file)

    assert solution_data == processed_data
    assert list(solution_data) == [
        "solution_file_names",
        "selected_solution_file_name",
        "employees",
        "days",
        "shifts",
        "stats",
        "fulfilled_shift_wish_cells",
        "fulfilled_day_off_cells",
        "all_shift_wish_colors",
        "all_day_off_wish_cells",
        "variables",
    ]
    assert solution_data["selected_solution_file_name"] == "solution_77_2024-11-01-2024-11-30_wdefault"
    assert solution_data["variables"]["(101, '2024-11-01', 0)"] == 1
    assert len(solution_data["employees"]) == 2
    assert len(solution_data["days"]) == 30
    assert len(solution_data["shifts"]) == 8


def _dataset() -> SchedulingDataset:
    return SchedulingDataset(
        planning_month=PlanningMonth(year=2024, month=11),
        planning_units=(
            PlanningUnit(
                planning_unit_id=77,
                display_name="Station 77",
                type=PlanningUnitType.STATION,
            ),
        ),
        plans=(),
        shifts=(
            Shift(
                shift_id=EARLY_SHIFT_ID,
                code="F",
                type=ShiftType.EARLY,
                staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
                start_minute=360,
                end_minute=820,
                net_work_minutes=460,
            ),
            Shift(
                shift_id=LATE_SHIFT_ID,
                code="S",
                type=ShiftType.LATE,
                staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
                start_minute=805,
                end_minute=1265,
                net_work_minutes=460,
            ),
        ),
        employees=(
            Employee(
                employee_id=101,
                display_name="Alice",
                staff_level=StaffLevel.PROFESSIONAL,
            ),
            Employee(
                employee_id=102,
                display_name="Bob",
                staff_level=StaffLevel.PROFESSIONAL,
            ),
        ),
        assignments=(
            Assignment(
                employee_id=101,
                planning_unit_id=77,
                date=date(2024, 11, 1),
                shift_id=EARLY_SHIFT_ID,
                assignment_type=AssignmentType.PLANNED,
            ),
        ),
    )
