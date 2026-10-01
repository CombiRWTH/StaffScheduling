import {AvailabilityTemplatesPageClient} from './availability-page-client';
import {listAvailabilityTemplatesAction} from '@/features/templates/availability-templates.actions';

export default async function AvailabilityTemplatesPage({
                                                            searchParams,
                                                        }: {
    searchParams: Promise<{ caseId?: string; monthYear?: string }>;
}) {
    const {caseId: caseIdStr, monthYear} = await searchParams;
    const caseId = Number(caseIdStr);

    if (!caseId || !monthYear) {
        return <div className="flex items-center justify-center h-64 text-muted-foreground">Bitte wähle einen Case und Monat aus</div>;
    }

    const templates = await listAvailabilityTemplatesAction(caseId);

    return <AvailabilityTemplatesPageClient caseId={caseId} monthYear={monthYear} templates={templates}/>;
}
