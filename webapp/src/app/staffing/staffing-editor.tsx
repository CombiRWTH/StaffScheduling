"use client";

import { useState, useTransition } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { STAFF_LEVEL_LABELS, WEEKDAYS, formatDate } from "@/lib/labels";
import type { DayType, DemandConfiguration, DemandRequirement, StaffLevel } from "@/lib/types";
import { cn } from "@/lib/utils";
import { expandPattern, saveDemand } from "./actions";

const LEVELS = Object.keys(STAFF_LEVEL_LABELS) as StaffLevel[];
const DAY_TYPES: Array<{ type: DayType; label: string }> = [
  ...(["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"] as const).map((type, index) => ({
    type,
    label: WEEKDAYS[index],
  })),
  { type: "holiday", label: "Feiertag" },
];

/** Required counts keyed by date, shift and qualification; absent keys require nobody. */
type Counts = Record<string, number>;
const key = (date: string, shiftId: number, level: StaffLevel) => `${date}|${shiftId}|${level}`;

function toCounts(requirements: DemandRequirement[]): Counts {
  return Object.fromEntries(
    requirements.map((row) => [key(row.date, row.shift_id, row.staff_level), row.required_count]),
  );
}

function sameCounts(left: Counts, right: Counts) {
  const keys = new Set([...Object.keys(left), ...Object.keys(right)]);
  return [...keys].every((cell) => (left[cell] ?? 0) === (right[cell] ?? 0));
}

function parseCount(value: string) {
  const count = Number(value);
  return Number.isInteger(count) && count >= 0 ? count : 0;
}

export function StaffingEditor({ month, configuration }: { month: string; configuration: DemandConfiguration }) {
  const { calendar, shifts, planning_unit_id: stationId } = configuration;
  const [saved, setSaved] = useState<Counts>(() => toCounts(configuration.demand?.requirements ?? []));
  const [counts, setCounts] = useState<Counts>(saved);
  const [level, setLevel] = useState<StaffLevel>("professional");
  const [isSaved, setIsSaved] = useState(configuration.demand !== null);
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);
  const [pending, startTransition] = useTransition();
  const dirty = !sameCounts(counts, saved);

  function setCount(date: string, shiftId: number, value: string) {
    setCounts((current) => ({ ...current, [key(date, shiftId, level)]: parseCount(value) }));
    setMessage(null);
  }

  function save() {
    const requirements = Object.entries(counts)
      .filter(([, count]) => count > 0)
      .map(([cell, required_count]) => {
        const [date, shiftId, staffLevel] = cell.split("|");
        return {
          planning_unit_id: stationId,
          date,
          shift_id: Number(shiftId),
          staff_level: staffLevel as StaffLevel,
          required_count,
        };
      });
    startTransition(async () => {
      const result = await saveDemand(month, stationId, requirements);
      if (result.ok) {
        setSaved(counts);
        setIsSaved(true);
        setMessage({ ok: true, text: "Mindestbesetzung gespeichert." });
      } else {
        setMessage({ ok: false, text: `${result.error} Änderungen wurden nicht gespeichert.` });
      }
    });
  }

  return (
    <div className="space-y-4">
      {!isSaved && (
        <p className="rounded-md border border-dashed p-3 text-sm text-muted-foreground">
          Für diesen Monat ist noch keine Mindestbesetzung gespeichert.
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div role="tablist" aria-label="Qualifikation" className="flex gap-1 rounded-lg bg-muted p-1">
          {LEVELS.map((value) => (
            <button
              key={value}
              type="button"
              role="tab"
              aria-selected={level === value}
              onClick={() => setLevel(value)}
              className={cn(
                "rounded-md px-3 py-1 text-sm",
                level === value ? "bg-background font-medium shadow-sm" : "text-muted-foreground",
              )}
            >
              {STAFF_LEVEL_LABELS[value]}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2">
          {dirty && <span className="text-sm text-muted-foreground">Ungespeicherte Änderungen</span>}
          <Button variant="outline" disabled={!dirty || pending} onClick={() => setCounts(saved)}>
            Zurücksetzen
          </Button>
          <Button disabled={pending || (!dirty && isSaved)} onClick={save}>
            Speichern
          </Button>
        </div>
      </div>
      {message && (
        <p
          role={message.ok ? "status" : "alert"}
          className={cn("text-sm", message.ok ? "text-green-700" : "text-destructive")}
        >
          {message.text}
        </p>
      )}

      <PatternCard
        month={month}
        stationId={stationId}
        calendar={calendar}
        shifts={shifts}
        level={level}
        counts={counts}
        onApply={(next) => {
          setCounts(next);
          setMessage(null);
        }}
      />

      <Card>
        <CardHeader>
          <CardTitle>{STAFF_LEVEL_LABELS[level]} je Tag</CardTitle>
          <CardDescription>Leere oder 0 bedeutet: keine Mindestbesetzung.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Datum</TableHead>
                {shifts.map((shift) => (
                  <TableHead key={shift.shift_id} className="text-center">
                    {shift.code}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {calendar.map((day) => (
                <TableRow key={day.date} className={cn((day.weekday > 5 || day.public_holiday) && "bg-muted/40")}>
                  <TableCell className="whitespace-nowrap">
                    {WEEKDAYS[day.weekday - 1]} {formatDate(day.date)}
                    {day.public_holiday && (
                      <Badge variant="outline" className="ml-2 text-xs">
                        {day.public_holiday}
                      </Badge>
                    )}
                  </TableCell>
                  {shifts.map((shift) => (
                    <TableCell key={shift.shift_id}>
                      <Input
                        type="number"
                        min={0}
                        max={99}
                        aria-label={`${shift.code} am ${formatDate(day.date)}`}
                        value={counts[key(day.date, shift.shift_id, level)] ?? 0}
                        onChange={(event) => setCount(day.date, shift.shift_id, event.target.value)}
                        className="mx-auto w-16 text-center"
                      />
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

/** Previews a weekly pattern via the backend calendar and applies it to the unsaved grid only after confirmation. */
function PatternCard({
  month,
  stationId,
  calendar,
  shifts,
  level,
  counts,
  onApply,
}: {
  month: string;
  stationId: number;
  calendar: DemandConfiguration["calendar"];
  shifts: DemandConfiguration["shifts"];
  level: StaffLevel;
  counts: Counts;
  onApply: (counts: Counts) => void;
}) {
  const [pattern, setPattern] = useState<Record<string, number>>({});
  const [preview, setPreview] = useState<{ next: Counts; changed: string[] } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [previewing, startPreview] = useTransition();

  function showPreview() {
    const cells = DAY_TYPES.flatMap(({ type }) =>
      shifts.map((shift) => ({
        day_type: type,
        shift_id: shift.shift_id,
        staff_level: level,
        required_count: pattern[`${type}|${shift.shift_id}`] ?? 0,
      })),
    );
    startPreview(async () => {
      setError(null);
      const result = await expandPattern(month, stationId, cells);
      if (!result.ok) {
        setError(result.error);
        return;
      }
      const expanded = toCounts(result.requirements);
      const next = { ...counts };
      for (const day of calendar) {
        for (const shift of shifts)
          next[key(day.date, shift.shift_id, level)] = expanded[key(day.date, shift.shift_id, level)] ?? 0;
      }
      const changed = calendar
        .map((day) => day.date)
        .filter((date) =>
          shifts.some(
            (shift) =>
              (next[key(date, shift.shift_id, level)] ?? 0) !== (counts[key(date, shift.shift_id, level)] ?? 0),
          ),
        );
      setPreview({ next, changed });
    });
  }

  return (
    <details className="group rounded-xl border bg-card">
      <summary className="cursor-pointer list-none px-6 py-4 font-semibold">
        <span className="mr-2 inline-block transition-transform group-open:rotate-90">›</span>Wochenmuster anwenden
      </summary>
      <div className="space-y-3 px-6 pb-6">
        <p className="text-sm text-muted-foreground">
          Muster für {STAFF_LEVEL_LABELS[level]} auf alle Tage dieses Monats übertragen. Feiertage (NRW) nutzen die
          Zeile Feiertag. Das Muster wird nicht gespeichert und gilt nicht für andere Monate.
        </p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Tag</TableHead>
              {shifts.map((shift) => (
                <TableHead key={shift.shift_id} className="text-center">
                  {shift.code}
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {DAY_TYPES.map(({ type, label }) => (
              <TableRow key={type}>
                <TableCell>{label}</TableCell>
                {shifts.map((shift) => (
                  <TableCell key={shift.shift_id}>
                    <Input
                      type="number"
                      min={0}
                      max={99}
                      aria-label={`Muster ${shift.code} ${label}`}
                      value={pattern[`${type}|${shift.shift_id}`] ?? 0}
                      onChange={(event) => {
                        setPattern((current) => ({
                          ...current,
                          [`${type}|${shift.shift_id}`]: parseCount(event.target.value),
                        }));
                        setPreview(null);
                      }}
                      className="mx-auto w-16 text-center"
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Button variant="outline" disabled={previewing} onClick={showPreview}>
          Vorschau
        </Button>
        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        {preview &&
          (preview.changed.length ? (
            <div role="region" aria-label="Vorschau" className="space-y-2 rounded-md border p-3 text-sm">
              <p>
                {preview.changed.length} Tage werden ersetzt:{" "}
                {preview.changed.map((date) => formatDate(date).slice(0, 6)).join(", ")}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={() => {
                    onApply(preview.next);
                    setPreview(null);
                  }}
                >
                  Übernehmen
                </Button>
                <Button size="sm" variant="outline" onClick={() => setPreview(null)}>
                  Verwerfen
                </Button>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Das Muster ändert keinen Tag.</p>
          ))}
      </div>
    </details>
  );
}
