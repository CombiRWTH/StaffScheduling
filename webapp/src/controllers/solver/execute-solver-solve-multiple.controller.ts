import { z } from "zod";
import { isDomainError } from "@/entities/errors/base.errors";
import { validateMonthYear } from "@/entities/validation/input-validators";
import { SolveMultipleParamsSchema } from "@/entities/models/solver.model";
import type { SolverJob, SolveMultipleScheduleInfo } from "@/entities/models/solver.model";
import type { ScheduleSolutionRaw } from "@/entities/models/schedule.model";
import type { IExecuteSolverSolveMultipleUseCase } from "@/application/use-cases/solver/execute-solver-solve-multiple.use-case";

const InputSchema = z.object({
  caseId: z.number().int().positive(),
  monthYear: z.string(),
  params: SolveMultipleParamsSchema,
});

export interface IExecuteSolverSolveMultipleController {
  (input: { caseId: number; monthYear: string; params: z.infer<typeof SolveMultipleParamsSchema> }): Promise<
    | {
        data: {
          job: SolverJob;
          scheduleInfo: SolveMultipleScheduleInfo;
          solutions: ScheduleSolutionRaw[]; // Included explicitly for API-based solve-multiple results.
        };
      }
    | { error: string }
  >;
}

export function makeExecuteSolverSolveMultipleController(
  executeUseCase: IExecuteSolverSolveMultipleUseCase,
): IExecuteSolverSolveMultipleController {
  return async (rawInput) => {
    try {
      const { caseId, monthYear, params } = InputSchema.parse(rawInput);
      validateMonthYear(monthYear);
      const result = await executeUseCase({ caseId, monthYear, params });
      return { data: result };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      if (error instanceof z.ZodError) return { error: error.issues[0]?.message ?? "Invalid input" };
      if (error instanceof Error) return { error: error.message };
      throw error;
    }
  };
}
