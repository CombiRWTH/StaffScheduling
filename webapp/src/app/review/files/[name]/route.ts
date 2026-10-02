import { REVIEW_FILES, getReviewFile, type ReviewFile } from "@/lib/api";

/** Download one file of the schedule under review with the API's attachment headers; the API stays server-side. */
export async function GET(_request: Request, { params }: { params: Promise<{ name: string }> }) {
  const { name } = await params;
  if (!REVIEW_FILES.includes(name as ReviewFile)) return new Response("Unbekannte Datei.", { status: 404 });
  try {
    const file = await getReviewFile(name as ReviewFile);
    if (!file) return new Response("Kein Dienstplan zur Prüfung.", { status: 404 });
    const headers = [...file.headers].filter(([key]) => key === "content-type" || key === "content-disposition");
    return new Response(file.body, { headers });
  } catch (error) {
    return new Response((error as Error).message, { status: 503 });
  }
}
