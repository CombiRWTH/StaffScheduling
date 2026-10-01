import {GlobalWishesAndBlockedDatabase} from "@/entities/models";
import {getSolverApiConfig} from "@/lib/config/app-config";

export async function getGlobalWishesAndBlockedDb(caseId: number, monthYear: string) {
    const [month, year] = monthYear.split('_').map(Number);
    const fromDate = new Date(Date.UTC(year, month - 1, 1));
    const url = new URL(`${getSolverApiConfig().baseUrl}/global-wishes-and-blocked`);

    url.searchParams.set('planning_unit', String(caseId));
    url.searchParams.set('from_date', fromDate.toISOString().split('T')[0]);

    const response = await fetch(url, {cache: 'no-store'});

    return {
        data: response.ok ? await response.json() as GlobalWishesAndBlockedDatabase : {employees: []},
        async write() {
            await fetch(url, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({data: this.data}),
            });
        }
    };
}
