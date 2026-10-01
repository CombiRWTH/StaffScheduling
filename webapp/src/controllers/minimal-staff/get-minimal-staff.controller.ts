import type { IGetMinimalStaffUseCase } from "@/application/use-cases/minimal-staff/get-minimal-staff.use-case";
import type { MinimalStaffRequirements } from "@/entities/models/minimal-staff.model";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";

export interface IGetMinimalStaffController {
  (input: { caseId: number; monthYear: string }): Promise<{ data: MinimalStaffRequirements } | { error: string }>;
}

export function makeGetMinimalStaffController(
  getMinimalStaffUseCase: IGetMinimalStaffUseCase,
): IGetMinimalStaffController {
  return async ({ caseId, monthYear }) => {
    try {
      validateMonthYear(monthYear);
      const minimalStaff = await getMinimalStaffUseCase({ caseId, monthYear });
      return { data: minimalStaff };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
