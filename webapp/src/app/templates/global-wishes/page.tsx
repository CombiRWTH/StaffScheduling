import {GlobalWishesTemplatesPageClient} from './global-wishes-page-client';
import {listGlobalWishesTemplatesAction} from '@/features/templates/global-wishes-templates.actions';

export default async function GlobalWishesTemplatesPage({
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

    const templates = await listGlobalWishesTemplatesAction(caseId);

    return <GlobalWishesTemplatesPageClient caseId={caseId} monthYear={monthYear} templates={templates}/>;
}
