import {SolverPageClient} from './solver-page-client';
import {checkSolverHealth, getLastInsertedSolution} from '@/features/solver/solver.actions';
import {getWorkflowSession} from '@/infrastructure/services/workflow-session.service';
import {getSelectedScheduleAction} from '@/features/schedule/schedule.actions';
import {listAvailableCaseIdsForMonthAction} from '@/features/cases/cases.actions';

export default async function SolverPage({
                                             searchParams,
                                         }: {
    searchParams: Promise<{ caseId?: string; caseIds?: string; monthYear?: string }>;
}) {
    const [{caseId: caseIdStr, caseIds: caseIdsStr, monthYear}, workflowState] =
        await Promise.all([searchParams, getWorkflowSession()]);

    if (!monthYear || !/^(0?[1-9]|1[0-2])_\d{4}$/.test(monthYear)) {
        return (
            <div className="flex items-center justify-center h-64 text-muted-foreground">
                Bitte wähle einen Monat aus
            </div>
        );
    }

    const rawCaseIds = caseIdsStr ?? caseIdStr ?? '';
    const selectedCaseIds = Array.from(
        new Set(
            rawCaseIds
                .split(',')
                .map(Number)
                .filter(id => Number.isInteger(id) && id > 0)
        )
    );

    const availableCaseIds = await listAvailableCaseIdsForMonthAction(monthYear);

    const activeCaseId =
        selectedCaseIds.find(id => availableCaseIds.includes(id)) ?? null;

    const [configResult, lastInsertedResult, selectedScheduleData] =
        activeCaseId
            ? await Promise.all([
                checkSolverHealth(),
                getLastInsertedSolution(activeCaseId, monthYear).catch(() => ({
                    success: true,
                    data: null,
                })),
                getSelectedScheduleAction(activeCaseId, monthYear).catch(() => ({
                    solution: null,
                })),
            ])
            : await Promise.all([
                checkSolverHealth(),
                Promise.resolve({success: true, data: null}),
                Promise.resolve({solution: null}),
            ]);

    return (
        <SolverPageClient
            caseId={activeCaseId}
            monthYear={monthYear}
            availableCaseIds={availableCaseIds}
            initialConfigValidation={configResult.success ? configResult.data : null}
            initialJobs={[]}
            initialLastInsertedSolution={
                lastInsertedResult.success ? lastInsertedResult.data : null
            }
            initialPendingInsertSolution={selectedScheduleData.solution ?? null}
            isLocked={workflowState.isWorkflowMode}
        />
    );
}
