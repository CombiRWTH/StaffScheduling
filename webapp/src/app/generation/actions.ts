"use server";

import { startGeneration } from "@/lib/api";
import { writeResult } from "@/lib/write-result";

/** Start a generation; success means the backend validated the input and is solving. */
export async function generate(month: string, stationIds: number[], timeoutSeconds: number) {
  return writeResult(() => startGeneration(month, stationIds, timeoutSeconds), "/generation");
}
