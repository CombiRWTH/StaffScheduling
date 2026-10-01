import "server-only";
import { redirect } from "next/navigation";
import { getPlanningOptions } from "@/lib/api";
import { selectionSearch } from "@/lib/selection";
import type { PlanningUnit } from "@/lib/types";

export interface ScopeSearchParams {
  month?: string;
  stations?: string;
}

export interface PlanningScope {
  month: string;
  stationIds: number[];
  stations: PlanningUnit[];
  error?: string;
}

/**
 * Read the planning month and stations from the URL and load the month's stations.
 * A missing or invalid month redirects to January of the current year; stations unavailable
 * in the month are dropped by redirecting to the corrected URL.
 */
export async function loadPlanningScope(pathname: string, params: ScopeSearchParams): Promise<PlanningScope> {
  const stationsParam = params.stations ?? "";
  const requested = /^[1-9]\d*(,[1-9]\d*)*$/.test(stationsParam)
    ? [...new Set(stationsParam.split(",").map(Number))]
    : [];
  const month = params.month ?? "";
  if (!/^(20\d{2}|21\d{2}|2200)-(0[1-9]|1[0-2])$/.test(month)) {
    redirect(`${pathname}${selectionSearch(`${new Date().getFullYear()}-01`, requested)}`);
  }

  let stations: PlanningUnit[];
  try {
    stations = (await getPlanningOptions(month)).planning_units;
  } catch (error) {
    return { month, stationIds: requested, stations: [], error: (error as Error).message };
  }
  const stationIds = requested.filter((id) => stations.some((unit) => unit.planning_unit_id === id));
  if (stationIds.length !== requested.length) {
    redirect(`${pathname}${selectionSearch(month, stationIds)}`);
  }
  return { month, stationIds, stations };
}
