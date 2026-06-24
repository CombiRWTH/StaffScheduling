from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from scheduling.domain.availability import AvailabilityType
from scheduling.domain.employee import Capability, StaffLevel
from scheduling.domain.planning_unit import PlanningUnitId, PlanningUnitType
from scheduling.domain.shift import ShiftId, ShiftType, StaffingDemandRole
from scheduling.domain.wish import WishType

# TPlan.RefPlanungsIntervalle value for monthly planning.
MONTHLY_PLANNING_INTERVAL_ID = 1

# TPlan.RefStati value for the editable target roster used as planning input.
TARGET_PLANNING_STATUS_ID = 20

# TDienste.RefDienstTypen value for normal work shifts.
WORK_SHIFT_TYPE_ID = 1

# TPersonalKontenJeMonat.RefKonten for planned monthly target hours.
MONTHLY_TARGET_WORK_ACCOUNT_ID = 1

# TPersonalKontenJeMonat.RefKonten for current monthly actual hours.
MONTHLY_ACTUAL_WORK_ACCOUNT_ID = 55

# TPlanungseinheiten.Prim values currently known to the project.
STATION_77_ID = 77
STATION_78_ID = 78
STATION_79_ID = 79
STATION_85_ID = 85
STATION_239_ID = 239
STATION_337_ID = 337

# Known TimeOffice planning unit for the shared/jump pool.
SHARED_POOL_408_ID = 408

# TDienste.Prim values for the reduced reference shifts exposed to the solver.
# These are the only TimeOffice shift IDs that should become canonical Shift.shift_id
# values in the reduced SchedulingDataset.
EARLY_F2_SHIFT_ID = 2939
LATE_S2_SHIFT_ID = 2947
NIGHT_N2_SHIFT_ID = 2953
INTERMEDIATE_T75_SHIFT_ID = 2906
MANAGEMENT_Z60_SHIFT_ID = 1406


@dataclass(frozen=True, slots=True)
class TimeOfficeReferenceShiftFact:
    """Domain meaning of one reduced reference shift.

    The mapping code verifies that the TimeOffice shift row identified by the
    reference shift ID still has expected_code. Source-shift variants are mapped
    separately by shift_code_overrides.
    """

    expected_code: str
    type: ShiftType
    staffing_role: StaffingDemandRole


type WeekdayDemand = tuple[int, int, int, int, int, int, int]  # Mo, Di, Mi, Do, Fr, Sa, So
type PlanningUnitDemandMatrix = Mapping[StaffLevel, Mapping[ShiftId, WeekdayDemand]]


@dataclass(frozen=True, slots=True)
class TimeOfficeFacts:
    """Source assumptions and reduced-domain mappings for the TimeOffice adapter.

    Facts contain adapter constants and source-to-domain mappings only. They do
    not perform checks themselves; readers provide source rows and mapping code
    uses these facts to fail loudly on unmapped or drifted source semantics.
    """

    monthly_planning_interval_id: int
    target_planning_status_id: int

    planning_unit_type_by_id: Mapping[PlanningUnitId, PlanningUnitType]

    work_shift_type_id: int

    reference_shift_facts_by_id: Mapping[ShiftId, TimeOfficeReferenceShiftFact]

    # Non-reference source shift IDs normalized to reduced reference shifts.
    # Missing source shift ID => fail loudly in mapping.
    shift_id_overrides: Mapping[ShiftId, ShiftId]

    staff_level_by_profession_code: Mapping[str, StaffLevel]

    # Temporary fallback until demand is read from TimeOffice demand tables.
    # Shape mirrors the future source concept: planning unit -> staff level -> shift -> weekday demand.
    fallback_demand_by_planning_unit: Mapping[PlanningUnitId, PlanningUnitDemandMatrix]

    # Temporary project/problem assumptions. Not DB-backed yet.
    capabilities_by_employee_id: Mapping[int, tuple[Capability, ...]]

    availability_type_by_absence_code: Mapping[str, AvailabilityType]
    ignored_availability_absence_codes: frozenset[str]

    wish_type_by_absence_code: Mapping[str, WishType]

    monthly_target_work_account_id: int
    monthly_actual_work_account_id: int


REFERENCE_SHIFT_FACTS_BY_ID: Mapping[ShiftId, TimeOfficeReferenceShiftFact] = MappingProxyType(
    {
        EARLY_F2_SHIFT_ID: TimeOfficeReferenceShiftFact(
            expected_code="F2_",
            type=ShiftType.EARLY,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        LATE_S2_SHIFT_ID: TimeOfficeReferenceShiftFact(
            expected_code="S2_",
            type=ShiftType.LATE,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        NIGHT_N2_SHIFT_ID: TimeOfficeReferenceShiftFact(
            expected_code="N2_",
            type=ShiftType.NIGHT,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        INTERMEDIATE_T75_SHIFT_ID: TimeOfficeReferenceShiftFact(
            expected_code="T75_",
            type=ShiftType.INTERMEDIATE,
            staffing_role=StaffingDemandRole.OPTIONAL_COVERAGE,
        ),
        MANAGEMENT_Z60_SHIFT_ID: TimeOfficeReferenceShiftFact(
            expected_code="Z60",
            type=ShiftType.MANAGEMENT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
    }
)

# Source shift variants observed in roster rows.
# Reference shift codes must not be repeated here.
SHIFT_ID_OVERRIDES: Mapping[ShiftId, ShiftId] = MappingProxyType(
    {
        # Night variants normalized to canonical N2_ night shift.
        1692: NIGHT_N2_SHIFT_ID,  # N15, partial night
        3076: NIGHT_N2_SHIFT_ID,  # N5
        2889: NIGHT_N2_SHIFT_ID,  # N5
        1698: NIGHT_N2_SHIFT_ID,  # N5
        2866: NIGHT_N2_SHIFT_ID,  # N5
        # Day/intermediate variant normalized to canonical T75_ intermediate shift.
        2994: INTERMEDIATE_T75_SHIFT_ID,  # T8x
        # Short/day special variants normalized to canonical Z60 non-minimum work shift.
        2957: MANAGEMENT_Z60_SHIFT_ID,  # Z52
        2687: MANAGEMENT_Z60_SHIFT_ID,  # Z52
        1403: MANAGEMENT_Z60_SHIFT_ID,  # Z52
        3066: MANAGEMENT_Z60_SHIFT_ID,  # Z52
    }
)

STAFF_LEVEL_BY_PROFESSION_CODE: Mapping[str, StaffLevel] = MappingProxyType(
    {
        # Fachkraft
        "81302-003": StaffLevel.PROFESSIONAL,  # Gesundheits- und Kinderkrankenpfleger/in
        "81302-005": StaffLevel.PROFESSIONAL,  # Gesundheits- und Krankenpfleger/in
        "81302-007": StaffLevel.PROFESSIONAL,  # Kinderkrankenschwester/-pfleger
        "81302-008": StaffLevel.PROFESSIONAL,  # Krankenschwester/-pfleger
        "81302-009": StaffLevel.PROFESSIONAL,  # Krankenschwester/-pfleger - Nachtwache
        "81302-016": StaffLevel.PROFESSIONAL,  # Pflegefachkraft - Kinderkrankenpflege
        "81302-018": StaffLevel.PROFESSIONAL,  # Pflegefachkraft Krankenpflege
        "81302-028": StaffLevel.PROFESSIONAL,  # Pflegefachmann/-frau
        "81313-059": StaffLevel.PROFESSIONAL,  # Fachkrankenpfleger/in - Notfallpflege
        "81393-011": StaffLevel.PROFESSIONAL,  # Stationsleiter/in - Pflegedienst
        "82102-002": StaffLevel.PROFESSIONAL,  # Altenpfleger/in
        "EX-81302-028": StaffLevel.PROFESSIONAL,  # EX-Pflegefachmann/-frau
        # Legacy classified this as Fachkraft.
        "63302-045": StaffLevel.PROFESSIONAL,  # Servicekraft
        # Hilfskraft / support
        "81102-001": StaffLevel.ASSISTANT,  # Arzthelfer/in
        "81102-004": StaffLevel.ASSISTANT,  # Medizinische/r Fachangestellte/r
        "81301-002": StaffLevel.ASSISTANT,  # Helfer/in - stationäre Krankenpflege
        "81301-006": StaffLevel.ASSISTANT,  # Krankenpflegehelfer/in, 1-jährige Ausbildung
        "81301-010": StaffLevel.ASSISTANT,  # Pflegehelfer/in ohne 1-jährige Ausbildung
        "81301-014": StaffLevel.ASSISTANT,  # Schwesterhelfer/in
        "81301-018": StaffLevel.ASSISTANT,  # Stationshilfe
        "81302-014": StaffLevel.ASSISTANT,  # Pflegeassistent/in
        "BFD": StaffLevel.ASSISTANT,  # Bundesfreiwilligendienst
        # Legacy classified this as Hilfskraft.
        "Pra": StaffLevel.ASSISTANT,  # Praktikant/-in
        # Ausbildung / Praktikum
        "A-31342-005": StaffLevel.TRAINEE,  # A-Notfallsanitäter
        "A-81302-007": StaffLevel.TRAINEE,  # A-Kinderkrankenschwester/-pfleger
        "A-81302-008": StaffLevel.TRAINEE,  # A-Krankenschwester/-pfleger
        "A-81302-014": StaffLevel.TRAINEE,  # A-Pflegeassistent/in
        "A-81302-016": StaffLevel.TRAINEE,  # A-Pflegefachkraft Kinderkrankenpflege
        "A-81302-018": StaffLevel.TRAINEE,  # A-Pflegefachkraft Krankenpflege
        "A-81302-019": StaffLevel.TRAINEE,  # A-Pflegefachkraft Altenpflege
    }
)

# Minimal default while solver constraints are being migrated to SchedulingDataset.
# Empty demand means: read/map/validate the station, but do not create artificial
# fallback coverage requirements for it yet.
DEFAULT_STATION_DEMAND: PlanningUnitDemandMatrix = MappingProxyType({})

STATION_77_DEMAND: PlanningUnitDemandMatrix = MappingProxyType(
    {
        # Weekday tuple order: Mo, Di, Mi, Do, Fr, Sa, So.
        StaffLevel.PROFESSIONAL: MappingProxyType(
            {
                EARLY_F2_SHIFT_ID: (3, 3, 4, 3, 3, 2, 2),
                LATE_S2_SHIFT_ID: (2, 2, 2, 2, 2, 2, 2),
                NIGHT_N2_SHIFT_ID: (2, 2, 2, 2, 2, 1, 1),
            }
        ),
        StaffLevel.ASSISTANT: MappingProxyType(
            {
                EARLY_F2_SHIFT_ID: (2, 2, 2, 2, 2, 2, 2),
                LATE_S2_SHIFT_ID: (2, 2, 2, 2, 2, 2, 2),
                NIGHT_N2_SHIFT_ID: (0, 0, 0, 0, 0, 1, 1),
            }
        ),
        StaffLevel.TRAINEE: MappingProxyType(
            {
                EARLY_F2_SHIFT_ID: (1, 1, 1, 1, 1, 1, 1),
                LATE_S2_SHIFT_ID: (1, 1, 1, 1, 1, 1, 1),
                NIGHT_N2_SHIFT_ID: (0, 0, 0, 0, 0, 0, 0),
            }
        ),
    }
)


TIMEOFFICE_FACTS = TimeOfficeFacts(
    monthly_planning_interval_id=MONTHLY_PLANNING_INTERVAL_ID,
    target_planning_status_id=TARGET_PLANNING_STATUS_ID,
    planning_unit_type_by_id=MappingProxyType(
        {
            STATION_77_ID: PlanningUnitType.STATION,
            STATION_78_ID: PlanningUnitType.STATION,
            STATION_79_ID: PlanningUnitType.STATION,
            STATION_85_ID: PlanningUnitType.STATION,
            STATION_239_ID: PlanningUnitType.STATION,
            STATION_337_ID: PlanningUnitType.STATION,
            SHARED_POOL_408_ID: PlanningUnitType.SHARED_POOL,
        }
    ),
    work_shift_type_id=WORK_SHIFT_TYPE_ID,
    reference_shift_facts_by_id=REFERENCE_SHIFT_FACTS_BY_ID,
    shift_id_overrides=SHIFT_ID_OVERRIDES,
    staff_level_by_profession_code=STAFF_LEVEL_BY_PROFESSION_CODE,
    fallback_demand_by_planning_unit=MappingProxyType(
        {
            STATION_77_ID: STATION_77_DEMAND,
            STATION_78_ID: DEFAULT_STATION_DEMAND,
            STATION_79_ID: DEFAULT_STATION_DEMAND,
            STATION_85_ID: DEFAULT_STATION_DEMAND,
            STATION_239_ID: DEFAULT_STATION_DEMAND,
            STATION_337_ID: DEFAULT_STATION_DEMAND,
            # Intentionally no demand for SHARED_POOL_408_ID.
        }
    ),
    capabilities_by_employee_id=MappingProxyType(
        {
            # Not DB-backed yet.
            # Problem/legacy assumption: FWB employees for weekday early rounds.
            791: (Capability.ROUNDS,),  # Branz, Janett
            2963: (Capability.ROUNDS,),  # Hoots, Renilde
            3868: (Capability.ROUNDS,),  # Vanfleet, Eike
            # Problem assumption: night-watch employees.
            925: (Capability.NIGHT_WATCH,),  # Farniok, Lina
            6681: (Capability.NIGHT_WATCH,),  # Labelle, Saskia
            928: (Capability.NIGHT_WATCH,),  # Wunderlich, Daniele
        }
    ),
    availability_type_by_absence_code=MappingProxyType(
        {
            "U": AvailabilityType.VACATION,
            "ZU": AvailabilityType.VACATION,
            # Conservative hard blockers until TimeOffice/domain semantics are confirmed.
            "SC": AvailabilityType.UNAVAILABLE,
            "EZ": AvailabilityType.UNAVAILABLE,
            "RE": AvailabilityType.UNAVAILABLE,
            "FI": AvailabilityType.UNAVAILABLE,
        }
    ),
    ignored_availability_absence_codes=frozenset(
        {
            # Existing roster free/reduction markers.
            # They must not block solve-from-scratch.
            "FR",
            "AZV",
        }
    ),
    wish_type_by_absence_code=MappingProxyType(
        {
            "FR": WishType.FREE_DAY,
        }
    ),
    monthly_target_work_account_id=MONTHLY_TARGET_WORK_ACCOUNT_ID,
    monthly_actual_work_account_id=MONTHLY_ACTUAL_WORK_ACCOUNT_ID,
)
