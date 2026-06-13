from enum import IntEnum, StrEnum

from pydantic import BaseModel, Field

from src.scheduling.models.shift import ShiftKind


class TimeOfficePlanStatus(IntEnum):
    """Known TimeOffice plan status ids."""

    TARGET_PLANNING = 20
    ACTUAL = 50
    COMPLETED = 70
    SETTLED = 80


class TimeOfficePlanningInterval(IntEnum):
    """Known TimeOffice planning interval ids."""

    MONTHLY = 1
    ANNUAL = 3


class TimeOfficeShiftType(IntEnum):
    """Known TimeOffice shift type ids."""

    WORK = 1


class StationType(StrEnum):
    """Configured station role for the TimeOffice import."""

    REGULAR = "regular"
    JUMP_POOL = "jump_pool"


class TimeOfficePlanSelection(BaseModel):
    """Which TimeOffice plans are used as source for scheduling."""

    planning_interval_id: TimeOfficePlanningInterval
    plan_status_id: TimeOfficePlanStatus


class TimeOfficeStationConfig(BaseModel):
    """Configured TimeOffice station relevant for the project."""

    station_id: int = Field(gt=0)
    label: str
    station_type: StationType = StationType.REGULAR
    area_hint: str | None = None
    notes: str | None = None


class TimeOfficeShiftConfig(BaseModel):
    """Configured TimeOffice shift relevant for the solver."""

    source_shift_id: int = Field(gt=0)
    expected_code: str

    kind: ShiftKind
    group_id: str

    assignable: bool = True
    counts_as_work: bool = True
    counts_for_minimum_staffing: bool = True

    description: str | None = None


class TimeOfficeConfig(BaseModel):
    """Source of truth for TimeOffice IDs and project-specific import semantics.

    Keep external TimeOffice IDs and project/domain decisions here instead of
    scattering them through repositories, SQL queries, or solver code.
    """

    plan_selection: TimeOfficePlanSelection
    stations: tuple[TimeOfficeStationConfig, ...]
    solver_shifts: tuple[TimeOfficeShiftConfig, ...]
    assignable_shift_type_ids: tuple[TimeOfficeShiftType, ...]

    @property
    def station_ids(self) -> tuple[int, ...]:
        """Return all configured TimeOffice station ids."""
        return tuple(station.station_id for station in self.stations)

    @property
    def solver_shift_ids(self) -> tuple[int, ...]:
        """Return all configured TimeOffice shift ids used by the solver."""
        return tuple(shift.source_shift_id for shift in self.solver_shifts)

    @property
    def stations_by_id(self) -> dict[int, TimeOfficeStationConfig]:
        """Return configured stations keyed by TimeOffice station id."""
        return {station.station_id: station for station in self.stations}

    @property
    def shifts_by_id(self) -> dict[int, TimeOfficeShiftConfig]:
        """Return configured solver shifts keyed by TimeOffice shift id."""
        return {shift.source_shift_id: shift for shift in self.solver_shifts}

    def regular_station_ids_for(self, station_ids: tuple[int, ...]) -> tuple[int, ...]:
        """Return requested station ids that are configured as regular stations."""
        return tuple(
            station_id for station_id in station_ids if self.station_type_for(station_id) == StationType.REGULAR
        )

    def jump_pool_station_ids_for(self, station_ids: tuple[int, ...]) -> tuple[int, ...]:
        """Return requested station ids that are configured as jump-pool stations."""
        return tuple(
            station_id for station_id in station_ids if self.station_type_for(station_id) == StationType.JUMP_POOL
        )

    def station_type_for(self, station_id: int) -> StationType:
        """Return configured station type.

        Unknown stations default to regular to keep exploratory database reads
        possible while we are still inspecting TimeOffice data.
        """
        station = self.stations_by_id.get(station_id)

        if station is None:
            return StationType.REGULAR

        return station.station_type


STATION_77 = 77
STATION_79_LEGACY = 79
STATION_337 = 337
STATION_85 = 85
STATION_239 = 239
STATION_78 = 78
SPRINGERPOOL_408 = 408

SHIFT_Z60 = 1406
SHIFT_T75 = 2906
SHIFT_F2 = 2939
SHIFT_S2 = 2947
SHIFT_N2 = 2953

TIMEOFFICE_CONFIG = TimeOfficeConfig(
    plan_selection=TimeOfficePlanSelection(
        planning_interval_id=TimeOfficePlanningInterval.MONTHLY,
        plan_status_id=TimeOfficePlanStatus.TARGET_PLANNING,
    ),
    assignable_shift_type_ids=(TimeOfficeShiftType.WORK,),
    stations=(
        TimeOfficeStationConfig(
            station_id=STATION_77,
            label="Station 77",
            area_hint="Bereich 5 / Bereich 32",
            notes="Previously used station.",
        ),
        TimeOfficeStationConfig(
            station_id=STATION_79_LEGACY,
            label="Station 79",
            notes="Legacy/development station used during refactoring; not listed as long-term station.",
        ),
        TimeOfficeStationConfig(
            station_id=STATION_337,
            label="Station 337",
            area_hint="Bereich 5 / Bereich 32",
        ),
        TimeOfficeStationConfig(
            station_id=STATION_85,
            label="Station 85",
            area_hint="Bereich 5 / Bereich 32",
        ),
        TimeOfficeStationConfig(
            station_id=STATION_239,
            label="Station 239",
            area_hint="Bereich 17",
        ),
        TimeOfficeStationConfig(
            station_id=STATION_78,
            label="Station 78",
            area_hint="Bereich 5 / Bereich 32",
        ),
        TimeOfficeStationConfig(
            station_id=SPRINGERPOOL_408,
            label="Springerpool",
            station_type=StationType.JUMP_POOL,
            area_hint="Bereich 546",
        ),
    ),
    solver_shifts=(
        TimeOfficeShiftConfig(
            source_shift_id=SHIFT_F2,
            expected_code="F2_",
            kind=ShiftKind.EARLY,
            group_id="early",
            counts_for_minimum_staffing=True,
            description="Required early shift F2.",
        ),
        TimeOfficeShiftConfig(
            source_shift_id=SHIFT_S2,
            expected_code="S2_",
            kind=ShiftKind.LATE,
            group_id="late",
            counts_for_minimum_staffing=True,
            description="Required late shift S2.",
        ),
        TimeOfficeShiftConfig(
            source_shift_id=SHIFT_N2,
            expected_code="N2_",
            kind=ShiftKind.NIGHT,
            group_id="night",
            counts_for_minimum_staffing=True,
            description="Required night shift N2.",
        ),
        TimeOfficeShiftConfig(
            source_shift_id=SHIFT_T75,
            expected_code="T75_",
            kind=ShiftKind.INTERMEDIATE,
            group_id="intermediate",
            counts_for_minimum_staffing=True,
            description="Optional/intermediate Zwischendienst T75.",
        ),
        TimeOfficeShiftConfig(
            source_shift_id=SHIFT_Z60,
            expected_code="Z60",
            kind=ShiftKind.MANAGEMENT,
            group_id="management",
            counts_for_minimum_staffing=False,
            description="Management shift Z60. Counts as work, not minimum staffing.",
        ),
    ),
)
