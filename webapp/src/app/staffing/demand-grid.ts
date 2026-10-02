// The unsaved staffing demand of one station month. Cells are addressed by date, shift and
// qualification; a missing cell requires nobody. How cells are keyed stays inside this module.
import type { DemandRequirement, StaffLevel } from "@/lib/types";

type Cell = Omit<DemandRequirement, "planning_unit_id">;
export type DemandGrid = ReadonlyMap<string, Cell>;

const keyOf = (date: string, shiftId: number, level: StaffLevel) => `${date}|${shiftId}|${level}`;

export function gridOf(requirements: readonly DemandRequirement[]): DemandGrid {
  return new Map(
    requirements.map(({ date, shift_id, staff_level, required_count }) => [
      keyOf(date, shift_id, staff_level),
      { date, shift_id, staff_level, required_count },
    ]),
  );
}

export function countAt(grid: DemandGrid, date: string, shiftId: number, level: StaffLevel): number {
  return grid.get(keyOf(date, shiftId, level))?.required_count ?? 0;
}

/** A copy with one cell changed; a count of zero removes the cell. */
export function withCount(grid: DemandGrid, date: string, shiftId: number, level: StaffLevel, count: number) {
  const next = new Map(grid);
  const key = keyOf(date, shiftId, level);
  if (count > 0) next.set(key, { date, shift_id: shiftId, staff_level: level, required_count: count });
  else next.delete(key);
  return next as DemandGrid;
}

export function sameGrid(left: DemandGrid, right: DemandGrid): boolean {
  return (
    left.size === right.size && [...left].every(([key, cell]) => right.get(key)?.required_count === cell.required_count)
  );
}

/** The complete month as API requirements for one station. */
export function requirementsOf(grid: DemandGrid, stationId: number): DemandRequirement[] {
  return [...grid.values()].map((cell) => ({ planning_unit_id: stationId, ...cell }));
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
