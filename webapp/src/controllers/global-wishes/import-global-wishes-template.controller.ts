import {z} from 'zod';
import type {
    IImportGlobalWishesTemplateUseCase
} from '@/application/use-cases/global-wishes/import-global-wishes-template.use-case';
import {isDomainError} from '@/entities/errors/base.errors';

const ImportGlobalWishesTemplateInputSchema = z.object({
    caseId: z.number().int().positive(),
    monthYear: z.string().min(1),
    templateId: z.string().min(1),
});

export interface IImportGlobalWishesTemplateController {
    (input: {
        caseId: number;
        monthYear: string;
        templateId: string;
    }): Promise<
        | { data: { matchCount: number; totalCount: number; unmatchedCount: number } }
        | { error: string }
    >;
}

export function makeImportGlobalWishesTemplateController(
    importGlobalWishesTemplateUseCase: IImportGlobalWishesTemplateUseCase
): IImportGlobalWishesTemplateController {
    return async (rawInput) => {
        try {
            const input = ImportGlobalWishesTemplateInputSchema.parse(rawInput);
            const result = await importGlobalWishesTemplateUseCase(input);
            return {data: result};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            if (error instanceof z.ZodError) return {error: error.message};
            throw error;
        }
    };
}
