/**
 * Base class for all domain errors.
 */
export class DomainError extends Error {
    constructor(
        message: string,
        public readonly statusCode: number = 500
    ) {
        super(message);
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
}

/**
 * Error thrown when a requested resource is not found.
 */
export class ResourceNotFoundError extends DomainError {
    constructor(message: string) {
        super(message, 404);
    }
}

/**
 * Error thrown when attempting to create a resource that already exists.
 */
export class DuplicateResourceError extends DomainError {
    constructor(message: string) {
        super(message, 409);
    }
}

/**
 * Error thrown when input data fails validation.
 */
export class ValidationError extends DomainError {
    constructor(message: string) {
        super(message, 400);
    }
}

/**
 * Type guard to check if an error is a DomainError.
 */
export function isDomainError(error: unknown): error is DomainError {
    return error instanceof DomainError;
}
