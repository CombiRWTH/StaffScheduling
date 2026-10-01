import type {
    IUpdateGlobalWishesTemplateUseCase
} from '@/application/use-cases/templates/global-wishes/update-global-wishes-template.use-case';
import type {GlobalWishesTemplateContent, Template} from '@/entities/models/template.model';
import {isDomainError} from '@/entities/errors/base.errors';

export interface IUpdateGlobalWishesTemplateController {
    (input: {
        caseId: number;
        templateId: string;
        data: { content?: GlobalWishesTemplateContent; description?: string };
    }): Promise<{ data: Template<GlobalWishesTemplateContent> } | { error: string }>;
}

export function makeUpdateGlobalWishesTemplateController(
    updateGlobalWishesTemplateUseCase: IUpdateGlobalWishesTemplateUseCase
): IUpdateGlobalWishesTemplateController {
    return async ({caseId, templateId, data}) => {
        try {
            const template = await updateGlobalWishesTemplateUseCase({caseId, templateId, data});
            return {data: template};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
