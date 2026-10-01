// Server component: compute search parameters and render a thin client wrapper
import {HomePageClient} from '@/components/home-page-client';
import {getWorkflowSession} from '@/infrastructure/services/workflow-session.service';

export default async function HomePage({
                                           searchParams,
                                       }: {
    searchParams: Promise<{ caseId?: string; monthYear?: string }>;
}) {
    const [{caseId, monthYear}, workflowState] = await Promise.all([
        searchParams,
        getWorkflowSession(),
    ]);
    const caseSearch = caseId && monthYear ? `?caseId=${caseId}&monthYear=${monthYear}` : '';

    return <HomePageClient caseSearch={caseSearch} isWorkflowMode={workflowState.isWorkflowMode}/>;
}
