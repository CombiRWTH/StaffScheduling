import { z } from "zod";

const id = z.number().int().positive();
const date = z.iso.date();
const qualification = z.enum(["professional", "assistant", "trainee", "mfa"]);
const unit = z.object({
  planning_unit_id: id,
  display_name: z.string().min(1),
  type: z.enum(["station", "shared_pool"]),
});
const planningMonth = z.object({
  year: z.number().int(),
  month: z.number().int().min(1).max(12),
  start: date,
  end: date,
});
export const PlanningOptionsSchema = z.object({ planning_month: planningMonth, planning_units: z.array(unit) });
export const PlanningInspectionSchema = z.object({
  planning_month: planningMonth,
  selected_station_ids: z.array(id),
  planning_units: z.array(unit),
  employees: z.array(
    z.object({
      employee_id: id,
      display_name: z.string().min(1),
      staff_level: qualification,
      memberships: z.array(
        z.object({
          planning_unit_id: id,
          employee_id: id,
          valid_from: date,
          valid_until: date.nullable(),
          staff_level: qualification,
          is_home: z.boolean(),
          is_replacement: z.boolean(),
        }),
      ),
      account: z.object({
        employee_id: id,
        target_minutes: z.number().int().nonnegative(),
        actual_minutes: z.number().int().nonnegative().nullable(),
        credited_minutes: z.number().int().nonnegative(),
        credit_details: z.array(
          z.object({
            date,
            minutes: z.number().int().nonnegative(),
            kind: z.enum(["approved_absence", "trusted_work"]),
            source: z.string().min(1),
          }),
        ),
        evidence_source: z.string().min(1),
      }),
      hard_restrictions: z.array(
        z.object({
          employee_id: id,
          date,
          availability_type: z.enum(["unavailable", "vacation", "training", "free_day", "available_only"]),
          shift_ids: z.array(id).nullable(),
          reason: z.string().nullable(),
          source: z.string().nullable(),
        }),
      ),
      restrictions_source: z.string().min(1),
    }),
  ),
});
export type PlanningOptions = z.infer<typeof PlanningOptionsSchema>;
export type PlanningInspection = z.infer<typeof PlanningInspectionSchema>;
