import {
    AvailabilityApiResponseSchema,
    AvailabilityDatabase
} from "@/entities/models";
import {getSolverApiConfig} from "@/lib/config/app-config";

export async function getGlobalAvailabilityDb(caseId: number, monthYear: string) {
    const [month, year] = monthYear.split('_').map(Number);
    const fromDate = new Date(Date.UTC(year, month - 1, 1));
    const url = new URL(`${getSolverApiConfig().baseUrl}/global-availability`);

    url.searchParams.set('planning_unit', String(caseId));
    url.searchParams.set('from_date', fromDate.toISOString().split('T')[0]);

    const response = await fetch(url, {cache: 'no-store'});
    const data: AvailabilityDatabase = {employees: []};

    if (response.ok) {
        const parsed = AvailabilityApiResponseSchema.safeParse(await response.json());
        if (!parsed.success) {
            throw new Error('Invalid global availability response from backend API');
        }
        const parsedData = 'data' in parsed.data ? parsed.data.data : parsed.data;
        data.employees = parsedData.employees;
    }

    return {
        data,
        async write() {
            const response = await fetch(url, {
                method: 'PUT',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({data: this.data}),
            });

            if (!response.ok) {
                const message = await response.text();
                throw new Error(message || 'Failed to write global availability to backend API');
            }
        },
    };
}
