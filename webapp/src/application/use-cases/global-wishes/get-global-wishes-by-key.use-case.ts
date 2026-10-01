import { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { ResourceNotFoundError } from "@/entities/errors/base.errors";
import { IGlobalWishesAndBlockedRepository } from "@/application/ports/global-wishes-and-blocked.repository";

export interface IGetGlobalWishesByKeyUseCase {
  (input: { caseId: number; monthYear: string; key: number }): Promise<WishesAndBlockedEmployee>;
}

export function makeGetGlobalWishesByKeyUseCase(
  globalWishesRepository: IGlobalWishesAndBlockedRepository,
): IGetGlobalWishesByKeyUseCase {
  return async ({ caseId, monthYear, key }) => {
    const entry = await globalWishesRepository.getByKey(caseId, monthYear, key);
    if (!entry) throw new ResourceNotFoundError(`Global wishes entry with key ${key} not found`);
    return entry;
  };
}
