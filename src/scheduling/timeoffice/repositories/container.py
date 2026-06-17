from dataclasses import dataclass

from scheduling.timeoffice.facts import TimeOfficeFacts
from scheduling.timeoffice.repositories.demand import TimeOfficeDemandRepository
from scheduling.timeoffice.repositories.monthly_work_accounts import TimeOfficeMonthlyWorkAccountRepository
from scheduling.timeoffice.repositories.personnel import TimeOfficePersonnelRepository
from scheduling.timeoffice.repositories.planning_units import TimeOfficePlanningUnitRepository
from scheduling.timeoffice.repositories.roster import TimeOfficeRosterRepository
from scheduling.timeoffice.repositories.shifts import TimeOfficeShiftRepository
from scheduling.timeoffice.repositories.sunday_work_history import TimeOfficeSundayWorkHistoryRepository
from scheduling.timeoffice.repositories.wishes import TimeOfficeWishRepository


@dataclass(frozen=True, slots=True)
class TimeOfficeRepositories:
    planning_units: TimeOfficePlanningUnitRepository
    personnel: TimeOfficePersonnelRepository
    shifts: TimeOfficeShiftRepository
    roster: TimeOfficeRosterRepository
    demand: TimeOfficeDemandRepository
    sunday_work_history: TimeOfficeSundayWorkHistoryRepository
    wishes: TimeOfficeWishRepository
    monthly_work_accounts: TimeOfficeMonthlyWorkAccountRepository

    @classmethod
    def create(cls, *, facts: TimeOfficeFacts) -> "TimeOfficeRepositories":
        return cls(
            planning_units=TimeOfficePlanningUnitRepository(facts=facts),
            personnel=TimeOfficePersonnelRepository(facts=facts),
            shifts=TimeOfficeShiftRepository(facts=facts),
            roster=TimeOfficeRosterRepository(facts=facts),
            demand=TimeOfficeDemandRepository(facts=facts),
            sunday_work_history=TimeOfficeSundayWorkHistoryRepository(),
            wishes=TimeOfficeWishRepository(facts=facts),
            monthly_work_accounts=TimeOfficeMonthlyWorkAccountRepository(facts=facts),
        )
