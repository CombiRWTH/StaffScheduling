import {GlobalWishesTemplateContent, Template, TemplateSummary} from '@/entities/models/template.model';

export interface IGlobalWishesTemplateRepository {
    list(caseId: number): Promise<TemplateSummary[]>;

    get(caseId: number, templateId: string): Promise<Template<GlobalWishesTemplateContent>>;

    create(caseId: number, content: GlobalWishesTemplateContent, description: string): Promise<TemplateSummary>;

    update(
        caseId: number,
        templateId: string,
        data: { content?: GlobalWishesTemplateContent; description?: string }
    ): Promise<Template<GlobalWishesTemplateContent>>;

    delete(caseId: number, templateId: string): Promise<void>;
}
