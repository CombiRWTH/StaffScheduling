import {z} from 'zod';

export const WishesAndBlockedEmployeeSchema = z.object({
    key: z.number(),
    firstname: z.string(),
    name: z.string(),
    wish_days: z.array(z.number()).optional().default([]),
    wish_shifts: z.array(z.tuple([z.number(), z.string()])).optional().default([]),
    work_days: z.array(z.number()).optional().default([]),
    work_shifts: z.array(z.tuple([z.number(), z.string()])).optional().default([]),
    blocked_days: z.array(z.number()).optional().default([]),
    blocked_shifts: z.array(z.tuple([z.number(), z.string()])).optional().default([]),
});

export type WishesAndBlockedEmployee = z.infer<typeof WishesAndBlockedEmployeeSchema>;

export const WishesAndBlockedDatabaseSchema = z.object({
    employees: z.array(WishesAndBlockedEmployeeSchema),
});

export type WishesAndBlockedDatabase = z.infer<typeof WishesAndBlockedDatabaseSchema>;

export const GlobalWishesAndBlockedDatabaseSchema = z.object({
    employees: z.array(WishesAndBlockedEmployeeSchema),
});

export type GlobalWishesAndBlockedDatabase = z.infer<typeof GlobalWishesAndBlockedDatabaseSchema>;
