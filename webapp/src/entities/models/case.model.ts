import {z} from 'zod';

export const CaseSchema = z.object({
    caseId: z.number(),
    monthYear: z.string(),
    month: z.number(),
    year: z.number(),
});

export type Case = z.infer<typeof CaseSchema>;

export const CaseUnitSchema = z.object({
    unitId: z.number(),
    months: z.array(z.string()),
});

export type CaseUnit = z.infer<typeof CaseUnitSchema>;
