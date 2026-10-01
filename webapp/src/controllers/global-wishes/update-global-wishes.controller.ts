import type { IUpdateGlobalWishesUseCase } from "@/application/use-cases/global-wishes/update-global-wishes.use-case";
import type { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IUpdateGlobalWishesController {
  (input: {
    caseId: number;
    monthYear: string;
    key: number;
    data: Partial<WishesAndBlockedEmployee>;
  }): Promise<{ data: void } | { error: string }>;
}

export function makeUpdateGlobalWishesController(
  updateGlobalWishesUseCase: IUpdateGlobalWishesUseCase,
): IUpdateGlobalWishesController {
  return async ({ caseId, monthYear, key, data }) => {
    try {
      validateMonthYear(monthYear);
      await updateGlobalWishesUseCase({ caseId, monthYear, key, data });
      return { data: undefined };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
