// Response types of the canonical FastAPI planning endpoints.

export type Qualification = "professional" | "assistant" | "trainee" | "mfa";

export interface PlanningMonth {
  year: number;
  month: number;
  start: string;
  end: string;
}

export interface PlanningUnit {
  planning_unit_id: number;
  display_name: string;
  type: "station" | "shared_pool";
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
  staff_level: Qualification;
  is_home: boolean;
  is_replacement: boolean;
}

export interface WorkCredit {
  date: string;
  minutes: number;
  kind: "approved_absence" | "trusted_work";
  source: string;
}

export interface Constraint {
  employee_id: number;
  date: string;
  availability_type: "unavailable" | "vacation" | "training" | "free_day" | "available_only";
  shift_ids: number[] | null;
  reason: string | null;
  source: string | null;
}

export interface Employee {
  employee_id: number;
  display_name: string;
  staff_level: Qualification;
  memberships: Membership[];
  account: {
    target_minutes: number;
    actual_minutes: number | null;
    credited_minutes: number;
    credit_details: WorkCredit[];
    evidence_source: string;
  };
  constraints: Constraint[];
  constraints_source: string;
}

export interface PlanningInspection {
  planning_month: PlanningMonth;
  selected_station_ids: number[];
  /** Pools that station members call home; replacement memberships do not associate a pool. */
  associated_pool_ids: number[];
  planning_units: PlanningUnit[];
  employees: Employee[];
}
