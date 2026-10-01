import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";
import { IWishesAndBlockedRepository } from "@/application/ports/wishes-and-blocked.repository";

export interface ICreateGlobalWishesUseCase {
  (input: { caseId: number; monthYear: string; entry: WishesAndBlockedEmployee }): Promise<void>;
}

export function makeCreateGlobalWishesUseCase(
  globalWishesRepository: IGlobalWishesAndBlockedRepository,
  wishesRepository: IWishesAndBlockedRepository,
): ICreateGlobalWishesUseCase {
  return async ({ caseId, monthYear, entry }) => {
    // Remove any existing monthly entry first, then create gw and generate fresh mw
    await wishesRepository.delete(caseId, monthYear, entry.key);
    await globalWishesRepository.create(caseId, monthYear, entry);
    await wishesRepository.generateFromGlobal(caseId, monthYear, entry);
  };
}
