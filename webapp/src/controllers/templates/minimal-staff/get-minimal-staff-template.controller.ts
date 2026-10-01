import type {
    IGetMinimalStaffTemplateUseCase
} from '@/application/use-cases/templates/minimal-staff/get-minimal-staff-template.use-case';
import type {Template} from '@/entities/models/template.model';
import type {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import {isDomainError} from '@/entities/errors/base.errors';

export interface IGetMinimalStaffTemplateController {
    (input: { caseId: number; templateId: string }): Promise<{ data: Template<MinimalStaffRequirements> } | { error: string }>;
}

export function makeGetMinimalStaffTemplateController(
    getMinimalStaffTemplateUseCase: IGetMinimalStaffTemplateUseCase
): IGetMinimalStaffTemplateController {
    return async ({caseId, templateId}) => {
        try {
            const template = await getMinimalStaffTemplateUseCase({caseId, templateId});
            return {data: template};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
