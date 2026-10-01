import {z} from 'zod';

export const ShiftTypeSchema = z.enum(['F', 'Z', 'S', 'N']);
export type ShiftType = z.infer<typeof ShiftTypeSchema>;

export const WeekDaySchema = z.enum(['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So']);
export type WeekDay = z.infer<typeof WeekDaySchema>;

export const EmployeeCategorySchema = z.enum(['Fachkraft', 'Azubi', 'Hilfskraft']);
export type EmployeeCategory = z.infer<typeof EmployeeCategorySchema>;

export const DayRequirementsSchema = z.object({
    F: z.number(),
    Z: z.number(),
    S: z.number(),
    N: z.number(),
});

export type DayRequirements = z.infer<typeof DayRequirementsSchema>;

export const CategoryRequirementsSchema = z.object({
    Mo: DayRequirementsSchema,
    Di: DayRequirementsSchema,
    Mi: DayRequirementsSchema,
    Do: DayRequirementsSchema,
    Fr: DayRequirementsSchema,
    Sa: DayRequirementsSchema,
    So: DayRequirementsSchema,
});

export type CategoryRequirements = z.infer<typeof CategoryRequirementsSchema>;

export const MinimalStaffRequirementsSchema = z.object({
    Fachkraft: CategoryRequirementsSchema,
    Azubi: CategoryRequirementsSchema,
    Hilfskraft: CategoryRequirementsSchema,
});

export type MinimalStaffRequirements = z.infer<typeof MinimalStaffRequirementsSchema>;
