"use server";

import { setAvailability, setWish } from "@/lib/api";
import type { AvailabilityEntry, WishEntry } from "@/lib/types";
import { writeResult } from "@/lib/write-result";

/** Save the employee's availability on that date; `null` removes it. */
export async function saveAvailability(employeeId: number, date: string, entry: AvailabilityEntry | null) {
  return writeResult(() => setAvailability(employeeId, date, entry), "/availability");
}

/** Save the employee's wish on that date; `null` removes it. */
export async function saveWish(employeeId: number, date: string, entry: WishEntry | null) {
  return writeResult(() => setWish(employeeId, date, entry), "/availability");
}
