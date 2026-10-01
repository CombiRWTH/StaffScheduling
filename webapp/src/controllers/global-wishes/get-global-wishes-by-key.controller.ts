import type {
    IGetGlobalWishesByKeyUseCase
} from '@/application/use-cases/global-wishes/get-global-wishes-by-key.use-case';
import type {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {isDomainError} from '@/entities/errors/base.errors';
import {validateMonthYear} from '@/entities/validation/input-validators';

export interface IGetGlobalWishesByKeyController {
    (input: { caseId: number; monthYear: string; key: number }): Promise<
        { data: WishesAndBlockedEmployee } | { error: string }
    >;
}

export function makeGetGlobalWishesByKeyController(
    getGlobalWishesByKeyUseCase: IGetGlobalWishesByKeyUseCase
): IGetGlobalWishesByKeyController {
    return async ({caseId, monthYear, key}) => {
        try {
            validateMonthYear(monthYear);
            const wishes = await getGlobalWishesByKeyUseCase({caseId, monthYear, key});
            return {data: wishes};
        } catch (error) {
            if (isDomainError(error)) return {error: error.message};
            throw error;
        }
    };
}
