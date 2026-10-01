import type { IUpdateWeightsTemplateUseCase } from "@/application/use-cases/templates/weights/update-weights-template.use-case";
import type { Template } from "@/entities/models/template.model";
import type { Weights } from "@/entities/models/weights.model";
import { isDomainError } from "@/entities/errors/base.errors";

export interface IUpdateWeightsTemplateController {
  (input: {
    caseId: number;
    templateId: string;
    data: { content?: Weights; description?: string };
  }): Promise<{ data: Template<Weights> } | { error: string }>;
}

export function makeUpdateWeightsTemplateController(
  updateWeightsTemplateUseCase: IUpdateWeightsTemplateUseCase,
): IUpdateWeightsTemplateController {
  return async ({ caseId, templateId, data }) => {
    try {
      const template = await updateWeightsTemplateUseCase({ caseId, templateId, data });
      return { data: template };
    } catch (error) {
      if (isDomainError(error)) return { error: error.message };
      throw error;
    }
  };
}
