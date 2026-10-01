import type { IScheduleRepository } from '@/application/ports/schedule.repository';
import type { ImportSolutionResult } from '@/entities/models/solver.model';
import type { ScheduleSolutionRaw } from '@/entities/models/schedule.model';

export type { ImportSolutionResult };

export interface ImportSolutionInput {
    caseId: number;
    monthYear: string;
    start: string;
    end: string;
    solutionType: string;
    solution: ScheduleSolutionRaw;
}

export interface IImportSolutionUseCase {
    (input: ImportSolutionInput): Promise<ImportSolutionResult>;
}

function formatDateForFilename(dateStr: string): string {
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

export function makeImportSolutionUseCase(
    scheduleRepository: IScheduleRepository
): IImportSolutionUseCase {
    return async ({ caseId, monthYear, start, end, solutionType, solution }) => {
        const startFormatted = formatDateForFilename(start);
        const endFormatted = formatDateForFilename(end);

        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const scheduleId = `imported_${solutionType}_${timestamp}`;
        const description = `Automatisch importiert: ${solutionType} (${startFormatted} bis ${endFormatted})`;
        const filename = `solution_${caseId}_${startFormatted}-${endFormatted}_${solutionType}_processed.json`;

        await scheduleRepository.save(caseId, monthYear, scheduleId, solution, description);
        await scheduleRepository.select(caseId, monthYear, scheduleId);

        return {
            success: true,
            scheduleId,
            filename,
            message: 'Solution imported successfully',
        };
    };
}
