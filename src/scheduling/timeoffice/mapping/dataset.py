from scheduling.domain import PlanningMonth, SchedulingDataset
from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.mapping.demand import map_demand_requirements
from scheduling.timeoffice.mapping.personnel import map_employees, map_planning_unit_memberships
from scheduling.timeoffice.mapping.planning import map_planning_units, map_plans
from scheduling.timeoffice.mapping.roster import map_assignments, map_availability
from scheduling.timeoffice.mapping.shifts import map_shifts
from scheduling.timeoffice.mapping.sunday_work import map_sunday_work_history
from scheduling.timeoffice.mapping.wishes import map_wishes
from scheduling.timeoffice.mapping.work_accounts import map_monthly_work_accounts
from scheduling.timeoffice.reading.container import TimeOfficeSources


def map_scheduling_dataset(
    *,
    sources: TimeOfficeSources,
    facts: TimeOfficeFacts,
    planning_month: PlanningMonth,
) -> SchedulingDataset:
    planning_units = map_planning_units(sources.planning_unit_rows, facts=facts)
    plans = map_plans(sources.planning_unit_rows)
    shifts = map_shifts(sources.shift_rows, facts=facts)

    return SchedulingDataset(
        planning_month=planning_month,
        planning_units=planning_units,
        plans=plans,
        employees=map_employees(sources.employee_rows, facts=facts),
        planning_unit_memberships=map_planning_unit_memberships(
            sources.planning_unit_membership_rows,
            facts=facts,
        ),
        shifts=shifts,
        assignments=map_assignments(
            rows=sources.roster_rows,
            selected_plan_ids={plan.plan_id for plan in plans},
            selected_planning_unit_ids={planning_unit.planning_unit_id for planning_unit in planning_units},
            facts=facts,
        ),
        availability=map_availability(
            rows=sources.roster_rows,
            facts=facts,
        ),
        demand_requirements=map_demand_requirements(
            planning_month=planning_month,
            planning_units=planning_units,
            facts=facts,
        ),
        sunday_work_history=map_sunday_work_history(sources.sunday_history_rows),
        wishes=map_wishes(
            rows=sources.wish_rows,
            shifts=shifts,
            facts=facts,
        ),
        monthly_work_accounts=map_monthly_work_accounts(sources.monthly_work_account_rows),
    )
