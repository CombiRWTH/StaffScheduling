from web import App
from cli import CLIParser
from cp import (
    FreeDayAfterNightShiftPhaseConstraint,
    MinRestTimeConstraint,
    MinStaffingConstraint,
    MaxOneShiftPerDayConstraint,
    TargetWorkingTimeConstraint,
    VacationDaysAndShiftsConstraint,
    FreeDaysNearWeekendObjective,
    MinimizeConsecutiveNightShiftsObjective,
    MinimizeOvertimeObjective,
    NotTooManyConsecutiveDaysObjective,
    RotateShiftsForwardObjective,
    HierarchyOfIntermediateShifts,
)


def main():
    cli = CLIParser(
        [
            FreeDayAfterNightShiftPhaseConstraint,
            MinRestTimeConstraint,
            MinStaffingConstraint,
            MaxOneShiftPerDayConstraint,
            TargetWorkingTimeConstraint,
            VacationDaysAndShiftsConstraint,
            FreeDaysNearWeekendObjective,
            MinimizeConsecutiveNightShiftsObjective,
            MinimizeOvertimeObjective,
            NotTooManyConsecutiveDaysObjective,
            RotateShiftsForwardObjective,
            HierarchyOfIntermediateShifts,
        ]
    )
    case_id = cli.get_case_id()
    start_date = cli.get_start_date()

    app = App(case_id, start_date)
    app.run()


if __name__ == "__main__":
    main()
