import {IMinimalStaffTemplateRepository} from '@/application/ports/minimal-staff-template.repository';
import {TemplateNotFoundError} from '@/entities/errors/template.errors';

export interface IDeleteMinimalStaffTemplateUseCase {
    (input: { caseId: number; templateId: string }): Promise<void>;
}

export function makeDeleteMinimalStaffTemplateUseCase(
    repository: IMinimalStaffTemplateRepository
): IDeleteMinimalStaffTemplateUseCase {
    return async ({caseId, templateId}) => {
        try {
            await repository.delete(caseId, templateId);
        } catch {
            throw new TemplateNotFoundError(templateId);
        }
    };
}
