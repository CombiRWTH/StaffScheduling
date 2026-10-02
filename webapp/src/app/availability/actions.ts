"use server";

import { revalidatePath } from "next/cache";
import { deleteAvailability, deleteWish, putAvailability, putWish } from "@/lib/api";
import type { Availability, Wish } from "@/lib/types";

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

export async function saveAvailability(entry: Omit<Availability, "source">) {
  return run(() => putAvailability(entry));
}

export async function removeAvailability(employeeId: number, date: string) {
  return run(() => deleteAvailability(employeeId, date));
}

export async function saveWish(wish: Wish) {
  return run(() => putWish(wish));
}

export async function removeWish(employeeId: number, date: string) {
  return run(() => deleteWish(employeeId, date));
}
