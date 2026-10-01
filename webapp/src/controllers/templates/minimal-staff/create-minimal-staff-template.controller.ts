import type {
    ICreateMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/create-minimal-staff-template.use-case';
import type {TemplateSummary} from '@/entities/models/template.model';
import type {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {isDomainError} from '@/entities/errors/base.errors';

export interface ICreateMinimalStaffTemplateController {
    (input: { caseId: number; content: MinimalStaffRequirements; description: string }): Promise<{ data: TemplateSummary } | { error: string }>;
}

export function makeCreateMinimalStaffTemplateController(
    createMinimalStaffTemplateUseCase: ICreateMinimalStaffTemplateUseCase
): ICreateMinimalStaffTemplateController {
    return async ({caseId, content, description}) => {
        try {
            const summary = await createMinimalStaffTemplateUseCase({caseId, content, description});
            return {data: summary};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
