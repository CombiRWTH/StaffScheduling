import {IGlobalWishesAndBlockedRepository} from '@/application/ports/global-wishes-and-blocked.repository';
import {IWishesAndBlockedRepository} from '@/application/ports/wishes-and-blocked.repository';

export interface IDeleteGlobalWishesUseCase {
    (input: { caseId: number; monthYear: string; key: number }): Promise<void>;
}

export function makeDeleteGlobalWishesUseCase(
    globalWishesRepository: IGlobalWishesAndBlockedRepository,
    wishesRepository: IWishesAndBlockedRepository
): IDeleteGlobalWishesUseCase {
    return async ({caseId, monthYear, key}) => {
        // Delete monthly wishes first, then the global entry
        await wishesRepository.delete(caseId, monthYear, key);
        await globalWishesRepository.delete(caseId, monthYear, key);
    };
}
