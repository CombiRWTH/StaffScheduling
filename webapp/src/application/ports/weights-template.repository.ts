import { Template, TemplateSummary } from "@/entities/models/template.model";
import { Weights } from "@/entities/models/weights.model";

export interface IWeightsTemplateRepository {
  list(caseId: number): Promise<TemplateSummary[]>;

  get(caseId: number, templateId: string): Promise<Template<Weights>>;

  create(caseId: number, content: Weights, description: string): Promise<TemplateSummary>;

  update(
    caseId: number,
    templateId: string,
    data: { content?: Weights; description?: string },
  ): Promise<Template<Weights>>;

  delete(caseId: number, templateId: string): Promise<void>;
}
