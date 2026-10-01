import { IWishesAndBlockedRepository } from "@/application/ports/wishes-and-blocked.repository";

export interface IDeleteWishesUseCase {
  (input: { caseId: number; monthYear: string; key: number }): Promise<void>;
}

export function makeDeleteWishesUseCase(wishesRepository: IWishesAndBlockedRepository): IDeleteWishesUseCase {
  return async ({ caseId, monthYear, key }) => {
    return wishesRepository.delete(caseId, monthYear, key);
  };
}
