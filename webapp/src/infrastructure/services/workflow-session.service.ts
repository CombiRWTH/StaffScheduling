import { cookies } from "next/headers";
import { WorkflowState } from "@/entities/models/workflow.model";
import { deriveMonthYear } from "@/lib/utils/case-utils";

export async function getWorkflowSession(): Promise<WorkflowState> {
  const cookieStore = await cookies();
  const isWorkflowMode = cookieStore.get("workflow_mode")?.value === "true";
  const caseIdRaw = cookieStore.get("workflow_case")?.value ?? null;
  const startDate = cookieStore.get("workflow_start")?.value ?? null;
  const endDate = cookieStore.get("workflow_end")?.value ?? null;
  const monthYear = startDate ? deriveMonthYear(startDate) : null;

  return {
    isWorkflowMode,
    caseId: caseIdRaw ? parseInt(caseIdRaw, 10) : null,
    startDate,
    endDate,
    monthYear,
  };
}

export async function setWorkflowSession(caseId: string, start: string, end: string): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.set("workflow_mode", "true", { path: "/", httpOnly: true, sameSite: "lax" });
  cookieStore.set("workflow_case", caseId, { path: "/", httpOnly: true, sameSite: "lax" });
  cookieStore.set("workflow_start", start, { path: "/", httpOnly: true, sameSite: "lax" });
  cookieStore.set("workflow_end", end, { path: "/", httpOnly: true, sameSite: "lax" });
}

export async function clearWorkflowSession(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete("workflow_mode");
  cookieStore.delete("workflow_case");
  cookieStore.delete("workflow_start");
  cookieStore.delete("workflow_end");
}
