import "server-only";
import { revalidatePath } from "next/cache";

/** What a server action reports back to the form: success, with the API's answer, only after it confirmed the write. */
export type WriteResult<T = unknown> = { ok: true; value: T } | { ok: false; error: string };

/** Run one API write; on success revalidate `path`, on failure return the user-facing message. */
export async function writeResult<T>(write: () => Promise<T>, path: string): Promise<WriteResult<T>> {
  let value: T;
  try {
    value = await write();
  } catch (error) {
    return { ok: false, error: (error as Error).message };
  }
  revalidatePath(path);
  return { ok: true, value };
}
