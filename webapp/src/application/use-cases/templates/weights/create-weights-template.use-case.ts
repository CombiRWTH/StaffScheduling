import { IWeightsTemplateRepository } from "@/application/ports/weights-template.repository";
import { TemplateSummary } from "@/entities/models/template.model";
import { Weights } from "@/entities/models/weights.model";

export interface ICreateWeightsTemplateUseCase {
  (input: { caseId: number; content: Weights; description: string }): Promise<TemplateSummary>;
}

export function makeCreateWeightsTemplateUseCase(
  repository: IWeightsTemplateRepository,
): ICreateWeightsTemplateUseCase {
  return async ({ caseId, content, description }) => {
    return repository.create(caseId, content, description);
  };
}
