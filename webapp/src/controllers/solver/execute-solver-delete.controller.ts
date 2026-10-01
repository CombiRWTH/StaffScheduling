import { z } from "zod";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";
import { DeleteParamsSchema, SolverJob } from "@/entities/models/solver.model";
import type { IExecuteSolverDeleteUseCase } from "@/application/use-cases/solver/execute-solver-delete.use-case";
import type { ScheduleSolutionRaw } from "@/entities/models";

const InputSchema = z.object({
  caseId: z.number().int().positive(),
  monthYear: z.string(),
  params: DeleteParamsSchema,
  solution: z.unknown().optional(),
});

export interface IExecuteSolverDeleteController {
  (input: {
    caseId: number;
    monthYear: string;
    params: z.infer<typeof DeleteParamsSchema>;
    solution?: ScheduleSolutionRaw;
  }): Promise<{ data: { job: SolverJob } } | { error: string }>;
}

export function makeExecuteSolverDeleteController(
  executeUseCase: IExecuteSolverDeleteUseCase,
): IExecuteSolverDeleteController {
  return async (rawInput) => {
    try {
      const { caseId, monthYear, params, solution } = InputSchema.parse(rawInput);
      validateMonthYear(monthYear);
      const result = await executeUseCase({
        caseId,
        monthYear,
        params,
        solution: solution as ScheduleSolutionRaw | undefined,
      });
      return { data: result };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      if (error instanceof z.ZodError) return { error: error.issues[0]?.message ?? "Invalid input" };
      if (error instanceof Error) return { error: error.message };
      throw error;
    }
  };
}
