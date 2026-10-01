import {IWeightsTemplateRepository} from '@/application/ports/weights-template.repository';
import {TemplateSummary} from '@/entities/models/template.model';

export interface IListWeightsTemplatesUseCase {
    (input: { caseId: number }): Promise<TemplateSummary[]>;
}

export function makeListWeightsTemplatesUseCase(
    repository: IWeightsTemplateRepository
): IListWeightsTemplatesUseCase {
    return async ({caseId}) => {
        return repository.list(caseId);
    };
}
