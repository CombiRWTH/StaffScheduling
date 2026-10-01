import {z} from 'zod';

export const AvailabilityEmployeeSchema = z.object({
    key: z.number(),
    firstname: z.string(),
    name: z.string(),
    unavailability_days: z.array(z.number()).optional().default([]),
    unavailability_shifts: z.array(z.tuple([z.number(), z.string()])).optional().default([]),
});

export type AvailabilityEmployee = z.infer<typeof AvailabilityEmployeeSchema>;

export const AvailabilityDatabaseSchema = z.object({
    employees: z.array(AvailabilityEmployeeSchema),
});

export type AvailabilityDatabase = z.infer<typeof AvailabilityDatabaseSchema>;

export const AvailabilityApiResponseSchema = z.union([
    AvailabilityDatabaseSchema,
    z.object({
        data: AvailabilityDatabaseSchema,
    }),
]);

export type AvailabilityApiResponse = z.infer<typeof AvailabilityApiResponseSchema>;
