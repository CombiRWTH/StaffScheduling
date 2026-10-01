import {ResourceNotFoundError} from './base.errors';

export class ScheduleNotFoundError extends ResourceNotFoundError {
    constructor(scheduleId: string) {
        super(`Schedule with id "${scheduleId}" not found`);
    }
}

export class NoScheduleSelectedError extends ResourceNotFoundError {
    constructor() {
        super('No schedule is currently selected');
    }
}
