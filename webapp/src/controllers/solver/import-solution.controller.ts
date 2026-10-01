import { z } from 'zod';
import { isDomainError } from '@/entities/errors/base.errors';
import { validateMonthYear } from '@/entities/validation/input-validators';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';
import type {
    IImportSolutionUseCase,
    ImportSolutionResult,
} from '@/application/use-cases/solver/import-solution.use-case';

const InputSchema = z.object({
    caseId: z.number().int().positive(),
    monthYear: z.string(),
    start: z.string().min(1, 'start date is required'),
    end: z.string().min(1, 'end date is required'),
    solutionType: z.string().min(1, 'solutionType is required'),
    solution: z.unknown(),
});

export interface IImportSolutionController {
    (input: {
        caseId: number;
        monthYear: string;
        start: string;
        end: string;
        solutionType: string;
        solution: ScheduleSolutionRaw;
    }): Promise<{ data: ImportSolutionResult } | { error: string }>;
}

export function makeImportSolutionController(
    importSolutionUseCase: IImportSolutionUseCase
): IImportSolutionController {
    return async (rawInput) => {
        try {
            const input = InputSchema.parse(rawInput);
            validateMonthYear(input.monthYear);
            const result = await importSolutionUseCase({
                ...input,
                solution: input.solution as ScheduleSolutionRaw,
            });
            return { data: result };
        } catch (error) {
            if (isDomainError(error)) return { error: error.message };
            if (error instanceof z.ZodError) return { error: error.issues[0]?.message ?? 'Invalid input' };
            if (error instanceof Error) return { error: error.message };
            throw error;
        }
    };
}
