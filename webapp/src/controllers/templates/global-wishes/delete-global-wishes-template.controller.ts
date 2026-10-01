import type {
    IDeleteGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/delete-global-wishes-template.use-case';
import {isDomainError} from '@/entities/errors/base.errors';

export interface IDeleteGlobalWishesTemplateController {
    (input: { caseId: number; templateId: string }): Promise<{ data: { success: boolean } } | { error: string }>;
}

export function makeDeleteGlobalWishesTemplateController(
    deleteGlobalWishesTemplateUseCase: IDeleteGlobalWishesTemplateUseCase
): IDeleteGlobalWishesTemplateController {
    return async ({caseId, templateId}) => {
        try {
            await deleteGlobalWishesTemplateUseCase({caseId, templateId});
            return {data: {success: true}};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
