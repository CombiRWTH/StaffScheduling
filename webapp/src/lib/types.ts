// Request and response types of the canonical FastAPI planning endpoints.

export type StaffLevel = "professional" | "assistant" | "trainee" | "mfa";

interface PlanningMonth {
  year: number;
  month: number;
  start: string;
  end: string;
}

export interface PlanningUnit {
  planning_unit_id: number;
  display_name: string;
  type: "station" | "jumper_pool";
}

export interface PlanningOptions {
  planning_month: PlanningMonth;
  planning_units: PlanningUnit[];
}

export interface Membership {
  planning_unit_id: number;
  employee_id: number;
  valid_from: string;
  valid_until: string | null;
  staff_level: StaffLevel;
  is_home: boolean;
  is_replacement: boolean;
}

export interface WorkCredit {
  date: string;
  minutes: number;
  kind: "approved_absence" | "trusted_work";
  source: string;
}

export type AvailabilityType = "unavailable" | "vacation" | "training" | "free_day" | "available_only";

/** What an employee's availability on one date is; `shift_ids` only for `available_only`. */
export interface AvailabilityEntry {
  availability_type: AvailabilityType;
  shift_ids: number[] | null;
  reason: string | null;
}

/** A date on which an employee must not be planned, or only for `shift_ids`. */
export interface Availability extends AvailabilityEntry {
  employee_id: number;
  date: string;
  /** An approved TimeOffice absence, read-only here; its `reason` is the absence code. */
  native_absence: boolean;
}

export type WishType = "free_day" | "free_shift" | "preferred_day" | "preferred_shift";

export interface WishEntry {
  type: WishType;
  shift_id: number | null;
}

export interface Wish extends WishEntry {
  employee_id: number;
  date: string;
}

export type ShiftType = "early" | "late" | "night" | "intermediate" | "management" | "other";

export interface ShiftOption {
  shift_id: number;
  code: string;
  type: ShiftType;
}

export interface EmployeeSummary {
  employee_id: number;
  display_name: string;
}

export interface EmployeeCalendar {
  employee_id: number;
  planning_month: PlanningMonth;
  /** Approved roster absences; read-only. */
  absences: Availability[];
  availability: Availability[];
  wishes: Wish[];
  calendar: CalendarDay[];
  shifts: ShiftOption[];
}

interface CalendarDay {
  date: string;
  /** ISO weekday, Monday=1 to Sunday=7. */
  weekday: number;
  public_holiday: string | null;
}

/** How many of a qualification one shift needs on one date of the month's station (1–99). */
export interface DemandCell {
  date: string;
  shift_id: number;
  staff_level: StaffLevel;
  required_count: number;
}

export interface MonthlyDemand {
  planning_unit_id: number;
  planning_month: PlanningMonth;
  cells: DemandCell[];
}

export interface DemandConfiguration {
  planning_unit_id: number;
  planning_month: PlanningMonth;
  /** Null until the station month has been saved once. */
  demand: MonthlyDemand | null;
  calendar: CalendarDay[];
  shifts: ShiftOption[];
}

export type DayType = "monday" | "tuesday" | "wednesday" | "thursday" | "friday" | "saturday" | "sunday" | "holiday";

export interface PatternRequirement {
  day_type: DayType;
  shift_id: number;
  staff_level: StaffLevel;
  required_count: number;
}

export interface Employee {
  employee_id: number;
  display_name: string;
  staff_level: StaffLevel;
  memberships: Membership[];
  account: {
    target_minutes: number;
    actual_minutes: number | null;
    credited_minutes: number;
    credit_details: WorkCredit[];
  };
  /** Native absences and project availability of the month. */
  availability: Availability[];
}

export interface PlanningInspection {
  planning_month: PlanningMonth;
  selected_station_ids: number[];
  /** Jumper pools that station members call home; replacement memberships do not associate one. */
  associated_jumper_pool_ids: number[];
  planning_units: PlanningUnit[];
  /** The reference shifts, for naming the allowed shifts of an availability entry. */
  shifts: ShiftOption[];
  employees: Employee[];
}

export type SolutionStatus = "optimal" | "feasible" | "infeasible" | "model_invalid" | "unknown";

type Severity = "info" | "warning" | "error";

interface GeneratedAssignment {
  employee_id: number;
  planning_unit_id: number;
  date: string;
  shift_id: number;
  /** The qualification the duty is credited as towards demand. */
  staff_level: StaffLevel;
}

export type CheckStatus = "accepted" | "rejected" | "incomplete";

export type Rule =
  | "input"
  | "staffing"
  | "eligibility"
  | "one_duty_per_day"
  | "availability"
  | "monthly_balance"
  | "work_and_breaks"
  | "work_average"
  | "rest"
  | "consecutive_nights"
  | "night_recovery"
  | "replacement_rest"
  | "annual_free_sundays";

/** The independent schedule check of a found schedule; computed by the backend, never here. */
export interface ScheduleCheck {
  status: CheckStatus;
  rules: Rule[];
  findings: {
    rule: Rule;
    message: string;
    employee_id: number | null;
    date: string | null;
    planning_unit_id: number | null;
    shift_id: number | null;
  }[];
  not_assessed: {
    rule: Rule;
    reason: string;
    blocking: boolean;
    start: string;
    end: string;
    employee_id: number | null;
  }[];
  scores: {
    gaps: number;
    six_day_windows: number;
    backward_transitions: number;
    isolated_workdays: number;
    back_to_back_weekends: number;
    health_events: number;
    station_transfers: number;
    wish_cost: number;
    balance_deviation_minutes: number;
    surplus_intermediate_duties: number;
  };
  /** Every wish of the input with what the schedule made of it; wishes never bind. */
  wishes: (Wish & { status: WishStatus })[];
  wish_counts: Record<WishStatus, number>;
}

export type WishStatus = "granted" | "denied" | "not_grantable";

export interface Solution {
  status: SolutionStatus;
  wall_time_seconds: number;
  assignments: GeneratedAssignment[];
  diagnostics: { code: string; severity: Severity; message: string }[];
  /** Present with a found schedule only. */
  check: ScheduleCheck | null;
  /** Required slots the schedule leaves unfilled; never published as duties. */
  gaps: { planning_unit_id: number; date: string; shift_id: number; staff_level: StaffLevel; missing_count: number }[];
  /** Every objective tier in solving order; `status` is optimal exactly when every stage is. */
  stages: Stage[];
}

/** The objective tiers, highest priority first; each is a score of the check. */
export type ObjectiveTier =
  | "gaps"
  | "health_events"
  | "station_transfers"
  | "wish_cost"
  | "balance_deviation_minutes"
  | "surplus_intermediate_duties";

/**
 * One objective tier's stage: its value in the schedule (the check's score) and CP-SAT's proven bound, null when
 * the stage found no schedule in its time and kept the previous one.
 */
export interface Stage {
  name: ObjectiveTier;
  status: "optimal" | "feasible";
  value: number;
  best_bound: number | null;
}

/** One generation run: `state` is the job's progress, `solution.status` what the solver found. */
export interface GenerationJob {
  job_id: string;
  request: { planning_unit_ids: number[]; planning_month: PlanningMonth; timeout_seconds: number };
  state: "running" | "completed" | "failed";
  started_at: string;
  finished_at: string | null;
  solution: Solution | null;
  error: string | null;
}

export interface Shift extends ShiftOption {
  /** Active work in local minutes after midnight of the start date; beyond 1440 on the next date. */
  segments: { start_minute: number; end_minute: number }[];
  net_work_minutes: number;
}

/** One duty as the review and `schedule.csv` show it; times are Europe/Berlin with their offset. */
export interface DutyRow {
  employee_id: number;
  employee_name: string;
  date: string;
  weekday: number;
  is_public_holiday: boolean;
  planning_unit_id: number;
  planning_unit_name: string;
  shift_id: number;
  shift_code: string;
  shift_type: ShiftType;
  start_at: string;
  end_at: string;
  net_work_minutes: number;
  staff_level: StaffLevel;
  origin_unit_id: number | null;
  origin_unit_name: string | null;
  origin_unit_type: PlanningUnit["type"] | null;
}

/** One participant's month as the review and `employees.csv` show it; computed by the backend. */
interface EmployeeRow {
  employee_id: number;
  employee_name: string;
  staff_level: StaffLevel;
  planning_month: string;
  target_minutes: number;
  credited_minutes: number;
  generated_minutes: number;
  balance_minutes: number;
  memberships: Membership[];
  hard_availability: Availability[];
  credit_details: WorkCredit[];
}

interface StaffingRow {
  planning_unit_id: number;
  date: string;
  shift_id: number;
  staff_level: StaffLevel;
  required_count: number;
  assigned_count: number;
}

/** Unfilled required slots of one station, date, shift and qualification, as the review and `gaps.csv` show them. */
interface GapRow {
  planning_unit_id: number;
  planning_unit_name: string;
  date: string;
  shift_id: number;
  shift_code: string;
  staff_level: StaffLevel;
  required_count: number;
  assigned_count: number;
  missing_count: number;
}

/** The effective settings of one solve; `policy` holds the rule parameters in minutes and days. */
interface RunConfiguration {
  policy: { balance_tolerance_minutes: number } & Record<string, number>;
  timeout_seconds: number;
  search_workers: number | null;
  random_seed: number | null;
}

/** The latest generated or imported schedule with its independent check and readable tables. */
export interface ScheduleReview {
  source: "generation" | "import";
  received_at: string;
  planning_month: PlanningMonth;
  planning_units: PlanningUnit[];
  shifts: Shift[];
  calendar: CalendarDay[];
  /** Always a found schedule: it has its stages and check. */
  solution: Solution & { check: ScheduleCheck; configuration: RunConfiguration };
  tables: { duties: DutyRow[]; employees: EmployeeRow[]; staffing: StaffingRow[]; gaps: GapRow[] };
}

/** Why the backend refused an uploaded pair of files. */
export type BundleProblem = "malformed" | "mismatch" | "no_schedule" | "policy" | "references" | "check";

/** What a committed publication or clear changed in the named stations' month. */
export interface PublicationResult {
  planning_month: PlanningMonth;
  planning_unit_ids: number[];
  removed_duties: number;
  published_duties: number;
}

/** Why the backend refused to publish the schedule under review. */
export type PublicationProblem = "changed" | "not_accepted" | "conflict" | "read_back";

/** Why the backend rolled back any write: another writer changed the same TimeOffice rows. */
export type WriteProblem = "concurrent";
