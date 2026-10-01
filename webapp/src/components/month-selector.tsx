"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState, useTransition } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { loadPlanningOptions } from "@/features/planning/planning.actions";
import type { PlanningOptions } from "@/features/planning/models";

export function MonthSelector() {
  const params = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const month = params.get("month") ?? "";
  const stationIds = params.get("stations") ?? "";
  const selected = useMemo(() => stationIds.split(",").filter(Boolean).map(Number), [stationIds]);
  const [options, setOptions] = useState<{ month: string; data?: PlanningOptions; error?: string }>({ month: "" });
  const [refresh, setRefresh] = useState(0);
  const [pending, startTransition] = useTransition();
  useEffect(() => {
    if (!month) return;
    let current = true;
    loadPlanningOptions(month).then((result) => {
      if (current) setOptions({ month, ...result });
    });
    return () => {
      current = false;
    };
  }, [month, refresh]);
  const loaded = options.month === month;
  const units = loaded ? (options.data?.planning_units ?? []) : [];
  const navigate = (nextMonth: string, stations: number[]) => {
    const next = new URLSearchParams();
    if (nextMonth) next.set("month", nextMonth);
    if (stations.length) next.set("stations", stations.join(","));
    startTransition(() => router.push(`${pathname}?${next}`));
  };
  const changeMonth = (nextMonth: string) => {
    setOptions({ month: "" });
    navigate(nextMonth, selected);
  };
  useEffect(() => {
    if (!loaded || !options.data) return;
    const valid = options.data.planning_units.map((unit) => unit.planning_unit_id);
    const retained = selected.filter((id) => valid.includes(id));
    if (retained.length !== selected.length) {
      const next = new URLSearchParams({ month });
      if (retained.length) next.set("stations", retained.join(","));
      router.replace(`${pathname}?${next}`);
    }
  }, [loaded, options.data, month, params, pathname, router, selected]);
  return (
    <div className="flex w-full flex-wrap items-center gap-3">
      <label className="flex items-center gap-2">
        Planungsmonat{" "}
        <Input
          aria-label="Planungsmonat"
          type="month"
          min="2000-01"
          max="2200-12"
          value={month}
          disabled={pending}
          onChange={(event) => void changeMonth(event.target.value)}
          className="w-auto"
        />
      </label>
      {month && (
        <fieldset disabled={pending || !loaded} className="flex flex-wrap gap-3">
          <legend>Stationen</legend>
          {units.map((unit) => (
            <label key={unit.planning_unit_id} className="flex items-center gap-1">
              <input
                type="checkbox"
                checked={selected.includes(unit.planning_unit_id)}
                onChange={(event) =>
                  navigate(
                    month,
                    event.target.checked
                      ? [...selected, unit.planning_unit_id]
                      : selected.filter((id) => id !== unit.planning_unit_id),
                  )
                }
              />
              {unit.display_name}
            </label>
          ))}
        </fieldset>
      )}
      <Button
        variant="outline"
        disabled={!month || pending}
        onClick={() => {
          setOptions({ month: "" });
          setRefresh((value) => value + 1);
          router.refresh();
        }}
      >
        Stationen aktualisieren
      </Button>
      {pending || (month && !loaded) ? (
        <p role="status">Planungsauswahl wird geladen…</p>
      ) : loaded && options.error ? (
        <p role="alert">{options.error}</p>
      ) : month && !units.length ? (
        <p>Keine Stationen für diesen Monat verfügbar.</p>
      ) : null}
    </div>
  );
}
