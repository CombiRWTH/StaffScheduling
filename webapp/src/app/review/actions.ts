"use server";

import { clearPublication, importReview, publishReview } from "@/lib/api";
import { writeResult } from "@/lib/write-result";

/** Review an uploaded `input`/`result` pair; success means the backend validated and re-checked it. */
export async function importFiles(files: FormData) {
  return writeResult(async () => {
    await importReview(files);
  }, "/review");
}

/** Publish the reviewed schedule; success means TimeOffice committed it and read it back. */
export async function publishSchedule(month: string, stationIds: number[], receivedAt: string) {
  return writeResult(() => publishReview(month, stationIds, receivedAt), "/review");
}

/** Remove the published duties of exactly these stations' month; success means committed. */
export async function clearSchedule(month: string, stationIds: number[]) {
  return writeResult(() => clearPublication(month, stationIds), "/review");
}
