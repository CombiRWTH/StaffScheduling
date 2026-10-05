from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from app.domain.availability import AvailabilityType
from app.domain.employee import StaffLevel
from app.domain.planning_unit import PlanningUnitId, PlanningUnitType
from app.domain.shift import ShiftId, ShiftType

# TPlan.RefPlanungsIntervalle value for monthly planning.
MONTHLY_PLANNING_INTERVAL_ID = 1

# TPlan.RefStati value for the editable target roster used as planning input.
TARGET_PLANNING_STATUS_ID = 20

# TPlan.RefStati value of plans whose worked roster rows are trusted context around a month.
TRUSTED_CONTEXT_STATUS_ID = 30

# TPlanPersonalKommtGeht.Info of the duty rows this application publishes; only these rows are its output.
GENERATED_DUTY_INFO = "StaffScheduling"

# TPersonalKontenJeMonat.RefKonten for planned monthly target hours.
MONTHLY_TARGET_WORK_ACCOUNT_ID = 1

# TPersonalKontenJeMonat.RefKonten for current monthly actual hours.
MONTHLY_ACTUAL_WORK_ACCOUNT_ID = 55

# TPersonalKontenJeTag.RefKonten of the daily absence-hour accounts that credit work.
VACATION_CREDIT_ACCOUNT_ID = 85  # U_STD, ABW: Urlaub Std.
INTERNAL_TRAINING_CREDIT_ACCOUNT_ID = 93  # FI_STD, ABW: Fortbildung intern Std.
EXTERNAL_TRAINING_CREDIT_ACCOUNT_ID = 95  # FE_STD, ABW: Fortbildung extern Std.
SCHOOL_CREDIT_ACCOUNT_ID = 97  # ST_STD, ABW: Schule Stunden

# TDienste.Prim values of the reduced reference shifts; the only shift IDs the planning model uses.
# Other rows share the codes (F 3000; S 2449, 3001; N 2011, 3002) and the day shift T (1410) is not one;
# roster rows with them are not reference duties, so a trusted context duty using one stops generation.
EARLY_SHIFT_ID = 1113  # F
LATE_SHIFT_ID = 1605  # S
NIGHT_SHIFT_ID = 1690  # N
INTERMEDIATE_SHIFT_ID = 1453  # Z


@dataclass(frozen=True, slots=True)
class TimeOfficeFacts:
    """Source assumptions and reduced-domain mappings for the TimeOffice adapter.

    Facts contain adapter constants and source-to-domain mappings only. They do
    not perform checks themselves; the query functions use them and fail loudly
    on unmapped or drifted source semantics.
    """

    monthly_planning_interval_id: int
    target_planning_status_id: int
    trusted_context_status_id: int
    generated_duty_info: str

    planning_unit_type_by_id: Mapping[PlanningUnitId, PlanningUnitType]

    reference_shift_type_by_id: Mapping[ShiftId, ShiftType]

    staff_level_by_profession_code: Mapping[str, StaffLevel]

    availability_type_by_absence_code: Mapping[str, AvailabilityType]
    ignored_availability_absence_codes: frozenset[str]

    monthly_target_work_account_id: int
    monthly_actual_work_account_id: int

    # Daily absence-hour accounts that credit work, with the absence code they book.
    credited_absence_code_by_account_id: Mapping[int, str]

    @property
    def reference_shift_ids(self) -> frozenset[ShiftId]:
        return frozenset(self.reference_shift_type_by_id)

    @property
    def station_ids(self) -> list[PlanningUnitId]:
        return sorted(unit for unit, kind in self.planning_unit_type_by_id.items() if kind == PlanningUnitType.STATION)


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
        # Unverified assumption.
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
        # Unverified assumption.
        "Pra": StaffLevel.ASSISTANT,  # Praktikant/-in
        # Ausbildung / Praktikum
        "A-31342-005": StaffLevel.TRAINEE,  # A-Notfallsanitäter
        "A-81302-007": StaffLevel.TRAINEE,  # A-Kinderkrankenschwester/-pfleger
        "A-81302-008": StaffLevel.TRAINEE,  # A-Krankenschwester/-pfleger
        "A-81302-014": StaffLevel.TRAINEE,  # A-Pflegeassistent/in
        "A-81302-016": StaffLevel.TRAINEE,  # A-Pflegefachkraft Kinderkrankenpflege
        "A-81302-018": StaffLevel.TRAINEE,  # A-Pflegefachkraft Krankenpflege
        "A-81302-019": StaffLevel.TRAINEE,  # A-Pflegefachkraft Altenpflege
        # Unverified assumption: the code names no profession.
        "-": StaffLevel.TRAINEE,
    }
)

TIMEOFFICE_FACTS = TimeOfficeFacts(
    monthly_planning_interval_id=MONTHLY_PLANNING_INTERVAL_ID,
    target_planning_status_id=TARGET_PLANNING_STATUS_ID,
    trusted_context_status_id=TRUSTED_CONTEXT_STATUS_ID,
    generated_duty_info=GENERATED_DUTY_INFO,
    # TPlanungseinheiten.Prim of the planned units. Supporting another unit means adding it here;
    # see the TimeOffice adapter docs for the checklist.
    planning_unit_type_by_id=MappingProxyType(
        {
            77: PlanningUnitType.STATION,  # PE 77
            78: PlanningUnitType.STATION,  # PE 78
            79: PlanningUnitType.STATION,  # PE 79
            83: PlanningUnitType.STATION,  # PE 83
            85: PlanningUnitType.STATION,  # PE 85
            88: PlanningUnitType.STATION,  # PE 88
            337: PlanningUnitType.STATION,  # PE 337
            68: PlanningUnitType.JUMPER_POOL,  # PE 68
            408: PlanningUnitType.JUMPER_POOL,  # PE 408
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
    availability_type_by_absence_code=MappingProxyType(
        {
            "U": AvailabilityType.VACATION,  # Urlaub
            "ZU": AvailabilityType.VACATION,  # Zusatzurlaub
            "SC": AvailabilityType.UNAVAILABLE,  # Schulung
            "EZ": AvailabilityType.UNAVAILABLE,  # Elternzeit
            "RE": AvailabilityType.UNAVAILABLE,  # Reha
            "FI": AvailabilityType.UNAVAILABLE,  # Freistellung
            "KK": AvailabilityType.UNAVAILABLE,  # Krank
            # Unverified assumptions: meanings unknown, so they block the whole day.
            "AZV": AvailabilityType.UNAVAILABLE,  # presumably Arbeitszeitverkürzung
            "K": AvailabilityType.UNAVAILABLE,  # presumably Krank
            "TB": AvailabilityType.UNAVAILABLE,
            "SO": AvailabilityType.UNAVAILABLE,
        }
    ),
    ignored_availability_absence_codes=frozenset(
        {
            # A planned free day of an existing roster; a schedule made from scratch plans free days itself.
            "FR",  # geplanter freier Tag
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
