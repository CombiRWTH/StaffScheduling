import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";

export interface IGetAllGlobalWishesUseCase {
  (input: { caseId: number; monthYear: string }): Promise<WishesAndBlockedEmployee[]>;
}

export function makeGetAllGlobalWishesUseCase(
  globalWishesRepository: IGlobalWishesAndBlockedRepository,
): IGetAllGlobalWishesUseCase {
  return async ({ caseId, monthYear }) => {
    return globalWishesRepository.getAll(caseId, monthYear);
  };
}
