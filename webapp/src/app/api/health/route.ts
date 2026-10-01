import { isApiHealthy } from "@/lib/api";

/** Webapp liveness including a real server-side request to the API; database access is checked separately. */
export async function GET() {
  if (await isApiHealthy()) return Response.json({ status: "healthy", api: "healthy" });
  return Response.json({ status: "unavailable", detail: "Check API service and API_URL." }, { status: 503 });
}
