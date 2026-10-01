import {DuplicateResourceError, ResourceNotFoundError} from './base.errors';

export class EmployeeNotFoundError extends ResourceNotFoundError {
    constructor(key: number) {
        super(`Employee with key ${key} not found`);
    }
}

export class DuplicateEmployeeError extends DuplicateResourceError {
    constructor(key: number) {
        super(`Employee with key ${key} already exists`);
    }
}
