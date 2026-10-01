import {ResourceNotFoundError} from './base.errors';

export class TemplateNotFoundError extends ResourceNotFoundError {
    constructor(templateId: string) {
        super(`Template with id "${templateId}" not found`);
    }
}
