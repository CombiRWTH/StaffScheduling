import {IGlobalWishesTemplateRepository} from '@/application/ports/global-wishes-template.repository';
import {GlobalWishesTemplateContent, Template} from '@/entities/models/template.model';
import {TemplateNotFoundError} from '@/entities/errors/template.errors';

export interface IGetGlobalWishesTemplateUseCase {
    (input: { caseId: number; templateId: string }): Promise<Template<GlobalWishesTemplateContent>>;
}

export function makeGetGlobalWishesTemplateUseCase(
    repository: IGlobalWishesTemplateRepository
): IGetGlobalWishesTemplateUseCase {
    return async ({caseId, templateId}) => {
        try {
            return await repository.get(caseId, templateId);
        } catch {
            throw new TemplateNotFoundError(templateId);
        }
    };
}
