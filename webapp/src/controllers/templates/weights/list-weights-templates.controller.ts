import type {
    IListWeightsTemplatesUseCase
} from '@/application/use-cases/templates/weights/list-weights-templates.use-case';
import type {TemplateSummary} from '@/entities/models/template.model';
import {isDomainError} from '@/entities/errors/base.errors';

export interface IListWeightsTemplatesController {
    (input: { caseId: number }): Promise<{ data: TemplateSummary[] } | { error: string }>;
}

export function makeListWeightsTemplatesController(
    listWeightsTemplatesUseCase: IListWeightsTemplatesUseCase
): IListWeightsTemplatesController {
    return async ({caseId}) => {
        try {
            const templates = await listWeightsTemplatesUseCase({caseId});
            return {data: templates};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
