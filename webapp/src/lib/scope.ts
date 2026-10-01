import "server-only";
import { redirect } from "next/navigation";
import { getPlanningOptions } from "@/lib/api";
import type { PlanningUnit } from "@/lib/types";

export interface ScopeSearchParams {
  month?: string;
  stations?: string;
}

export interface PlanningScope {
  month?: string;
  stationIds: number[];
  stations: PlanningUnit[];
  error?: string;
}

/**
 * Read the planning month and stations from the URL and load the month's stations.
 * Stations unavailable in the chosen month are dropped by redirecting to the corrected URL.
 */
export async function loadPlanningScope(pathname: string, params: ScopeSearchParams): Promise<PlanningScope> {
  const month = params.month && /^\d{4}-(0[1-9]|1[0-2])$/.test(params.month) ? params.month : undefined;
  const stationsParam = params.stations ?? "";
  const requested = /^[1-9]\d*(,[1-9]\d*)*$/.test(stationsParam)
    ? [...new Set(stationsParam.split(",").map(Number))]
    : [];
  if (!month) return { stationIds: [], stations: [] };

  let stations: PlanningUnit[];
  try {
    stations = (await getPlanningOptions(month)).planning_units;
  } catch (error) {
    return { month, stationIds: requested, stations: [], error: (error as Error).message };
  }
  const stationIds = requested.filter((id) => stations.some((unit) => unit.planning_unit_id === id));
  if (stationIds.length !== requested.length) {
    const query = new URLSearchParams({ month });
    if (stationIds.length) query.set("stations", stationIds.join(","));
    redirect(`${pathname}?${query}`);
  }
  return { month, stationIds, stations };
}
