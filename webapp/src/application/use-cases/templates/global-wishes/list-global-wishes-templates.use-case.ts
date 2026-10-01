import {IGlobalWishesTemplateRepository} from '@/application/ports/global-wishes-template.repository';
import {TemplateSummary} from '@/entities/models/template.model';

export interface IListGlobalWishesTemplatesUseCase {
    (input: { caseId: number }): Promise<TemplateSummary[]>;
}

export function makeListGlobalWishesTemplatesUseCase(
    repository: IGlobalWishesTemplateRepository
): IListGlobalWishesTemplatesUseCase {
    return async ({caseId}) => {
        return repository.list(caseId);
    };
}
