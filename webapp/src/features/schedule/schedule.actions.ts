'use server';

import {revalidatePath} from 'next/cache';
import {getInjection} from '@/di/container';
import type {SchedulesMetadata, ScheduleSolutionRaw} from '@/entities/models/schedule.model';
import type {ActionResult} from '@/entities/models/action-result.model';
import {writeScheduleToTimeOfficeDb} from '@/infrastructure/persistence/lowdb/schedule.db';

export async function getSchedulesMetadataAction(caseId: number, monthYear: string): Promise<SchedulesMetadata> {
    const controller = getInjection('IGetSchedulesMetadataController');
    const result = await controller({caseId, monthYear});
    if ('error' in result) throw new Error(result.error);
    return result.data;
}

export async function getSelectedScheduleAction(caseId: number, monthYear: string): Promise<{
    solution: ScheduleSolutionRaw | null
}> {
    const controller = getInjection('IGetSelectedScheduleController');
    const result = await controller({caseId, monthYear});
    if ('error' in result) throw new Error(result.error);
    return {solution: result.data};
}

export async function getScheduleByIdAction(caseId: number, monthYear: string, scheduleId: string): Promise<{
    solution: ScheduleSolutionRaw | null;
    description?: string;
    generatedAt?: string;
}> {
    const scheduleController = getInjection('IGetScheduleController');
    const scheduleResult = await scheduleController({caseId, monthYear, scheduleId});

    if ('error' in scheduleResult) {
        throw new Error('Schedule not found');
    }

    const metadataController = getInjection('IGetSchedulesMetadataController');
    const metadataResult = await metadataController({caseId, monthYear});
    const scheduleMetadata = 'data' in metadataResult
        ? metadataResult.data.schedules.find(s => s.scheduleId === scheduleId)
        : undefined;

    return {
        solution: scheduleResult.data,
        description: scheduleMetadata?.description,
        generatedAt: scheduleMetadata?.generatedAt,
    };
}

export async function writeScheduleToTimeOfficeAction(
    caseId: number,
    monthYear: string,
    scheduleId: string,
): Promise<ActionResult> {
    try {
        const controller = getInjection('IGetScheduleController');
        const result = await controller({caseId, monthYear, scheduleId});

        if ('error' in result) return {success: false, error: result.error};
        if (!result.data) return {success: false, error: 'Dienstplan wurde nicht gefunden.'};

        await writeScheduleToTimeOfficeDb(caseId, monthYear, result.data);
        return {success: true, data: undefined};
    } catch (error) {
        return {
            success: false,
            error: error instanceof Error ? error.message : 'Dienstplan konnte nicht gespeichert werden.',
        };
    }
}

export async function saveScheduleAction(
    caseId: number,
    monthYear: string,
    scheduleId: string,
    solution: ScheduleSolutionRaw,
    description?: string,
    autoSelect: boolean = false
): Promise<ActionResult> {
    const saveController = getInjection('ISaveScheduleController');
    const result = await saveController({caseId, monthYear, scheduleId, solution, description});
    if ('error' in result) return {success: false, error: result.error};

    if (autoSelect) {
        const selectController = getInjection('ISelectScheduleController');
        await selectController({caseId, monthYear, scheduleId});
    }

    revalidatePath('/schedule');
    return {success: true, data: undefined};
}

export async function selectScheduleAction(caseId: number, monthYear: string, scheduleId: string): Promise<ActionResult> {
    const controller = getInjection('ISelectScheduleController');
    const result = await controller({caseId, monthYear, scheduleId});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/schedule');
    return {success: true, data: undefined};
}

export async function deleteScheduleAction(caseId: number, monthYear: string, scheduleId: string): Promise<ActionResult> {
    const controller = getInjection('IDeleteScheduleController');
    const result = await controller({caseId, monthYear, scheduleId});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/schedule');
    return {success: true, data: undefined};
}

export async function updateScheduleMetadataAction(
    caseId: number,
    monthYear: string,
    scheduleId: string,
    updates: { description?: string; comment?: string }
): Promise<ActionResult> {
    const controller = getInjection('IUpdateScheduleMetadataController');
    const result = await controller({caseId, monthYear, scheduleId, updates});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/schedule');
    return {success: true, data: undefined};
}
