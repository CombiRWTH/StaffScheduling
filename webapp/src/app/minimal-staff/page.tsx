import {MinimalStaffPageClient} from './minimal-staff-page-client';
import {getMinimalStaffAction} from '@/features/minimal-staff/minimal-staff.actions';
import {listAvailableCaseIdsForMonthAction} from '@/features/cases/cases.actions';
import {MinimalStaffRequirements} from '@/entities/models/minimal-staff.model';

interface MinimalStaffCaseData {
    caseId: number;
    requirements: MinimalStaffRequirements;
}

interface MinimalStaffCaseError {
    caseId: number;
    error: string;
}

type MinimalStaffResult =
    | { caseId: number; requirements: MinimalStaffRequirements | null; error: null }
    | { caseId: number; requirements: null; error: string };

function getErrorMessage(error: unknown): string {
    return error instanceof Error ? error.message : String(error);
}

export default async function MinimalStaffPage({
                                                   searchParams,
                                               }: {
    searchParams: Promise<{ caseId?: string; caseIds?: string; monthYear?: string }>;
}) {
    const {caseId: caseIdStr, caseIds: caseIdsStr, monthYear} = await searchParams;
    const rawCaseIds = caseIdsStr ?? caseIdStr ?? '';
    const caseIds = Array.from(
        new Set(
            rawCaseIds
                .split(',')
                .map(id => Number(id))
                .filter(id => Number.isInteger(id) && id > 0)
        )
    );

    if (!monthYear) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Monat
            aus</div>;
    }

    if (!/^(0?[1-9]|1[0-2])_\d{4}$/.test(monthYear)) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Monat
            aus</div>;
    }

    const availableCaseIds = await listAvailableCaseIdsForMonthAction(monthYear);

    const selectedCaseIds = caseIds.filter(id => availableCaseIds.includes(id));

    const minimalStaffResults: MinimalStaffResult[] = await Promise.all(
        selectedCaseIds.map(async caseId => {
            try {
                return {
                    caseId,
                    requirements: await getMinimalStaffAction(caseId, monthYear),
                    error: null,
                };
            } catch (error) {
                return {
                    caseId,
                    requirements: null,
                    error: getErrorMessage(error),
                };
            }
        })
    );

    const minimalStaffCases: MinimalStaffCaseData[] = minimalStaffResults
        .filter((result): result is { caseId: number; requirements: MinimalStaffRequirements; error: null } => result.error === null)
        .map(({caseId, requirements}) => ({caseId, requirements}));

    const minimalStaffErrors: MinimalStaffCaseError[] = minimalStaffResults
        .filter((result): result is { caseId: number; requirements: null; error: string } => result.error !== null)
        .map(({caseId, error}) => ({caseId, error}));

    return (
        <MinimalStaffPageClient
            monthYear={monthYear}
            minimalStaffCases={minimalStaffCases}
            minimalStaffErrors={minimalStaffErrors}
            availableCaseIds={availableCaseIds}
        />
    );
}
