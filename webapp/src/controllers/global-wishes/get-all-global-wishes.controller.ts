import type {
    IGetAllGlobalWishesUseCase
} from '@/application/use-cases/global-wishes/get-all-global-wishes.use-case';
import type {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IGetAllGlobalWishesController {
    (input: { caseId: number; monthYear: string }): Promise<
        { data: WishesAndBlockedEmployee[] } | { error: string }
    >;
}

export function makeGetAllGlobalWishesController(
    getAllGlobalWishesUseCase: IGetAllGlobalWishesUseCase
): IGetAllGlobalWishesController {
    return async ({caseId, monthYear}) => {
        try {
            validateMonthYear(monthYear);
            const wishes = await getAllGlobalWishesUseCase({caseId, monthYear});
            return {data: wishes};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
