"use client";

import { useState, useTransition } from "react";
import { Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { AVAILABILITY_LABELS, WEEKDAYS, WISH_LABELS, formatDate } from "@/lib/labels";
import type { Availability, AvailabilityType, EmployeeCalendar, ShiftOption, WishType } from "@/lib/types";
import { cn } from "@/lib/utils";
import type { WriteResult } from "@/lib/write-result";
import { saveAvailability, saveWish } from "./actions";

const NONE = "none";

function availabilityText(row: Availability, shifts: ShiftOption[]) {
  const codes = row.shift_ids?.map((id) => shifts.find((shift) => shift.shift_id === id)?.code ?? id).join(", ");
  return [AVAILABILITY_LABELS[row.availability_type], codes, row.reason].filter(Boolean).join(" · ");
}

export function AvailabilityCalendar({ calendar }: { calendar: EmployeeCalendar }) {
  const [selected, setSelected] = useState<string | null>(null);
  const days = calendar.calendar;
  const absences = new Map(calendar.absences.map((row) => [row.date, row]));
  const availability = new Map(calendar.availability.map((row) => [row.date, row]));
  const wishes = new Map(calendar.wishes.map((row) => [row.date, row]));
  const shiftCode = (id: number | null) => calendar.shifts.find((shift) => shift.shift_id === id)?.code;

  return (
    <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <Card>
        <CardHeader>
          <CardTitle>Monatskalender</CardTitle>
          <CardDescription>Einen Tag wählen, um Einschränkung oder Wunsch zu bearbeiten.</CardDescription>
          <div className="flex flex-wrap gap-2 pt-1 text-xs">
            <Badge variant="secondary">Abwesenheit (TimeOffice)</Badge>
            <Badge className="bg-red-100 text-red-800">Einschränkung</Badge>
            <Badge className="bg-green-100 text-green-800">Wunsch</Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-1 text-center text-xs font-medium text-muted-foreground">
            {WEEKDAYS.map((day) => (
              <div key={day}>{day}</div>
            ))}
          </div>
          <div className="mt-1 grid grid-cols-7 gap-1">
            {Array.from({ length: (days[0]?.weekday ?? 1) - 1 }, (_, index) => (
              <div key={`blank-${index}`} />
            ))}
            {days.map(({ date, weekday, public_holiday }) => {
              const absence = absences.get(date);
              const entry = availability.get(date);
              const wish = wishes.get(date);
              return (
                <button
                  key={date}
                  type="button"
                  aria-label={formatDate(date)}
                  aria-pressed={selected === date}
                  onClick={() => setSelected(date)}
                  className={cn(
                    "flex min-h-20 flex-col gap-0.5 rounded-md border p-1 text-left text-[11px] transition-colors hover:bg-muted",
                    selected === date && "ring-2 ring-ring",
                    (weekday > 5 || public_holiday) && "bg-muted/40",
                  )}
                >
                  <span className="text-sm font-medium">
                    {Number(date.slice(8))}
                    {public_holiday && (
                      <span className="ml-1 text-[10px] font-normal text-muted-foreground">{public_holiday}</span>
                    )}
                  </span>
                  {absence && (
                    <span className="rounded bg-secondary px-1">{availabilityText(absence, calendar.shifts)}</span>
                  )}
                  {entry && (
                    <span className="rounded bg-red-100 px-1 text-red-800">
                      {availabilityText(entry, calendar.shifts)}
                    </span>
                  )}
                  {wish && (
                    <span className="rounded bg-green-100 px-1 text-green-800">
                      {[WISH_LABELS[wish.type], shiftCode(wish.shift_id)].filter(Boolean).join(" · ")}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {selected ? (
        <Card key={selected}>
          <CardHeader>
            <CardTitle>{formatDate(selected)}</CardTitle>
            {absences.has(selected) && (
              <CardDescription>
                Abwesenheit aus TimeOffice: {availabilityText(absences.get(selected)!, calendar.shifts)} (nur lesend)
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-6">
            <AvailabilityForm
              employeeId={calendar.employee_id}
              date={selected}
              saved={availability.get(selected)}
              shifts={calendar.shifts}
            />
            <WishForm
              employeeId={calendar.employee_id}
              date={selected}
              saved={wishes.get(selected)}
              shifts={calendar.shifts}
            />
          </CardContent>
        </Card>
      ) : (
        <p className="text-sm text-muted-foreground">Kein Tag gewählt.</p>
      )}
    </div>
  );
}

/** Runs one save or delete; on failure the entered values stay and the error is shown instead of success. */
function useSave() {
  const [pending, startTransition] = useTransition();
  const [result, setResult] = useState<WriteResult | null>(null);
  const run = (action: () => Promise<WriteResult>, onSuccess?: () => void) =>
    startTransition(async () => {
      setResult(null);
      const outcome = await action();
      setResult(outcome);
      if (outcome.ok) onSuccess?.();
    });
  return { pending, result, run };
}

function SaveStatus({ result, success }: { result: WriteResult | null; success: string }) {
  if (!result) return null;
  return result.ok ? (
    <p role="status" className="text-sm text-green-700">
      {success}
    </p>
  ) : (
    <p role="alert" className="text-sm text-destructive">
      {result.error} Eingaben wurden nicht gespeichert.
    </p>
  );
}

function AvailabilityForm({
  employeeId,
  date,
  saved,
  shifts,
}: {
  employeeId: number;
  date: string;
  saved?: Availability;
  shifts: ShiftOption[];
}) {
  const [type, setType] = useState<AvailabilityType | typeof NONE>(saved?.availability_type ?? NONE);
  const [shiftIds, setShiftIds] = useState<number[]>(saved?.shift_ids ?? []);
  const [reason, setReason] = useState(saved?.reason ?? "");
  const chosen = new Set(shiftIds);
  const { pending, result, run } = useSave();

  function submit() {
    if (type === NONE) return;
    run(() =>
      saveAvailability(employeeId, date, {
        availability_type: type,
        shift_ids: type === "available_only" ? shiftIds : null,
        reason: reason.trim() || null,
      }),
    );
  }

  return (
    <section className="space-y-3" aria-label="Einschränkung">
      <h3 className="text-sm font-semibold">Einschränkung</h3>
      <Select value={type} onValueChange={(value) => setType(value as AvailabilityType)}>
        <SelectTrigger aria-label="Art der Einschränkung" className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>Keine Einschränkung</SelectItem>
          {Object.entries(AVAILABILITY_LABELS).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {type === "available_only" && (
        <fieldset className="flex flex-wrap gap-3">
          <legend className="sr-only">Erlaubte Schichten</legend>
          {shifts.map((shift) => (
            <Label key={shift.shift_id} className="gap-1.5 font-normal">
              <Checkbox
                checked={chosen.has(shift.shift_id)}
                onCheckedChange={(checked) =>
                  setShiftIds((ids) => (checked ? [...ids, shift.shift_id] : ids.filter((id) => id !== shift.shift_id)))
                }
              />
              {shift.code}
            </Label>
          ))}
        </fieldset>
      )}
      {type !== NONE && (
        <Input
          aria-label="Grund"
          placeholder="Grund (optional)"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
        />
      )}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" onClick={submit} disabled={pending || type === NONE}>
          Einschränkung speichern
        </Button>
        {saved && (
          <Button
            size="sm"
            variant="outline"
            disabled={pending}
            onClick={() =>
              run(
                () => saveAvailability(employeeId, date, null),
                () => setType(NONE),
              )
            }
          >
            Einschränkung entfernen
          </Button>
        )}
      </div>
      <SaveStatus result={result} success="Einschränkung gespeichert." />
    </section>
  );
}

function WishForm({
  employeeId,
  date,
  saved,
  shifts,
}: {
  employeeId: number;
  date: string;
  saved?: { type: WishType; shift_id: number | null };
  shifts: ShiftOption[];
}) {
  const [type, setType] = useState<WishType | typeof NONE>(saved?.type ?? NONE);
  const [shiftId, setShiftId] = useState(saved?.shift_id ? String(saved.shift_id) : "");
  const { pending, result, run } = useSave();
  const needsShift = type === "free_shift" || type === "preferred_shift";

  function submit() {
    if (type === NONE) return;
    run(() =>
      saveWish(employeeId, date, {
        type,
        shift_id: needsShift && shiftId ? Number(shiftId) : null,
      }),
    );
  }

  return (
    <section className="space-y-3" aria-label="Wunsch">
      <h3 className="text-sm font-semibold">Wunsch</h3>
      <p className="flex gap-1.5 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        Wünsche werden gespeichert, aber bei der Dienstplanerstellung derzeit nicht berücksichtigt.
      </p>
      <Select value={type} onValueChange={(value) => setType(value as WishType)}>
        <SelectTrigger aria-label="Art des Wunsches" className="w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={NONE}>Kein Wunsch</SelectItem>
          {Object.entries(WISH_LABELS).map(([value, label]) => (
            <SelectItem key={value} value={value}>
              {label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {needsShift && (
        <Select value={shiftId} onValueChange={setShiftId}>
          <SelectTrigger aria-label="Schicht des Wunsches" className="w-full">
            <SelectValue placeholder="Schicht wählen" />
          </SelectTrigger>
          <SelectContent>
            {shifts.map((shift) => (
              <SelectItem key={shift.shift_id} value={String(shift.shift_id)}>
                {shift.code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
      <div className="flex flex-wrap gap-2">
        <Button size="sm" onClick={submit} disabled={pending || type === NONE}>
          Wunsch speichern
        </Button>
        {saved && (
          <Button
            size="sm"
            variant="outline"
            disabled={pending}
            onClick={() =>
              run(
                () => saveWish(employeeId, date, null),
                () => setType(NONE),
              )
            }
          >
            Wunsch entfernen
          </Button>
        )}
      </div>
      <SaveStatus result={result} success="Wunsch gespeichert." />
    </section>
  );
}
