import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";
import { IWishesAndBlockedRepository } from "@/application/ports/wishes-and-blocked.repository";

export interface IUpdateGlobalWishesUseCase {
  (input: { caseId: number; monthYear: string; key: number; data: Partial<WishesAndBlockedEmployee> }): Promise<void>;
}

export function makeUpdateGlobalWishesUseCase(
  globalWishesRepository: IGlobalWishesAndBlockedRepository,
  wishesRepository: IWishesAndBlockedRepository,
): IUpdateGlobalWishesUseCase {
  return async ({ caseId, monthYear, key, data }) => {
    // Delete monthly entry, update gw, then regenerate monthly from the new gw
    await wishesRepository.delete(caseId, monthYear, key);
    await globalWishesRepository.update(caseId, monthYear, key, data);
    const updated = await globalWishesRepository.getByKey(caseId, monthYear, key);
    if (updated) {
      await wishesRepository.generateFromGlobal(caseId, monthYear, updated);
    }
  };
}
