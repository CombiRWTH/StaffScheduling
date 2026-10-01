import {z} from 'zod';

export const SolverCommandTypeSchema = z.enum([
    'fetch',
    'solve',
    'solve-multiple',
    'insert',
    'delete',
]);

export type SolverCommandType = z.infer<typeof SolverCommandTypeSchema>;

export const SolverJobStatusSchema = z.enum(['accepted', 'running', 'succeeded', 'completed', 'failed']);
export type SolverJobStatus = z.infer<typeof SolverJobStatusSchema>;

export const SolverUnitParamSchema = z.union([
    z.number(),
    z.array(z.number().int().positive()).min(1),
]);

export type SolverUnitParam = z.infer<typeof SolverUnitParamSchema>;

export const BaseSolverParamsSchema = z.object({
    unit: SolverUnitParamSchema,
    start: z.string(),
    end: z.string(),
});

export type BaseSolverParams = z.infer<typeof BaseSolverParamsSchema>;

export const FetchParamsSchema = BaseSolverParamsSchema;
export type FetchParams = z.infer<typeof FetchParamsSchema>;

export const SolveParamsSchema = BaseSolverParamsSchema.extend({
    timeout: z.number().optional(),
});

export type SolveParams = z.infer<typeof SolveParamsSchema>;

export const SolveMultipleParamsSchema = BaseSolverParamsSchema.extend({
    timeout: z.number().optional(),
});

export type SolveMultipleParams = z.infer<typeof SolveMultipleParamsSchema>;

export const InsertParamsSchema = BaseSolverParamsSchema;
export type InsertParams = z.infer<typeof InsertParamsSchema>;

export const DeleteParamsSchema = BaseSolverParamsSchema;
export type DeleteParams = z.infer<typeof DeleteParamsSchema>;

export const SolverParamsSchema = z.union([
    FetchParamsSchema,
    SolveParamsSchema,
    SolveMultipleParamsSchema,
    InsertParamsSchema,
    DeleteParamsSchema,
]);

export type SolverParams = z.infer<typeof SolverParamsSchema>;

export const PythonCommandResultSchema = z.object({
    success: z.boolean(),
    consoleOutput: z.string(),
    exitCode: z.number(),
    duration: z.number(),
});

export type PythonCommandResult = z.infer<typeof PythonCommandResultSchema>;

export const SolverJobSchema = z.object({
    id: z.string(),
    backendJobId: z.string().optional(),
    type: SolverCommandTypeSchema,
    status: SolverJobStatusSchema,
    caseId: z.number(),
    params: SolverParamsSchema,
    // Previously CLI-specific; now optional for backward compatibility.
    consoleOutput: z.string().optional(),
    exitCode: z.number().optional(),
    // Generic error message supported by all solver implementations.
    error: z.string().optional(),
    createdAt: z.string(),
    completedAt: z.string().optional(),
    duration: z.number().optional(),
    result: z.unknown().optional(),
    metadata: z.object({
        solutionsGenerated: z.number().optional(),
        expectedSolutions: z.number().optional(),
        feasibleSolutions: z.array(z.number()).optional(),
    }).optional(),
});

export type SolverJob = z.infer<typeof SolverJobSchema>;

export const JobHistoryDataSchema = z.object({
    jobs: z.array(SolverJobSchema),
});

export type JobHistoryData = z.infer<typeof JobHistoryDataSchema>;

export const SolveMultipleResultSchema = z.object({
    solutionsGenerated: z.number(),
    scheduleFiles: z.array(z.string()),
    commandResult: PythonCommandResultSchema,
});

export type SolveMultipleResult = z.infer<typeof SolveMultipleResultSchema>;

// ---- Result types (returned by controllers / used in server actions) ----

/**
 * Result of the solver configuration validation.
 * Mirrors the shape produced by ISolverService.validateConfig().
 */
export interface SolverConfigResult {
    isValid: boolean;
    isEnabled: boolean;
    errors: string[];
    warnings: string[];
    pythonExecutable: string;
    staffSchedulingPath: string;
    executionTest: {
        success: boolean;
        message: string;
        details?: string;
    } | null;
}

/**
 * Summary of schedules generated during a solve-multiple run.
 */
export interface SolveMultipleScheduleInfo {
    solutionsGenerated: number;
    scheduleFiles: string[];
    feasibleSolutions: number[];
}

/**
 * Result of persisting a solver solution file.
 */
export interface SaveSolutionResult {
    success: boolean;
    filename: string;
    path: string;
}

/**
 * Result of importing a solver solution into the schedule store.
 */
export interface ImportSolutionResult {
    success: boolean;
    scheduleId: string;
    filename: string;
    message: string;
}
