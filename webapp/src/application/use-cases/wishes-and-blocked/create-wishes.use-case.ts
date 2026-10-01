import {WishesAndBlockedEmployee} from '@/entities/models/wishes-and-blocked.model';
import {IWishesAndBlockedRepository} from '@/application/ports/wishes-and-blocked.repository';

export interface ICreateWishesUseCase {
    (input: { caseId: number; monthYear: string; entry: WishesAndBlockedEmployee }): Promise<void>;
}

export function makeCreateWishesUseCase(
    wishesRepository: IWishesAndBlockedRepository
): ICreateWishesUseCase {
    return async ({caseId, monthYear, entry}) => {
        return wishesRepository.create(caseId, monthYear, entry);
    };
}
