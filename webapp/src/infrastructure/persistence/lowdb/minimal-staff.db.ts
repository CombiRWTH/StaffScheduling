import {CategoryRequirements, DayRequirements, MinimalStaffRequirements} from "@/entities/models";
import {getSolverApiConfig} from "@/lib/config/app-config";

/**
 * Default requirements for a single day.
 */
const getDefaultDayRequirements = (): DayRequirements => ({
    F: 0,
    Z: 0,
    S: 0,
    N: 0,
});

/**
 * Default requirements for a single category across all days of the week.
 */
const getDefaultCategoryRequirements = (): CategoryRequirements => ({
    Mo: getDefaultDayRequirements(),
    Di: getDefaultDayRequirements(),
    Mi: getDefaultDayRequirements(),
    Do: getDefaultDayRequirements(),
    Fr: getDefaultDayRequirements(),
    Sa: getDefaultDayRequirements(),
    So: getDefaultDayRequirements(),
});

/**
 * Factory function for default minimal staff requirements.
 * Used when initializing a new case without existing requirements.
 * Always returns a fresh, deep-copied object.
 */
const getDefaultData = (): MinimalStaffRequirements => ({
    Fachkraft: getDefaultCategoryRequirements(),
    Azubi: getDefaultCategoryRequirements(),
    Hilfskraft: getDefaultCategoryRequirements(),
});

export async function getMinimalStaffDb(caseId: number, monthYear: string) {
    const [month, year] = monthYear.split('_').map(Number);
    const fromDate = new Date(Date.UTC(year, month - 1, 1));
    const url = new URL(`${getSolverApiConfig().baseUrl}/minimal-staff`);

    url.searchParams.set('planning_unit', String(caseId));
    url.searchParams.set('from_date', fromDate.toISOString().split('T')[0]);

    const response = await fetch(url, {cache: 'no-store'});
    const db = {
        data: response.ok ? await response.json() as MinimalStaffRequirements : getDefaultData(),
        async write() {
            await fetch(url, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({data: db.data}),
            });
        },
    };
    return db;
}
