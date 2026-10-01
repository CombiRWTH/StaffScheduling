import type { IGetWishesByKeyUseCase } from "@/application/use-cases/wishes-and-blocked/get-wishes-by-key.use-case";
import type { WishesAndBlockedEmployee } from "@/entities/models/wishes-and-blocked.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetWishesByKeyController {
  (input: {
    caseId: number;
    monthYear: string;
    key: number;
  }): Promise<{ data: WishesAndBlockedEmployee } | { error: string }>;
}

export function makeGetWishesByKeyController(getWishesByKeyUseCase: IGetWishesByKeyUseCase): IGetWishesByKeyController {
  return async ({ caseId, monthYear, key }) => {
    try {
      validateMonthYear(monthYear);
      const wishes = await getWishesByKeyUseCase({ caseId, monthYear, key });
      return { data: wishes };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
