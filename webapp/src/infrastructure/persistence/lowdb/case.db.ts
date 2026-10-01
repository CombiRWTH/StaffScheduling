import {join} from 'path';
import {CaseUnit} from '@/entities/models/case.model';
import fs from 'fs/promises';
import {CASES_DIR} from '@/lib/config/app-config';

/**
 * Lists all existing planning units with their available months.
 * Scans the cases directory two levels deep: unit folders and month_year subfolders.
 *
 * @returns Promise resolving to an array of case units with available months
 *
 * @example
 * const units = await listCases();
 * console.log(units); // [{ unitId: 77, months: ["11_2024", "12_2024"] }]
 */
export async function listCases(): Promise<CaseUnit[]> {
    try {
        // Ensure the cases directory exists
        await fs.mkdir(CASES_DIR, {recursive: true});
        const entries = await fs.readdir(CASES_DIR, {withFileTypes: true});

        // Filter for directories with numeric names (planning units)
        const unitDirs = entries
            .filter(entry => entry.isDirectory())
            .map(entry => parseInt(entry.name))
            .filter(id => !isNaN(id))
            .sort((a, b) => a - b);

        // For each unit, scan for month folders
        const caseUnits: CaseUnit[] = [];
        for (const unitId of unitDirs) {
            const unitPath = join(CASES_DIR, unitId.toString());
            const monthEntries = await fs.readdir(unitPath, {withFileTypes: true});

            // Filter for month folders (MM_YYYY format)
            const months = monthEntries
                .filter(entry => entry.isDirectory() && /^\d{1,2}_\d{4}$/.test(entry.name))
                .map(entry => entry.name)
                .sort();

            if (months.length > 0) {
                caseUnits.push({unitId, months});
            }
        }

        return caseUnits;
    } catch (error) {
        return [];
    }
}
