import {IMinimalStaffTemplateRepository} from '@/application/ports/minimal-staff-template.repository';
import {TemplateSummary} from '@/entities/models/template.model';
import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';

export interface ICreateMinimalStaffTemplateUseCase {
    (input: { caseId: number; content: MinimalStaffRequirements; description: string }): Promise<TemplateSummary>;
}

export function makeCreateMinimalStaffTemplateUseCase(
    repository: IMinimalStaffTemplateRepository
): ICreateMinimalStaffTemplateUseCase {
    return async ({caseId, content, description}) => {
        return repository.create(caseId, content, description);
    };
}
