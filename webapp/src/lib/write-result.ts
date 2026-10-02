import "server-only";
import { revalidatePath } from "next/cache";

/** What a server action reports back to the form: success only after the API confirmed the write. */
export type WriteResult = { ok: true } | { ok: false; error: string };

/** Run one API write; on success revalidate `path`, on failure return the user-facing message. */
export async function writeResult(write: () => Promise<unknown>, path: string): Promise<WriteResult> {
  try {
    await write();
  } catch (error) {
    return { ok: false, error: (error as Error).message };
  }
  revalidatePath(path);
  return { ok: true };
}
