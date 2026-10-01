import {JobHistoryData} from "@/entities/models";
import {getSolverApiConfig} from "@/lib/config/app-config";

export async function getJobHistoryDb(caseId: number, monthYear: string) {
    const [month, year] = monthYear.split('_').map(Number);
    const fromDate = new Date(Date.UTC(year, month - 1, 1));
    const url = new URL(`${getSolverApiConfig().baseUrl}/jobs`);

    url.searchParams.set('planning_unit', String(caseId));
    url.searchParams.set('from_date', fromDate.toISOString().split('T')[0]);

    const response = await fetch(url, {cache: 'no-store'});
    const db = {
        data: response.ok ? await response.json() as JobHistoryData : {jobs: []},
        async read() {
            const nextResponse = await fetch(url, {cache: 'no-store'});
            db.data = nextResponse.ok ? await nextResponse.json() as JobHistoryData : {jobs: []};
        },
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
