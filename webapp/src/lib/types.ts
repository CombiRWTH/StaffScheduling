// Request and response types of the canonical FastAPI planning endpoints.

export type StaffLevel = "professional" | "assistant" | "trainee" | "mfa";

export interface PlanningMonth {
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
  source: string | null;
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

export interface CalendarDay {
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
  employees: Employee[];
}

export type SolutionStatus = "optimal" | "feasible" | "infeasible" | "model_invalid" | "unknown";

export type Severity = "info" | "warning" | "error";

export interface GeneratedAssignment {
  employee_id: number;
  planning_unit_id: number | null;
  date: string;
  shift_id: number;
  assignment_type: "planned" | "external" | "generated";
}

export interface Solution {
  status: SolutionStatus;
  assignments: GeneratedAssignment[];
  diagnostics: { code: string; severity: Severity; message: string }[];
  /** Post-solve findings of the implemented rules; not an independent schedule check. */
  audit: { findings: { code: string; severity: Severity; message: string }[] };
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
  /** No independent schedule check exists yet. */
  acceptance: "not_assessed";
}
