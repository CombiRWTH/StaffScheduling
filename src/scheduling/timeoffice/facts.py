from collections.abc import Mapping
from dataclasses import dataclass
from enum import IntEnum
from types import MappingProxyType

from scheduling.models.availability import AvailabilityType
from scheduling.models.employee import Capability, StaffLevel
from scheduling.models.planning_unit import PlanningUnitId, PlanningUnitKind
from scheduling.models.shift import ShiftId, ShiftKind, StaffingDemandRole
from scheduling.models.wish import WishKind


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

    work_shift_type_ids: tuple[int, ...]
    shift_facts_by_id: Mapping[int, TimeOfficeShiftFact]

    staff_level_by_profession_id_map: dict[int, StaffLevel]
    demand_facts: tuple[TimeOfficeDemandFact, ...]

    # Temporary project/problem assumptions. Not DB-backed.
    capabilities_by_employee_id_map: dict[int, tuple[Capability, ...]]

    availability_type_by_absence_code: Mapping[str, AvailabilityType]
    wish_kind_by_absence_code: Mapping[str, WishKind]

    monthly_target_work_account_id: int
    monthly_actual_work_account_id: int


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
    work_shift_type_ids=(1,),
    shift_facts_by_id={
        EARLY_F2_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=EARLY_F2_SHIFT_ID,
            expected_code="F2_",
            kind=ShiftKind.EARLY,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        LATE_S2_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=LATE_S2_SHIFT_ID,
            expected_code="S2_",
            kind=ShiftKind.LATE,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        NIGHT_N2_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=NIGHT_N2_SHIFT_ID,
            expected_code="N2_",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.REQUIRED_MINIMUM,
        ),
        INTERMEDIATE_T75_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=INTERMEDIATE_T75_SHIFT_ID,
            expected_code="T75_",
            kind=ShiftKind.INTERMEDIATE,
            staffing_role=StaffingDemandRole.OPTIONAL_COVERAGE,
        ),
        MANAGEMENT_Z60_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=MANAGEMENT_Z60_SHIFT_ID,
            expected_code="Z60",
            kind=ShiftKind.MANAGEMENT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        NIGHT_N5_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=NIGHT_N5_SHIFT_ID,
            expected_code="N5",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        NIGHT_N15_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=NIGHT_N15_SHIFT_ID,
            expected_code="N15",
            kind=ShiftKind.NIGHT,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        OTHER_T8X_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=OTHER_T8X_SHIFT_ID,
            expected_code="T8x",
            kind=ShiftKind.OTHER,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
        OTHER_Z52_SHIFT_ID: TimeOfficeShiftFact(
            source_shift_id=OTHER_Z52_SHIFT_ID,
            expected_code="Z52",
            kind=ShiftKind.OTHER,
            staffing_role=StaffingDemandRole.NON_MINIMUM_WORK,
        ),
    },
    staff_level_by_profession_id_map={
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
    capabilities_by_employee_id_map={
        # Not DB-backed yet.
        # Problem/legacy assumption: FWB employees for weekday early rounds.
        791: (Capability.ROUNDS,),  # Branz, Janett
        2963: (Capability.ROUNDS,),  # Hoots, Renilde
        3868: (Capability.ROUNDS,),  # Vanfleet, Eike
        # Problem assumption: night-watch employees.
        925: (Capability.NIGHT_WATCH,),  # Farniok, Lina
        6681: (Capability.NIGHT_WATCH,),  # Labelle, Saskia
        928: (Capability.NIGHT_WATCH,),  # Wunderlich, Daniele
    },
    availability_type_by_absence_code=MappingProxyType(
        {
            "U": AvailabilityType.VACATION,
            "ZU": AvailabilityType.VACATION,
            "FR": AvailabilityType.FREE_DAY,
            "AZV": AvailabilityType.FREE_DAY,
            # Conservative hard blockers until TimeOffice/domain semantics are confirmed.
            "SC": AvailabilityType.UNAVAILABLE,
            "EZ": AvailabilityType.UNAVAILABLE,
            "RE": AvailabilityType.UNAVAILABLE,
            "FI": AvailabilityType.UNAVAILABLE,
        }
    ),
    wish_kind_by_absence_code=MappingProxyType(
        {
            "FR": WishKind.FREE_DAY,
        }
    ),
    monthly_target_work_account_id=1,
    monthly_actual_work_account_id=55,
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
