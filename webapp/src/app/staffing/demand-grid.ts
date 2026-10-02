// The unsaved staffing demand of one station month. Cells are addressed by date, shift and
// qualification; a missing cell requires nobody. How cells are keyed stays inside this module.
import type { DemandCell, StaffLevel } from "@/lib/types";

export type DemandGrid = ReadonlyMap<string, DemandCell>;

export const MAX_REQUIRED_COUNT = 99;

const keyOf = (date: string, shiftId: number, level: StaffLevel) => `${date}|${shiftId}|${level}`;

/** Whether the backend accepts a count: a whole number from 0 to 99. */
export function isValidCount(count: number) {
  return Number.isInteger(count) && count >= 0 && count <= MAX_REQUIRED_COUNT;
}

/** An input's text as a count: empty means zero; anything else is kept as typed, even if invalid. */
export function parseCount(text: string) {
  return text.trim() === "" ? 0 : Number(text);
}

export function gridOf(cells: readonly DemandCell[]): DemandGrid {
  return new Map(cells.map((cell) => [keyOf(cell.date, cell.shift_id, cell.staff_level), cell]));
}

export function countAt(grid: DemandGrid, date: string, shiftId: number, level: StaffLevel): number {
  return grid.get(keyOf(date, shiftId, level))?.required_count ?? 0;
}

/** A copy with one cell changed; zero removes the cell, an invalid count is kept for the API to reject. */
export function withCount(grid: DemandGrid, date: string, shiftId: number, level: StaffLevel, count: number) {
  const next = new Map(grid);
  const key = keyOf(date, shiftId, level);
  if (count === 0) next.delete(key);
  else next.set(key, { date, shift_id: shiftId, staff_level: level, required_count: count });
  return next as DemandGrid;
}

export function sameGrid(left: DemandGrid, right: DemandGrid): boolean {
  return (
    left.size === right.size && [...left].every(([key, cell]) => right.get(key)?.required_count === cell.required_count)
  );
}

/** The complete month as the cells the API saves. */
export function cellsOf(grid: DemandGrid): DemandCell[] {
  return [...grid.values()];
}

/** `grid` with every cell of `level` taken from `source`, and the sorted dates whose counts change. */
export function withLevelFrom(grid: DemandGrid, source: DemandGrid, level: StaffLevel) {
  const next = new Map([...grid].filter(([, cell]) => cell.staff_level !== level));
  for (const [key, cell] of source) if (cell.staff_level === level) next.set(key, cell);
  const changed = new Set<string>();
  for (const [key, cell] of [...grid, ...next]) {
    if (cell.staff_level === level && grid.get(key)?.required_count !== next.get(key)?.required_count) {
      changed.add(cell.date);
    }
  }
  return { grid: next as DemandGrid, changedDates: [...changed].sort() };
}
