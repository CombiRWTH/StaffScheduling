import type {
    IListGlobalWishesTemplatesUseCase
} from '@/application/use-cases/templates/global-wishes/list-global-wishes-templates.use-case';
import type {TemplateSummary} from '@/entities/models/template.model';
import {isDomainError} from '@/entities/errors/base.errors';

export interface IListGlobalWishesTemplatesController {
    (input: { caseId: number }): Promise<{ data: TemplateSummary[] } | { error: string }>;
}

export function makeListGlobalWishesTemplatesController(
    listGlobalWishesTemplatesUseCase: IListGlobalWishesTemplatesUseCase
): IListGlobalWishesTemplatesController {
    return async ({caseId}) => {
        try {
            const templates = await listGlobalWishesTemplatesUseCase({caseId});
            return {data: templates};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
