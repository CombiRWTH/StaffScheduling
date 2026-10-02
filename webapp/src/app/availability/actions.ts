"use server";

import { revalidatePath } from "next/cache";
import { setAvailability, setWish } from "@/lib/api";
import type { AvailabilityEntry, WishEntry } from "@/lib/types";

export type SaveResult = { ok: true } | { ok: false; error: string };

async function run(write: () => Promise<unknown>): Promise<SaveResult> {
  try {
    await write();
  } catch (error) {
    return { ok: false, error: (error as Error).message };
  }
  revalidatePath("/availability");
  return { ok: true };
}

/** Save the employee's availability on that date; `null` removes it. */
export async function saveAvailability(employeeId: number, date: string, entry: AvailabilityEntry | null) {
  return run(() => setAvailability(employeeId, date, entry));
}

/** Save the employee's wish on that date; `null` removes it. */
export async function saveWish(employeeId: number, date: string, entry: WishEntry | null) {
  return run(() => setWish(employeeId, date, entry));
}
