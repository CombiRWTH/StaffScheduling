import {z} from 'zod';

export const EmployeeSchema = z.object({
    key: z.number(),
    firstname: z.string(),
    name: z.string(),
    type: z.string(),
});

export type Employee = z.infer<typeof EmployeeSchema>;

export const EmployeeDatabaseSchema = z.object({
    employees: z.array(EmployeeSchema),
});

export type EmployeeDatabase = z.infer<typeof EmployeeDatabaseSchema>;
