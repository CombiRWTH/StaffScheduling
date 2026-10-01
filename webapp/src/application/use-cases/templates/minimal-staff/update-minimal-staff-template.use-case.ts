import {IMinimalStaffTemplateRepository} from '@/application/ports/minimal-staff-template.repository';
import {Template} from '@/entities/models/template.model';
import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {TemplateNotFoundError} from '@/entities/errors/template.errors';

export interface IUpdateMinimalStaffTemplateUseCase {
    (input: {
        caseId: number;
        templateId: string;
        data: { content?: MinimalStaffRequirements; description?: string };
    }): Promise<Template<MinimalStaffRequirements>>;
}

export function makeUpdateMinimalStaffTemplateUseCase(
    repository: IMinimalStaffTemplateRepository
): IUpdateMinimalStaffTemplateUseCase {
    return async ({caseId, templateId, data}) => {
        try {
            return await repository.update(caseId, templateId, data);
        } catch {
            throw new TemplateNotFoundError(templateId);
        }
    };
}
