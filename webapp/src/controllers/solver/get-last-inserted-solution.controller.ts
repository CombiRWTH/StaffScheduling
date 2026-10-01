import { z } from "zod";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";
import type { IGetLastInsertedSolutionUseCase } from "@/application/use-cases/solver/get-last-inserted-solution.use-case";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";

const InputSchema = z.object({
  caseId: z.number().int().positive(),
  monthYear: z.string(),
});

export interface IGetLastInsertedSolutionController {
  (input: { caseId: number; monthYear: string }): Promise<{ data: ScheduleSolutionRaw | null } | { error: string }>;
}

export function makeGetLastInsertedSolutionController(
  getLastInsertedUseCase: IGetLastInsertedSolutionUseCase,
): IGetLastInsertedSolutionController {
  return async (rawInput) => {
    try {
      const { caseId, monthYear } = InputSchema.parse(rawInput);
      validateMonthYear(monthYear);
      const data = await getLastInsertedUseCase({ caseId, monthYear });
      return { data };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      if (error instanceof z.ZodError) return { error: error.issues[0]?.message ?? "Invalid input" };
      if (error instanceof Error) return { error: error.message };
      throw error;
    }
  };
}
