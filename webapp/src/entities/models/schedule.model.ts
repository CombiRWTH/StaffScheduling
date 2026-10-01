import {z} from 'zod';

export const ShiftSchema = z.object({
    id: z.number(),
    name: z.string(),
    abbreviation: z.string(),
    color: z.string(),
    duration: z.number(),
    is_exclusive: z.boolean(),
});

export type Shift = z.infer<typeof ShiftSchema>;

export const ScheduleEmployeeSchema = z.object({
    id: z.number(),
    name: z.string(),
    level: z.string(),
    target_working_time: z.number(),
    wishes: z.object({
        shift_wishes: z.array(z.tuple([z.number(), z.string()])),
        day_off_wishes: z.array(z.number()),
    }),
    vacation_days: z.array(z.number()),
    forbidden_days: z.array(z.number()),
    vacation_shifts: z.array(z.tuple([z.number(), z.string()])),
    forbidden_shifts: z.array(z.tuple([z.number(), z.string()])),
    hidden_actual_working_time: z.number(),
    actual_working_time: z.number(),
    is_hidden_employee: z.boolean(),
});

export type ScheduleEmployee = z.infer<typeof ScheduleEmployeeSchema>;

export const ScheduleStatsSchema = z.object({
    forward_rotation_violations: z.number(),
    consecutive_working_days_gt_5: z.number(),
    no_free_weekend: z.number(),
    consecutive_night_shifts_gt_3: z.number(),
    total_overtime_hours: z.number(),
    no_free_days_around_weekend: z.number(),
    not_free_after_night_shift: z.number(),
    violated_wish_total: z.number(),
});

export type ScheduleStats = z.infer<typeof ScheduleStatsSchema>;

/** Runtime-only type with non-serializable fields (Set, Date). No Zod schema. */
export interface ScheduleSolution {
    variables: Record<string, number>;
    employees: ScheduleEmployee[];
    shifts: Shift[];
    days: Date[];
    stats: ScheduleStats;
    fulfilledDayOffCells: Set<string>;
    fulfilledShiftWishCells: Set<string>;
    allDayOffWishCells: Set<string>;
    allShiftWishColors: Record<string, string[]>;
}

export const ScheduleSolutionRawSchema = z.object({
    variables: z.record(z.string(), z.number()),
    employees: z.array(ScheduleEmployeeSchema),
    shifts: z.array(ShiftSchema),
    days: z.array(z.string()),
    stats: ScheduleStatsSchema,
});

export type ScheduleSolutionRaw = z.infer<typeof ScheduleSolutionRawSchema>;

export const ScheduleMetadataSchema = z.object({
    scheduleId: z.string(),
    description: z.string().optional(),
    generatedAt: z.string(),
    isSelected: z.boolean(),
    comment: z.string().optional(),
    stats: ScheduleStatsSchema,
});

export type ScheduleMetadata = z.infer<typeof ScheduleMetadataSchema>;

export const SchedulesMetadataSchema = z.object({
    schedules: z.array(ScheduleMetadataSchema),
    selectedScheduleId: z.string().nullable(),
});

export type SchedulesMetadata = z.infer<typeof SchedulesMetadataSchema>;

export const ScheduleDatabaseSchema = z.object({
    solution: ScheduleSolutionRawSchema.nullable(),
});

export type ScheduleDatabase = z.infer<typeof ScheduleDatabaseSchema>;
