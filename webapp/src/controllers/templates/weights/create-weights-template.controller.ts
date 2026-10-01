import type { ICreateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/create-weights-template.use-case";
import type { TemplateSummary } from "@/entities/models/template.model";
import type { Weights } from "@/entities/models/weights.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface ICreateWeightsTemplateController {
  (input: {
    caseId: number;
    content: Weights;
    description: string;
  }): Promise<{ data: TemplateSummary } | { error: string }>;
}

export function makeCreateWeightsTemplateController(
  createWeightsTemplateUseCase: ICreateWeightsTemplateUseCase,
): ICreateWeightsTemplateController {
  return async ({ caseId, content, description }) => {
    try {
      const summary = await createWeightsTemplateUseCase({ caseId, content, description });
      return { data: summary };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
