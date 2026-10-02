from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.domain.availability import AvailabilityType
from app.domain.employee import Capability, StaffLevel
from app.domain.planning_unit import PlanningUnitId, PlanningUnitType
from app.domain.shift import ShiftId, ShiftType

# TPlan.RefPlanungsIntervalle value for monthly planning.
MONTHLY_PLANNING_INTERVAL_ID = 1

# TPlan.RefStati value for the editable target roster used as planning input.
TARGET_PLANNING_STATUS_ID = 20

# TPersonalKontenJeMonat.RefKonten for planned monthly target hours.
MONTHLY_TARGET_WORK_ACCOUNT_ID = 1

# TPersonalKontenJeMonat.RefKonten for current monthly actual hours.
MONTHLY_ACTUAL_WORK_ACCOUNT_ID = 55

# TPersonalKontenJeTag.RefKonten of the daily absence-hour accounts that credit work.
VACATION_CREDIT_ACCOUNT_ID = 85  # U_STD, ABW: Urlaub Std.
INTERNAL_TRAINING_CREDIT_ACCOUNT_ID = 93  # FI_STD, ABW: Fortbildung intern Std.
EXTERNAL_TRAINING_CREDIT_ACCOUNT_ID = 95  # FE_STD, ABW: Fortbildung extern Std.
SCHOOL_CREDIT_ACCOUNT_ID = 97  # ST_STD, ABW: Schule Stunden

# TPlanungseinheiten.Prim of the prepared example units (KurzBez BSP-A, BSP-B, BSP-JUMP).
# Supporting another unit means adding it here; see the TimeOffice adapter docs for the checklist.
EXAMPLE_STATION_A_ID = 427  # demand profile 85
EXAMPLE_STATION_B_ID = 428  # demand profile 79
EXAMPLE_JUMPER_POOL_ID = 429

# TDienste.Prim values of the reduced reference shifts; the only shift IDs the planning model uses.
# There are 2 Prim for the Early Shift: 1113 and 3000
EARLY_SHIFT_ID = 1113
# There are 3 Prim for the Late Shift: 1605, 2011, and 3002
LATE_SHIFT_ID = 1605
# There are 3 Prim for the Night Shift: 1690, 2449, and 3001
NIGHT_SHIFT_ID = 1690
# Ist die Intermediate Shift T(1410) oder Z(1453)?
INTERMEDIATE_SHIFT_ID = 1453


@dataclass(frozen=True, slots=True)
class TimeOfficeFacts:
    """Source assumptions and reduced-domain mappings for the TimeOffice adapter.

    Facts contain adapter constants and source-to-domain mappings only. They do
    not perform checks themselves; the query functions use them and fail loudly
    on unmapped or drifted source semantics.
    """

    monthly_planning_interval_id: int
    target_planning_status_id: int

    planning_unit_type_by_id: Mapping[PlanningUnitId, PlanningUnitType]

    reference_shift_type_by_id: Mapping[ShiftId, ShiftType]

    staff_level_by_profession_code: Mapping[str, StaffLevel]

    # Temporary project/problem assumptions. Not DB-backed yet.
    capabilities_by_employee_id: Mapping[int, tuple[Capability, ...]]

    availability_type_by_absence_code: Mapping[str, AvailabilityType]
    ignored_availability_absence_codes: frozenset[str]

    monthly_target_work_account_id: int
    monthly_actual_work_account_id: int

    # Daily absence-hour accounts that credit work, with the absence code they book.
    credited_absence_code_by_account_id: Mapping[int, str]

    @property
    def reference_shift_ids(self) -> frozenset[ShiftId]:
        return frozenset(self.reference_shift_type_by_id)


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
        "81102-004": StaffLevel.MFA,  # Medizinische/r Fachangestellte/r
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
        "-": StaffLevel.TRAINEE,  # Später herausfinden was das für eine Profession ist
    }
)

TIMEOFFICE_FACTS = TimeOfficeFacts(
    monthly_planning_interval_id=MONTHLY_PLANNING_INTERVAL_ID,
    target_planning_status_id=TARGET_PLANNING_STATUS_ID,
    planning_unit_type_by_id=MappingProxyType(
        {
            EXAMPLE_STATION_A_ID: PlanningUnitType.STATION,
            EXAMPLE_STATION_B_ID: PlanningUnitType.STATION,
            EXAMPLE_JUMPER_POOL_ID: PlanningUnitType.JUMPER_POOL,
        }
    ),
    reference_shift_type_by_id=MappingProxyType(
        {
            EARLY_SHIFT_ID: ShiftType.EARLY,
            INTERMEDIATE_SHIFT_ID: ShiftType.INTERMEDIATE,
            LATE_SHIFT_ID: ShiftType.LATE,
            NIGHT_SHIFT_ID: ShiftType.NIGHT,
        }
    ),
    staff_level_by_profession_code=STAFF_LEVEL_BY_PROFESSION_CODE,
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
            "U": AvailabilityType.VACATION,  # Urlaub
            "ZU": AvailabilityType.VACATION,  # Zustatzurlaub
            # Conservative hard blockers until TimeOffice/domain semantics are confirmed.
            "SC": AvailabilityType.UNAVAILABLE,  # Schulung
            "EZ": AvailabilityType.UNAVAILABLE,  # Elternzeit
            "RE": AvailabilityType.UNAVAILABLE,  # Reha
            "FI": AvailabilityType.UNAVAILABLE,  # Freistellung
            "AZV": AvailabilityType.UNAVAILABLE,  # Arbeitszeitverkürzung - vermutlich unavailable
            "K": AvailabilityType.UNAVAILABLE,  # Vermutlich Krank
            "TB": AvailabilityType.UNAVAILABLE,  # Ungeklärt
            "SO": AvailabilityType.UNAVAILABLE,  # Ungeklärt
            "KK": AvailabilityType.UNAVAILABLE,  # Krank
        }
    ),
    ignored_availability_absence_codes=frozenset(
        {
            # Existing roster free/reduction markers.
            # They must not block solve-from-scratch.
            "FR",  # geplanter Freier Tag - Soll der als Urlaub oder unavailable gehändelt werden
        }
    ),
    monthly_target_work_account_id=MONTHLY_TARGET_WORK_ACCOUNT_ID,
    monthly_actual_work_account_id=MONTHLY_ACTUAL_WORK_ACCOUNT_ID,
    credited_absence_code_by_account_id=MappingProxyType(
        {
            VACATION_CREDIT_ACCOUNT_ID: "U",
            INTERNAL_TRAINING_CREDIT_ACCOUNT_ID: "FI",
            EXTERNAL_TRAINING_CREDIT_ACCOUNT_ID: "FE",
            SCHOOL_CREDIT_ACCOUNT_ID: "SC",
        }
    ),
)
