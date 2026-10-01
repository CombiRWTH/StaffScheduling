import {SchedulePageClient} from './schedule-page-client';
import {getSchedulesMetadataAction, getSelectedScheduleAction} from '@/features/schedule/schedule.actions';
import {parseSolutionFile} from '@/lib/services/schedule-parser';

export default async function SchedulePage({
                                               searchParams,
                                           }: {
    searchParams: Promise<{ caseId?: string; monthYear?: string }>;
}) {
    const {caseId: caseIdStr, monthYear} = await searchParams;

    if (!caseIdStr || !monthYear) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Case
            aus</div>;
    }

    const caseId = Number(caseIdStr);
    if (isNaN(caseId) || caseId <= 0 || !/^(0?[1-9]|1[0-2])_\d{4}$/.test(monthYear)) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Case
            aus</div>;
    }

    const [selectedScheduleData, schedulesMetadata] = await Promise.all([
        getSelectedScheduleAction(caseId, monthYear),
        getSchedulesMetadataAction(caseId, monthYear),
    ]);

    const schedule = selectedScheduleData.solution
        ? parseSolutionFile(selectedScheduleData.solution)
        : null;

    return <SchedulePageClient
        caseId={caseId}
        monthYear={monthYear}
        initialSchedule={schedule}
        initialMetadata={schedulesMetadata}
    />;
}
