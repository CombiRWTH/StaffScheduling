import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {IWishesAndBlockedRepository} from '@/application/ports/wishes-and-blocked.repository';

export interface IUpdateWishesUseCase {
    (input: { caseId: number; monthYear: string; key: number; data: Partial<WishesAndBlockedEmployee> }): Promise<void>;
}

export function makeUpdateWishesUseCase(
    wishesRepository: IWishesAndBlockedRepository
): IUpdateWishesUseCase {
    return async ({caseId, monthYear, key, data}) => {
        return wishesRepository.update(caseId, monthYear, key, data);
    };
}
