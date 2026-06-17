from dataclasses import dataclass

from src.scheduling.timeoffice.facts import TimeOfficeFacts
from src.scheduling.timeoffice.repositories.demand import TimeOfficeDemandRepository
from src.scheduling.timeoffice.repositories.personnel import TimeOfficePersonnelRepository
from src.scheduling.timeoffice.repositories.planning_units import TimeOfficePlanningUnitRepository
from src.scheduling.timeoffice.repositories.roster import TimeOfficeRosterRepository
from src.scheduling.timeoffice.repositories.shifts import TimeOfficeShiftRepository
from src.scheduling.timeoffice.repositories.sunday_work_history import TimeOfficeSundayWorkHistoryRepository


@dataclass(frozen=True, slots=True)
class TimeOfficeRepositories:
    planning_units: TimeOfficePlanningUnitRepository
    personnel: TimeOfficePersonnelRepository
    shifts: TimeOfficeShiftRepository
    roster: TimeOfficeRosterRepository
    demand: TimeOfficeDemandRepository
    sunday_work_history: TimeOfficeSundayWorkHistoryRepository

    @classmethod
    def create(cls, *, facts: TimeOfficeFacts) -> "TimeOfficeRepositories":
        return cls(
            planning_units=TimeOfficePlanningUnitRepository(facts=facts),
            personnel=TimeOfficePersonnelRepository(facts=facts),
            shifts=TimeOfficeShiftRepository(facts=facts),
            roster=TimeOfficeRosterRepository(facts=facts),
            demand=TimeOfficeDemandRepository(facts=facts),
            sunday_work_history=TimeOfficeSundayWorkHistoryRepository(),
        )
