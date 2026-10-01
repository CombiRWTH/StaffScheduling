import type {IUpdateWishesUseCase} from '@/application/use-cases/wishes-and-blocked/update-wishes.use-case';
import type {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IUpdateWishesController {
    (input: { caseId: number; monthYear: string; key: number; data: Partial<WishesAndBlockedEmployee> }): Promise<
        { data: void } | { error: string }
    >;
}

export function makeUpdateWishesController(
    updateWishesUseCase: IUpdateWishesUseCase
): IUpdateWishesController {
    return async ({caseId, monthYear, key, data}) => {
        try {
            validateMonthYear(monthYear);
            await updateWishesUseCase({caseId, monthYear, key, data});
            return {data: undefined};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
