"use client";

import { usePathname, useRouter } from "next/navigation";
import { useTransition } from "react";
import { Building2, ChevronDown, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { PlanningScope } from "@/lib/scope";
import { MONTHS, selectionMonth, selectionSearch } from "@/lib/selection";
import { cn } from "@/lib/utils";

/** Month and station selection; the URL is the only state. */
export function PlanningScopePicker({ month, stationIds, stations, error }: PlanningScope) {
  const router = useRouter();
  const pathname = usePathname();
  const [pending, startTransition] = useTransition();
  const [year, monthNumber] = month.split("-").map(Number);

  const navigate = (nextMonth: string, nextStations: number[]) => {
    startTransition(() => router.push(`${pathname}${selectionSearch(nextMonth, nextStations)}`));
  };
  const changeMonth = (nextMonth: string) => nextMonth !== month && navigate(nextMonth, stationIds);
  const toggleStation = (id: number, checked: boolean) =>
    navigate(month, checked ? [...stationIds, id] : stationIds.filter((value) => value !== id));

  const selected = new Set(stationIds);
  const selectedNames = stations.filter((unit) => selected.has(unit.planning_unit_id)).map((u) => u.display_name);
  // A count, not names, so the button keeps a predictable width like the month field.
  const summary =
    selectedNames.length === 0
      ? "Stationen wählen"
      : selectedNames.length === 1
        ? "1 Station"
        : `${selectedNames.length} Stationen`;

  return (
    <div className="flex flex-wrap items-center gap-2" role="group" aria-label="Planungsauswahl">
      <Select
        value={String(monthNumber)}
        onValueChange={(value) => changeMonth(selectionMonth(year, Number(value)))}
        disabled={pending}
      >
        <SelectTrigger className="h-8 w-[124px]" aria-label="Monat">
          <SelectValue placeholder="Monat wählen" />
        </SelectTrigger>
        <SelectContent>
          {MONTHS.map((label, index) => (
            <SelectItem key={label} value={String(index + 1)}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <Input
        key={year}
        type="number"
        min={2000}
        max={2200}
        defaultValue={year}
        disabled={pending}
        aria-label="Jahr"
        className="h-8 w-20"
        onKeyDown={(event) => event.key === "Enter" && event.currentTarget.blur()}
        onBlur={(event) => {
          const nextYear = Number(event.currentTarget.value);
          if (!Number.isInteger(nextYear) || nextYear < 2000 || nextYear > 2200)
            event.currentTarget.value = String(year);
          else changeMonth(selectionMonth(nextYear, monthNumber));
        }}
      />

      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            className={cn(
              "h-8 w-[160px] justify-between gap-2 px-3 font-normal",
              !stationIds.length && "border-primary",
            )}
            aria-label={`Stationen: ${selectedNames.join(", ") || summary}`}
          >
            <span className="flex min-w-0 items-center gap-2">
              <Building2 className="h-4 w-4 shrink-0 text-muted-foreground" />
              <span className="truncate">{summary}</span>
            </span>
            <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-64 p-2">
          <p className="px-2 pb-2 pt-1 text-xs font-medium uppercase text-muted-foreground">Stationen</p>
          {error ? (
            <p role="alert" className="px-2 py-1.5 text-sm text-destructive">
              {error}
            </p>
          ) : !stations.length ? (
            <p className="px-2 py-1.5 text-sm text-muted-foreground">Keine Stationen für diesen Monat verfügbar.</p>
          ) : (
            stations.map((unit) => (
              <Label
                key={unit.planning_unit_id}
                className="cursor-pointer rounded-sm px-2 py-1.5 font-normal hover:bg-accent"
              >
                <Checkbox
                  checked={selected.has(unit.planning_unit_id)}
                  disabled={pending}
                  onCheckedChange={(checked) => toggleStation(unit.planning_unit_id, checked === true)}
                />
                {unit.display_name}
              </Label>
            ))
          )}
        </PopoverContent>
      </Popover>

      <Button
        size="icon"
        variant="outline"
        className="size-8"
        disabled={pending}
        onClick={() => startTransition(() => router.refresh())}
        aria-label="Stationen aktualisieren"
        title="Stationen aktualisieren"
      >
        <RefreshCw className={cn("h-4 w-4", pending && "animate-spin")} />
      </Button>
      {error && (
        <p role="alert" className="text-sm text-destructive">
          Stationen nicht geladen
        </p>
      )}
    </div>
  );
}
