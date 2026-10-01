import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {ResourceNotFoundError} from '@/entities/errors/base.errors';
import {IWishesAndBlockedRepository} from '@/application/ports/wishes-and-blocked.repository';

export interface IGetWishesByKeyUseCase {
    (input: { caseId: number; monthYear: string; key: number }): Promise<WishesAndBlockedEmployee>;
}

export function makeGetWishesByKeyUseCase(
    wishesRepository: IWishesAndBlockedRepository
): IGetWishesByKeyUseCase {
    return async ({caseId, monthYear, key}) => {
        const entry = await wishesRepository.getByKey(caseId, monthYear, key);
        if (!entry) throw new ResourceNotFoundError(`Wishes entry with key ${key} not found`);
        return entry;
    };
}
