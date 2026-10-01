import {redirect} from 'next/navigation';
import {checkSolverHealth, getLastInsertedSolution} from '@/features/solver/solver.actions';
import {WorkflowPageClient} from './workflow-page-client';
import {getWorkflowSession} from '@/infrastructure/services/workflow-session.service';
import {getSelectedScheduleAction} from '@/features/schedule/schedule.actions';

/** Converts DD.MM.YYYY -> YYYY-MM-DD */
function convertToISODate(ddmmyyyy: string): string {
    const parts = ddmmyyyy.split('.');
    if (parts.length === 3) {
        return `${parts[2]}-${parts[1].padStart(2, '0')}-${parts[0].padStart(2, '0')}`;
    }
    return ddmmyyyy;
}

export default async function WorkflowPage() {
    const state = await getWorkflowSession();

    if (!state.isWorkflowMode || state.caseId === null || !state.startDate || !state.endDate || !state.monthYear) {
        redirect('/');
    }

    const caseId = state.caseId;
    const startDate = state.startDate;
    const endDate = state.endDate;
    const monthYear = state.monthYear;
    const isoStart = convertToISODate(startDate);
    const isoEnd = convertToISODate(endDate);

    const [configResult, lastInsertedResult, selectedScheduleData] = await Promise.all([
        checkSolverHealth(),
        getLastInsertedSolution(caseId, monthYear).catch(() => ({success: true, data: null})),
        getSelectedScheduleAction(caseId, monthYear).catch(() => ({solution: null})),
    ]);
    const initialConfig = configResult.success ? configResult.data : null;
    const initialLastInsertedSolution = lastInsertedResult.success ? lastInsertedResult.data : null;
    const initialPendingInsertSolution = selectedScheduleData.solution ?? null;

    return (
        <WorkflowPageClient
            caseId={caseId}
            monthYear={monthYear}
            startDate={startDate}
            endDate={endDate}
            isoStart={isoStart}
            isoEnd={isoEnd}
            initialConfig={initialConfig}
            initialJobs={[]}
            initialLastInsertedSolution={initialLastInsertedSolution}
            initialPendingInsertSolution={initialPendingInsertSolution}
        />
    );
}
