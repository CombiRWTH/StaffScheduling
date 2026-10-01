import {getSolverApiConfig} from '@/lib/config/app-config';
import {ScheduleDatabase, SchedulesMetadata, ScheduleSolutionRaw} from "@/entities/models";

function getScheduleApiUrl(caseId: number, monthYear: string, endpoint: string) {
    const [month, year] = monthYear.split('_').map(Number);
    const fromDate = new Date(Date.UTC(year, month - 1, 1));
    const url = new URL(`${getSolverApiConfig().baseUrl}${endpoint}`);

    url.searchParams.set('planning_unit', String(caseId));
    url.searchParams.set('from_date', fromDate.toISOString().split('T')[0]);

    return url;
}

/**
 * Gets or creates a database connection for schedule metadata.
 * Manages the list of all schedules for a case.
 *
 * @param caseId - The planning unit ID
 * @param monthYear - The month/year in MM_YYYY format
 * @returns Promise resolving to the schedules metadata database instance
 */
export async function getSchedulesMetadataDb(caseId: number, monthYear: string) {
    const url = getScheduleApiUrl(caseId, monthYear, '/schedules/metadata');
    let data: SchedulesMetadata = {schedules: [], selectedScheduleId: null};

    try {
        const response = await fetch(url, {cache: 'no-store'});
        data = response.ok ? await response.json() as SchedulesMetadata : {schedules: [], selectedScheduleId: null};
    } catch {
        data = {schedules: [], selectedScheduleId: null};
    }

    const db = {
        data,
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

/**
 * Gets or creates a database connection for a specific schedule solution.
 * Each schedule is stored in its own file named schedule_{scheduleId}.json
 *
 * @param caseId - The planning unit ID
 * @param monthYear - The month/year in MM_YYYY format
 * @param scheduleId - The ID of the specific schedule
 * @returns Promise resolving to the schedule database instance
 */
export async function getScheduleDb(caseId: number, monthYear: string, scheduleId: string) {
    const url = getScheduleApiUrl(caseId, monthYear, `/schedules/${scheduleId}`);
    let data: ScheduleDatabase = {solution: null};

    try {
        const response = await fetch(url, {cache: 'no-store'});
        data = response.ok ? await response.json() as ScheduleDatabase : {solution: null};
    } catch {
        data = {solution: null};
    }

    const db = {
        data,
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

/** Writes one saved schedule to TimeOffice through the scheduling backend. */
export async function writeScheduleToTimeOfficeDb(
    caseId: number,
    monthYear: string,
    solution: ScheduleSolutionRaw,
): Promise<void> {
    const url = getScheduleApiUrl(caseId, monthYear, '/schedules/write-to-timeoffice');
    const response = await fetch(url, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: solution}),
        cache: 'no-store',
    });

    if (!response.ok) {
        const message = await response.text().catch(() => '');
        throw new Error(message || `Dienstplan konnte nicht in TimeOffice gespeichert werden (${response.status}).`);
    }
}

/**
 * Deletes a specific schedule file.
 *
 * @param caseId - The planning unit ID
 * @param monthYear - The month/year in MM_YYYY format
 * @param scheduleId - The ID of the schedule to delete
 */
export async function deleteSchedule(caseId: number, monthYear: string, scheduleId: string): Promise<void> {
    try {
        await fetch(getScheduleApiUrl(caseId, monthYear, `/schedules/${scheduleId}`), {method: 'DELETE'});
    } catch {
        // Keep old filesystem behavior: deleting a missing schedule is a no-op.
    }
}

export async function saveLastInsertedDb(caseId: number, monthYear: string, solution: ScheduleSolutionRaw): Promise<void> {
    await fetch(getScheduleApiUrl(caseId, monthYear, '/schedules/last-inserted'), {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({data: solution}),
    });
}

export async function getLastInsertedDb(caseId: number, monthYear: string): Promise<ScheduleSolutionRaw | null> {
    try {
        const response = await fetch(getScheduleApiUrl(caseId, monthYear, '/schedules/last-inserted'), {cache: 'no-store'});

        return response.ok ? await response.json() as ScheduleSolutionRaw : null;
    } catch {
        return null;
    }
}

export async function clearLastInsertedDb(caseId: number, monthYear: string): Promise<void> {
    try {
        await fetch(getScheduleApiUrl(caseId, monthYear, '/schedules/last-inserted'), {method: 'DELETE'});
    } catch {
        // Keep old filesystem behavior: clearing a missing marker is a no-op.
    }
}
