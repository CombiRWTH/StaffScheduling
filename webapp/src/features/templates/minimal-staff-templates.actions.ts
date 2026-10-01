'use server';

import {revalidatePath} from 'next/cache';
import {getInjection} from '@/di/container';
import type {Template, TemplateSummary} from '@/entities/models/template.model';
import type {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';
import type {ActionResult} from '@/entities/models/action-result.model';

export async function listMinimalStaffTemplatesAction(caseId: number): Promise<TemplateSummary[]> {
    const controller = getInjection('IListMinimalStaffTemplatesController');
    const result = await controller({caseId});
    if ('error' in result) throw new Error(result.error);
    return result.data;
}

export async function getMinimalStaffTemplateAction(caseId: number, templateId: string): Promise<ActionResult<Template<MinimalStaffRequirements>>> {
    const controller = getInjection('IGetMinimalStaffTemplateController');
    const result = await controller({caseId, templateId});
    if ('error' in result) return {success: false, error: result.error};
    return {success: true, data: result.data};
}

export async function createMinimalStaffTemplateAction(caseId: number, content: MinimalStaffRequirements, description: string): Promise<ActionResult<TemplateSummary>> {
    const controller = getInjection('ICreateMinimalStaffTemplateController');
    const result = await controller({caseId, content, description});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/templates/minimal-staff');
    return {success: true, data: result.data};
}

export async function updateMinimalStaffTemplateAction(
    caseId: number,
    templateId: string,
    data: { content?: MinimalStaffRequirements; description?: string }
): Promise<ActionResult<Template<MinimalStaffRequirements>>> {
    const controller = getInjection('IUpdateMinimalStaffTemplateController');
    const result = await controller({caseId, templateId, data});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/templates/minimal-staff');
    return {success: true, data: result.data};
}

export async function deleteMinimalStaffTemplateAction(caseId: number, templateId: string): Promise<ActionResult> {
    const controller = getInjection('IDeleteMinimalStaffTemplateController');
    const result = await controller({caseId, templateId});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/templates/minimal-staff');
    return {success: true, data: undefined};
}
