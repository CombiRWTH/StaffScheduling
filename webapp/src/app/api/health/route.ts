import { NextResponse } from "next/server";
import { getSolverApiConfig } from "@/lib/config/app-config";

/** Process connectivity only; database availability is checked separately. */
export async function GET() {
  try {
    const { baseUrl } = getSolverApiConfig();
    const response = await fetch(`${baseUrl}/status`, { cache: "no-store", signal: AbortSignal.timeout(5000) });
    const body: unknown = await response.json();
    if (!response.ok || !body || typeof body !== "object" || !("status" in body) || body.status !== "healthy") {
      throw new Error("Invalid API liveness response");
    }
    return NextResponse.json({ status: "healthy", api: "healthy" });
  } catch {
    return NextResponse.json(
      { status: "unavailable", detail: "Check API service and SOLVER_API_URL." },
      { status: 503 },
    );
  }
}
