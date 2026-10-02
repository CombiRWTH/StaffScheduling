"use server";

import { importReview } from "@/lib/api";
import { writeResult } from "@/lib/write-result";

/** Review an uploaded `input`/`result` pair; success means the backend validated and re-checked it. */
export async function importFiles(files: FormData) {
  return writeResult(() => importReview(files), "/review");
}
