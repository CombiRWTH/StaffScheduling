import {ValidationError} from '@/entities/errors/base.errors';

/**
 * Regex for valid scheduleId: alphanumeric, hyphens, underscores only.
 * Prevents path traversal via /, .., or dots.
 */
const SCHEDULE_ID_REGEX = /^[a-zA-Z0-9_-]+$/;

/**
 * Regex for valid monthYear in M_YYYY or MM_YYYY format (project convention).
 * Matches months 1-12 (with optional leading zero), underscore separator, 4-digit year.
 */
const MONTH_YEAR_REGEX = /^(0?[1-9]|1[0-2])_\d{4}$/;

/**
 * Validates a scheduleId to prevent path traversal.
 * @throws ValidationError if the scheduleId is invalid
 */
export function validateScheduleId(scheduleId: string): void {
    if (!scheduleId || !SCHEDULE_ID_REGEX.test(scheduleId)) {
        throw new ValidationError(
            `Invalid scheduleId "${scheduleId}": must contain only alphanumeric characters, hyphens, and underscores.`
        );
    }
}

/**
 * Validates a monthYear string to match MM_YYYY format.
 * @throws ValidationError if the monthYear is invalid
 */
export function validateMonthYear(monthYear: string): void {
    if (!monthYear || !MONTH_YEAR_REGEX.test(monthYear)) {
        throw new ValidationError(
            `Invalid monthYear "${monthYear}": must be in M_YYYY or MM_YYYY format (e.g., "1_2024" or "11_2024").`
        );
    }
}
