from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType

from src.scheduling.models.availability import AvailabilityType
from src.scheduling.models.employee import Capability, StaffLevel
from src.scheduling.models.planning_unit import PlanningUnitId, PlanningUnitKind
from src.scheduling.models.shift import ShiftId, ShiftKind, StaffingDemandRole


class TimeOfficePlanStatusId(IntEnum):
    """Known TimeOffice RefStati values used around plan selection.

    These are source-system IDs from TimeOffice.

    TARGET_PLANNING is the currently used plan status for reading the editable
    target roster that we want to repair/optimize.

    The other values are kept because they were already known in the inherited
    implementation and make the meaning of TARGET_PLANNING reviewable. They are
    not used by the current read pipeline.
    """

    TARGET_PLANNING = 20
    ACTUAL = 50
    COMPLETED = 70
    SETTLED = 80


# TimeOffice TDienste.Prim values used by the reduced scheduling model.
# Keep these source IDs local to TimeOffice facts.
EARLY_F2_SHIFT_ID = 2939
LATE_S2_SHIFT_ID = 2947
NIGHT_N2_SHIFT_ID = 2953
INTERMEDIATE_T75_SHIFT_ID = 2906
MANAGEMENT_Z60_SHIFT_ID = 1406

# Additional TimeOffice work shifts observed in roster rows.
NIGHT_N5_SHIFT_ID = 2889
NIGHT_N15_SHIFT_ID = 1692
OTHER_T8X_SHIFT_ID = 2994
OTHER_Z52_SHIFT_ID = 3066


@dataclass(frozen=True, slots=True)
class TimeOfficeShiftFact:
    """Validated meaning of one known TimeOffice shift."""

    source_shift_id: int
    expected_code: str
    kind: ShiftKind
    staffing_role: StaffingDemandRole


@dataclass(frozen=True, slots=True)
class TimeOfficeAvailabilityFact:
    source_shift_id: int
    expected_code: str
    availability_type: AvailabilityType


IsoWeekday = int  # Monday=1 ... Sunday=7


@dataclass(frozen=True, slots=True)
class TimeOfficeDemandFact:
    """Fallback TimeOffice demand fact.

    This represents the same reduced information that should later come from
    TimeOffice `TBenutzerBedarf*` tables.

    If planning_unit_ids is None, the demand applies to all selected station-like
    planning units.
    """

    source_shift_id: ShiftId
    staff_level: StaffLevel
    required_by_iso_weekday: Mapping[IsoWeekday, int]
    planning_unit_ids: tuple[PlanningUnitId, ...] | None = None


@dataclass(frozen=True, slots=True)
class TimeOfficeFacts:
    """Flat source assumptions for the TimeOffice adapter.

    This object carries constants only. It must not contain behavior.
    Repositories and validation code consume these facts for fetching, mapping,
    and source-drift checks.
    """

    monthly_planning_interval_id: int
    target_planning_status_id: int

    planning_unit_kind_map: dict[int, PlanningUnitKind]

    real_work_shift_type_ids: tuple[int, ...]
    shift_facts: tuple[TimeOfficeShiftFact, ...]

    profession_staff_level_map: dict[int, StaffLevel]
    # Temporary project/problem assumptions. Not DB-backed.
    employee_capabilities_map: dict[int, tuple[Capability, ...]]

    availability_facts: tuple[TimeOfficeAvailabilityFact, ...]

    demand_facts: tuple[TimeOfficeDemandFact, ...]


TIMEOFFICE_FACTS = TimeOfficeFacts(
    monthly_planning_interval_id=1,  # Known TimeOffice RefPlanungsIntervalle value
    target_planning_status_id=int(TimeOfficePlanStatusId.TARGET_PLANNING),
    planning_unit_kind_map={
        77: PlanningUnitKind.STATION,
        78: PlanningUnitKind.STATION,
        79: PlanningUnitKind.STATION,
        85: PlanningUnitKind.STATION,
        239: PlanningUnitKind.STATION,
        337: PlanningUnitKind.STATION,
        408: PlanningUnitKind.SHARED_POOL,
    },
    real_work_shift_type_ids=(1,),
    shift_facts=(
        TimeOfficeShiftFact(
            source_shift_id=EARLY_F2_SHIFT_ID,
            expected_code="F2_",
            kind=ShiftKind.EARLY,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        TimeOfficeShiftFact(
            source_shift_id=LATE_S2_SHIFT_ID,
            expected_code="S2_",
            kind=ShiftKind.LATE,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        TimeOfficeShiftFact(
            source_shift_id=NIGHT_N2_SHIFT_ID,
            expected_code="N2_",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        TimeOfficeShiftFact(
            source_shift_id=INTERMEDIATE_T75_SHIFT_ID,
            expected_code="T75_",
            kind=ShiftKind.INTERMEDIATE,
            staffing_role=StaffingDemandRole.OPTIONAL_COVERAGE,
        ),
        TimeOfficeShiftFact(
            source_shift_id=MANAGEMENT_Z60_SHIFT_ID,
            expected_code="Z60",
            kind=ShiftKind.MANAGEMENT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        TimeOfficeShiftFact(
            source_shift_id=NIGHT_N5_SHIFT_ID,
            expected_code="N5",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        TimeOfficeShiftFact(
            source_shift_id=NIGHT_N15_SHIFT_ID,
            expected_code="N15",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        TimeOfficeShiftFact(
            source_shift_id=OTHER_T8X_SHIFT_ID,
            expected_code="T8x",
            kind=ShiftKind.OTHER,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        TimeOfficeShiftFact(
            source_shift_id=OTHER_Z52_SHIFT_ID,
            expected_code="Z52",
            kind=ShiftKind.OTHER,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
    ),
    profession_staff_level_map={
        # Fachkraft
        803: StaffLevel.PROFESSIONAL,  # Gesundheits- und Krankenpfleger/in
        110: StaffLevel.PROFESSIONAL,  # Pflegefachkraft (Krankenpflege)
        129: StaffLevel.PROFESSIONAL,  # Altenpfleger/in
        651: StaffLevel.PROFESSIONAL,  # Pflegefachmann/-frau
        736: StaffLevel.PROFESSIONAL,  # Krankenschwester/-pfleger
        987: StaffLevel.PROFESSIONAL,  # Pflegefachkraft - Kinderkrankenpflege
        # Hilfskraft
        90: StaffLevel.ASSISTANT,  # Krankenpflegehelfer/in
        124: StaffLevel.ASSISTANT,  # Medizinische/r Fachangestellte/r
        326: StaffLevel.ASSISTANT,  # Helfer/in - stationäre Krankenpflege
        334: StaffLevel.ASSISTANT,  # Pflegehelfer/in - stationäre Pflege
        793: StaffLevel.ASSISTANT,  # Stationshilfe
        1245: StaffLevel.ASSISTANT,  # Bundesfreiwilligendienst
        # Azubi / Ausbildung
        835: StaffLevel.TRAINEE,  # A-Pflegeassistent/in
        837: StaffLevel.TRAINEE,  # A-Pflegefachkraft (Krankenpflege)
        1478: StaffLevel.TRAINEE,  # A-Pflegefachkraft (Altenpflege)
    },
    employee_capabilities_map={
        # Problem/legacy assumption: FWB employees for weekday early rounds.
        # Not DB-backed yet.
        791: (Capability.ROUNDS,),  # Branz, Janett
        2963: (Capability.ROUNDS,),  # Hoots, Renilde
        3868: (Capability.ROUNDS,),  # Vanfleet, Eike
        # Problem assumption: night-watch employees.
        # TPersonalVertraege.IstReineNachtwache did not confirm this, so keep it
        # explicitly marked as temporary/problem-derived.
        925: (Capability.NIGHT_WATCH,),  # Farniok, Lina
        6681: (Capability.NIGHT_WATCH,),  # Labelle, Saskia
        928: (Capability.NIGHT_WATCH,),  # Wunderlich, Daniele
    },
    availability_facts=(
        TimeOfficeAvailabilityFact(
            source_shift_id=2434,
            expected_code="U",
            availability_type=AvailabilityType.VACATION,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=2091,
            expected_code="ZU",
            availability_type=AvailabilityType.VACATION,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=1089,
            expected_code="FR",
            availability_type=AvailabilityType.FREE_DAY,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=26,
            expected_code="SC",
            availability_type=AvailabilityType.TRAINING,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=739,
            expected_code="FI",
            availability_type=AvailabilityType.TRAINING,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=1078,
            expected_code="EZ",
            availability_type=AvailabilityType.UNAVAILABLE,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=1086,
            expected_code="RE",
            availability_type=AvailabilityType.UNAVAILABLE,
        ),
        TimeOfficeAvailabilityFact(
            source_shift_id=1092,
            expected_code="AZV",
            availability_type=AvailabilityType.FREE_DAY,
        ),
    ),
    demand_facts=(
        # Fachkraft
        TimeOfficeDemandFact(
            source_shift_id=EARLY_F2_SHIFT_ID,
            staff_level=StaffLevel.PROFESSIONAL,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 3,  # Mo
                    2: 3,  # Di
                    3: 4,  # Mi
                    4: 3,  # Do
                    5: 3,  # Fr
                    6: 2,  # Sa
                    7: 2,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=LATE_S2_SHIFT_ID,
            staff_level=StaffLevel.PROFESSIONAL,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 2,  # Mo
                    2: 2,  # Di
                    3: 2,  # Mi
                    4: 2,  # Do
                    5: 2,  # Fr
                    6: 2,  # Sa
                    7: 2,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=NIGHT_N2_SHIFT_ID,
            staff_level=StaffLevel.PROFESSIONAL,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 2,  # Mo
                    2: 2,  # Di
                    3: 2,  # Mi
                    4: 2,  # Do
                    5: 2,  # Fr
                    6: 1,  # Sa
                    7: 1,  # So
                }
            ),
        ),
        # Hilfskraft
        TimeOfficeDemandFact(
            source_shift_id=EARLY_F2_SHIFT_ID,
            staff_level=StaffLevel.ASSISTANT,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 2,  # Mo
                    2: 2,  # Di
                    3: 2,  # Mi
                    4: 2,  # Do
                    5: 2,  # Fr
                    6: 2,  # Sa
                    7: 2,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=LATE_S2_SHIFT_ID,
            staff_level=StaffLevel.ASSISTANT,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 2,  # Mo
                    2: 2,  # Di
                    3: 2,  # Mi
                    4: 2,  # Do
                    5: 2,  # Fr
                    6: 2,  # Sa
                    7: 2,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=NIGHT_N2_SHIFT_ID,
            staff_level=StaffLevel.ASSISTANT,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 0,  # Mo
                    2: 0,  # Di
                    3: 0,  # Mi
                    4: 0,  # Do
                    5: 0,  # Fr
                    6: 1,  # Sa
                    7: 1,  # So
                }
            ),
        ),
        # Azubi
        TimeOfficeDemandFact(
            source_shift_id=EARLY_F2_SHIFT_ID,
            staff_level=StaffLevel.TRAINEE,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 1,  # Mo
                    2: 1,  # Di
                    3: 1,  # Mi
                    4: 1,  # Do
                    5: 1,  # Fr
                    6: 1,  # Sa
                    7: 1,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=LATE_S2_SHIFT_ID,
            staff_level=StaffLevel.TRAINEE,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 1,  # Mo
                    2: 1,  # Di
                    3: 1,  # Mi
                    4: 1,  # Do
                    5: 1,  # Fr
                    6: 1,  # Sa
                    7: 1,  # So
                }
            ),
        ),
        TimeOfficeDemandFact(
            source_shift_id=NIGHT_N2_SHIFT_ID,
            staff_level=StaffLevel.TRAINEE,
            required_by_iso_weekday=MappingProxyType(
                {
                    1: 0,  # Mo
                    2: 0,  # Di
                    3: 0,  # Mi
                    4: 0,  # Do
                    5: 0,  # Fr
                    6: 0,  # Sa
                    7: 0,  # So
                }
            ),
        ),
    ),
)
