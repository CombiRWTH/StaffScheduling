import {IWeightsTemplateRepository} from '@/application/ports/weights-template.repository';
import {Template, TemplateMetadata, TemplateSummary} from '@/entities/models/template.model';
import {Weights} from '@/entities/models/weights.model';
import {getTemplateDb} from '@/infrastructure/persistence/lowdb/template.db';

export class LowdbWeightsTemplateRepository implements IWeightsTemplateRepository {
    async list(caseId: number): Promise<TemplateSummary[]> {
        const db = await getTemplateDb(caseId, 'weights');
        return db.data.templates
            .map((t) => ({
                id: t._metadata.id,
                description: t._metadata.description,
                last_modified: t._metadata.last_modified,
                type: 'weights' as const,
                fileName: 'weights.json',
            }))
            .sort((a, b) => new Date(b.last_modified).getTime() - new Date(a.last_modified).getTime());
    }

    async get(caseId: number, templateId: string): Promise<Template<Weights>> {
        const db = await getTemplateDb(caseId, 'weights');
        const template = db.data.templates.find((t) => t._metadata.id === templateId);
        if (!template) {
            throw new Error(`Weights template ${templateId} not found`);
        }
        return template as Template<Weights>;
    }

    async create(caseId: number, content: Weights, description: string): Promise<TemplateSummary> {
        const db = await getTemplateDb(caseId, 'weights');
        const metadata: TemplateMetadata = {
            id: Date.now().toString(),
            description,
            last_modified: new Date().toISOString(),
        };
        db.data.templates.push({content, _metadata: metadata});
        await db.write();
        return {
            id: metadata.id,
            description: metadata.description,
            last_modified: metadata.last_modified,
            type: 'weights',
            fileName: 'weights.json',
        };
    }

    async update(
        caseId: number,
        templateId: string,
        data: { content?: Weights; description?: string }
    ): Promise<Template<Weights>> {
        const db = await getTemplateDb(caseId, 'weights');
        const idx = db.data.templates.findIndex((t) => t._metadata.id === templateId);
        if (idx === -1) {
            throw new Error(`Weights template ${templateId} not found`);
        }
        const existing = db.data.templates[idx];
        db.data.templates[idx] = {
            content: data.content ?? existing.content,
            _metadata: {
                ...existing._metadata,
                description: data.description ?? existing._metadata.description,
                last_modified: new Date().toISOString(),
            },
        };
        await db.write();
        return db.data.templates[idx] as Template<Weights>;
    }

    async delete(caseId: number, templateId: string): Promise<void> {
        const db = await getTemplateDb(caseId, 'weights');
        db.data.templates = db.data.templates.filter((t) => t._metadata.id !== templateId);
        await db.write();
    }
}
