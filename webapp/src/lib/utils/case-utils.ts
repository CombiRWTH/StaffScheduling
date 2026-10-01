/**
 * Client-safe utility functions for case management.
 * These functions can be used in both client and server components.
 */

/**
 * Converts a DD.MM.YYYY date string to MM_YYYY folder format.
 *
 * @param ddmmyyyy - Date string in DD.MM.YYYY format (e.g., "15.11.2024")
 * @returns String in MM_YYYY format (e.g., "11_2024"), or empty string if invalid
 */
export function deriveMonthYear(ddmmyyyy: string): string {
    const parts = ddmmyyyy.split('.');
    if (parts.length === 3) {
        return `${parts[1].padStart(2, '0')}_${parts[2]}`;
    }
    return '';
}

/**
 * Parses a monthYear string in MM_YYYY format to extract month and year numbers.
 *
 * @param monthYear - String in MM_YYYY format (e.g., "11_2024")
 * @returns Object with month (1-12) and year numbers
 *
 * @example
 * const { month, year } = parseMonthYear("11_2024");
 * console.log(month, year); // 11, 2024
 */
export function parseMonthYear(monthYear: string): { month: number; year: number } {
    const [monthStr, yearStr] = monthYear.split('_');
    return {
        month: parseInt(monthStr, 10),
        year: parseInt(yearStr, 10)
    };
}

/**
 * Formats month and year into MM_YYYY string format.
 *
 * @param month - Month number (1-12)
 * @param year - Year (e.g., 2024)
 * @returns String in MM_YYYY format (e.g., "11_2024")
 *
 * @example
 * const formatted = formatMonthYear(11, 2024);
 * console.log(formatted); // "11_2024"
 */
export function formatMonthYear(month: number, year: number): string {
    return `${month.toString().padStart(2, '0')}_${year}`;
}

/**
 * Gets the display name for a month number.
 *
 * @param month - Month number (1-12)
 * @returns Full month name (e.g., "January")
 */
export function getMonthName(month: number): string {
    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ];
    return monthNames[month - 1] || 'Unknown';
}

/**
 * Gets the German display name for a month number.
 *
 * @param month - Month number (1-12)
 * @returns Full month name in German (e.g., "Januar")
 */
export function getMonthNameGerman(month: number): string {
    const monthNames = [
        'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni',
        'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember'
    ];
    return monthNames[month - 1] || 'Unbekannt';
}
