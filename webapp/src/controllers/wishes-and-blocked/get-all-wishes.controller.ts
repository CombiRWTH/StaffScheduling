import type { IGetAllWishesUseCase } from "@/application/use-cases/wishes-and-blocked/get-all-wishes.use-case";
import type { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetAllWishesController {
  (input: { caseId: number; monthYear: string }): Promise<{ data: WishesAndBlockedEmployee[] } | { error: string }>;
}

export function makeGetAllWishesController(getAllWishesUseCase: IGetAllWishesUseCase): IGetAllWishesController {
  return async ({ caseId, monthYear }) => {
    try {
      validateMonthYear(monthYear);
      const wishes = await getAllWishesUseCase({ caseId, monthYear });
      return { data: wishes };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
