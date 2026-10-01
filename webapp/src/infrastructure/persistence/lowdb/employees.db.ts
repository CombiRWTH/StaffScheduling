import { EmployeeDatabase } from "@/entities/models";
import { getSolverApiConfig } from "@/lib/config/app-config";

export async function getEmployeeDb(caseId: number, monthYear: string) {
  const [month, year] = monthYear.split("_").map(Number);
  const fromDate = new Date(Date.UTC(year, month - 1, 1));
  const url = new URL(`${getSolverApiConfig().baseUrl}/employees`);

  url.searchParams.set("planning_unit", String(caseId));
  url.searchParams.set("from_date", fromDate.toISOString().split("T")[0]);

  const response = await fetch(url, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`Failed to load employees from API: ${response.statusText}`);
  }

  return {
    data: (await response.json()) as EmployeeDatabase,
  };
}
