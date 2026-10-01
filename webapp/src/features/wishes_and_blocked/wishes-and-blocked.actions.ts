'use server';

import {revalidatePath} from 'next/cache';
import {getInjection} from '@/di/container';
import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import type {ActionResult} from '@/entities/models/action-result.model';

export async function getAllWishesAction(caseId: number, monthYear: string): Promise<WishesAndBlockedEmployee[]> {
    const controller = getInjection('IGetAllWishesController');
    const result = await controller({caseId, monthYear});
    if ('error' in result) throw new Error(result.error);
    return result.data;
}

export async function getWishesByKeyAction(caseId: number, monthYear: string, key: number): Promise<WishesAndBlockedEmployee | null> {
    const controller = getInjection('IGetWishesByKeyController');
    const result = await controller({caseId, monthYear, key});
    if ('error' in result) return null;
    return result.data;
}

export async function createWishesAction(
    caseId: number,
    monthYear: string,
    data: WishesAndBlockedEmployee
): Promise<ActionResult> {
    const controller = getInjection('ICreateWishesController');
    const result = await controller({caseId, monthYear, entry: data});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/wishes-and-blocked');
    return {success: true, data: undefined};
}

export async function updateWishesAction(
    caseId: number,
    monthYear: string,
    key: number,
    data: Partial<Omit<WishesAndBlockedEmployee, 'key'>>
): Promise<ActionResult> {
    const controller = getInjection('IUpdateWishesController');
    const result = await controller({caseId, monthYear, key, data});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/wishes-and-blocked');
    return {success: true, data: undefined};
}

export async function deleteWishesAction(caseId: number, monthYear: string, key: number): Promise<ActionResult> {
    const controller = getInjection('IDeleteWishesController');
    const result = await controller({caseId, monthYear, key});
    if ('error' in result) return {success: false, error: result.error};
    revalidatePath('/wishes-and-blocked');
    return {success: true, data: undefined};
}
