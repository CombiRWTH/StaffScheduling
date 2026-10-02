"use client";

import { Fragment, useEffect, useRef, useState } from "react";
import { Maximize, Minimize, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { AVAILABILITY_LABELS, SHIFT_TYPE_LABELS, STAFF_LEVEL_LABELS, WEEKDAYS } from "@/lib/labels";
import type { Availability, DutyRow, ScheduleReview, ShiftType } from "@/lib/types";
import { cn } from "@/lib/utils";

// Shift colors of the original schedule view; class names stay literal for Tailwind's scanner.
const SHIFT_COLORS: Record<ShiftType, string> = {
  early: "bg-[#a8d51f] text-black",
  intermediate: "bg-[#3a9ea1] text-white",
  late: "bg-[#f69e17] text-black",
  night: "bg-[#225e62] text-white",
  management: "bg-[#bfbdfb] text-black",
  other: "bg-[#dadada] text-black",
};
const AVAILABILITY_SHORT: Record<Availability["availability_type"], string> = {
  unavailable: "–",
  vacation: "U",
  training: "FB",
  free_day: "Fr",
  available_only: "nur",
};

const key = (employeeId: number, date: string) => `${employeeId}|${date}`;
/** `HH:MM` of an offset timestamp: its Europe/Berlin wall-clock time. */
const clock = (timestamp: string) => timestamp.slice(11, 16);

function dutyTitle(duty: DutyRow) {
  return [
    duty.planning_unit_name,
    `${SHIFT_TYPE_LABELS[duty.shift_type]} ${duty.shift_code} ${clock(duty.start_at)}–${clock(duty.end_at)}`,
    STAFF_LEVEL_LABELS[duty.staff_level],
    duty.origin_unit_name ? `Herkunft ${duty.origin_unit_name}` : "Herkunft unbekannt",
  ].join(" · ");
}

/** Employees by date with their duties, absences and findings, and each station's staffing per shift. */
export function ScheduleGrid({ review }: { review: ScheduleReview }) {
  const [search, setSearch] = useState("");
  const [compact, setCompact] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const update = () => setFullscreen(document.fullscreenElement === container.current);
    document.addEventListener("fullscreenchange", update);
    return () => document.removeEventListener("fullscreenchange", update);
  }, []);

  const { tables, calendar } = review;
  const units = new Map(review.planning_units.map((unit) => [unit.planning_unit_id, unit]));
  const stations = review.planning_units.filter((unit) => unit.type === "station");
  const shifts = new Map(review.shifts.map((shift) => [shift.shift_id, shift]));
  const duties = new Map(tables.duties.map((row) => [key(row.employee_id, row.date), row]));
  const availability = new Map<string, Availability[]>();
  for (const employee of tables.employees) {
    for (const row of employee.hard_availability) {
      availability.set(key(row.employee_id, row.date), [
        ...(availability.get(key(row.employee_id, row.date)) ?? []),
        row,
      ]);
    }
  }
  const findings = new Set(
    review.solution.check.findings.flatMap((row) =>
      row.employee_id && row.date ? [key(row.employee_id, row.date)] : [],
    ),
  );
  const needle = search.toLocaleLowerCase("de-DE");
  const employees = tables.employees
    .filter((row) => `${row.employee_id} ${row.employee_name}`.toLocaleLowerCase("de-DE").includes(needle))
    .sort((a, b) => a.employee_name.localeCompare(b.employee_name, "de-DE"));
  const home = (employee: (typeof employees)[number]) => {
    const membership = employee.memberships.find((row) => row.is_home);
    return membership ? units.get(membership.planning_unit_id)?.display_name : undefined;
  };
  // Staffing per station and shift: required and assigned counts per date over all qualifications.
  const staffing = new Map<string, { required: number; assigned: number; levels: string[] }>();
  for (const row of tables.staffing) {
    const cell = staffing.get(`${row.planning_unit_id}|${row.shift_id}|${row.date}`) ?? {
      required: 0,
      assigned: 0,
      levels: [],
    };
    cell.required += row.required_count;
    cell.assigned += row.assigned_count;
    cell.levels.push(`${STAFF_LEVEL_LABELS[row.staff_level]} ${row.assigned_count}/${row.required_count}`);
    staffing.set(`${row.planning_unit_id}|${row.shift_id}|${row.date}`, cell);
  }
  const staffedShifts = (stationId: number) =>
    review.shifts.filter((shift) =>
      tables.staffing.some((row) => row.planning_unit_id === stationId && row.shift_id === shift.shift_id),
    );
  const weekend = (day: (typeof calendar)[number]) => day.weekday >= 6 || day.public_holiday !== null;
  const cellWidth = compact ? "min-w-7" : "min-w-11";

  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void container.current?.requestFullscreen();
  }

  return (
    <Card aria-label="Dienstplan">
      <CardHeader>
        <CardTitle>Dienstplan</CardTitle>
        <CardDescription>Dienste je Mitarbeiter und Tag; Details beim Zeigen auf einen Dienst.</CardDescription>
      </CardHeader>
      <CardContent>
        <div ref={container} className={cn("space-y-4", fullscreen && "overflow-auto bg-background p-4")}>
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-64 flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                aria-label="Mitarbeiter im Dienstplan suchen"
                placeholder="Suche nach Name oder ID…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="outline" aria-pressed={compact} onClick={() => setCompact(!compact)}>
              Kompakt
            </Button>
            <Button variant="outline" onClick={toggleFullscreen}>
              {fullscreen ? <Minimize /> : <Maximize />}
              {fullscreen ? "Vollbild beenden" : "Vollbild"}
            </Button>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <table className="border-collapse text-xs">
              <thead>
                <tr>
                  <th className="sticky left-0 z-10 min-w-56 border-b bg-background p-2 text-left font-medium">
                    Mitarbeiter
                  </th>
                  {calendar.map((day) => (
                    <th
                      key={day.date}
                      title={day.public_holiday ?? undefined}
                      className={cn(
                        "border-b border-l p-1 text-center font-medium",
                        cellWidth,
                        weekend(day) && "bg-muted",
                      )}
                    >
                      <div>{Number(day.date.slice(8))}</div>
                      <div className="font-normal text-muted-foreground">{WEEKDAYS[day.weekday - 1]}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {employees.map((employee) => (
                  <tr key={employee.employee_id}>
                    <th scope="row" className="sticky left-0 z-10 border-b bg-background p-2 text-left font-normal">
                      <span className="text-muted-foreground">{employee.employee_id}</span> {employee.employee_name}
                      {!compact && <div className="text-muted-foreground">{home(employee)}</div>}
                    </th>
                    {calendar.map((day) => {
                      const duty = duties.get(key(employee.employee_id, day.date));
                      const absent = availability.get(key(employee.employee_id, day.date)) ?? [];
                      const finding = findings.has(key(employee.employee_id, day.date));
                      return (
                        <td
                          key={day.date}
                          className={cn(
                            "border-b border-l p-0.5 text-center",
                            weekend(day) && "bg-muted",
                            finding && "ring-2 ring-inset ring-destructive",
                          )}
                        >
                          {duty ? (
                            <div
                              title={dutyTitle(duty)}
                              className={cn("rounded px-1 py-0.5", SHIFT_COLORS[duty.shift_type])}
                            >
                              {duty.shift_code}
                              {!compact && stations.length > 1 && (
                                <div className="truncate text-[10px] opacity-80">{duty.planning_unit_name}</div>
                              )}
                            </div>
                          ) : absent.length ? (
                            <span
                              title={absent
                                .map(
                                  (row) =>
                                    `${AVAILABILITY_LABELS[row.availability_type]}${row.reason ? ` (${row.reason})` : ""}`,
                                )
                                .join(", ")}
                              className="text-muted-foreground"
                            >
                              {absent[0].reason ?? AVAILABILITY_SHORT[absent[0].availability_type]}
                            </span>
                          ) : null}
                        </td>
                      );
                    })}
                  </tr>
                ))}
                {stations.map((station) => (
                  <Fragment key={station.planning_unit_id}>
                    <tr>
                      <th
                        colSpan={calendar.length + 1}
                        className="sticky left-0 border-b bg-muted/50 p-2 text-left font-medium"
                      >
                        Besetzung {station.display_name}
                      </th>
                    </tr>
                    {staffedShifts(station.planning_unit_id).map((shift) => (
                      <tr key={shift.shift_id}>
                        <th scope="row" className="sticky left-0 z-10 border-b bg-background p-2 text-left font-normal">
                          {SHIFT_TYPE_LABELS[shift.type]} {shift.code}
                        </th>
                        {calendar.map((day) => {
                          const cell = staffing.get(`${station.planning_unit_id}|${shift.shift_id}|${day.date}`);
                          return (
                            <td
                              key={day.date}
                              title={cell?.levels.join(", ")}
                              className={cn(
                                "border-b border-l p-1 text-center tabular-nums",
                                weekend(day) && "bg-muted",
                                cell && cell.assigned < cell.required && "font-semibold text-destructive",
                              )}
                            >
                              {cell && `${cell.assigned}/${cell.required}`}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </Fragment>
                ))}
              </tbody>
            </table>
          </div>
          {!employees.length && <p className="text-sm text-muted-foreground">Kein Mitarbeiter passt zur Suche.</p>}

          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground" aria-label="Legende">
            {(Object.keys(SHIFT_TYPE_LABELS) as ShiftType[])
              .filter((type) => [...shifts.values()].some((shift) => shift.type === type))
              .map((type) => (
                <span key={type} className="flex items-center gap-1.5">
                  <span className={cn("inline-block size-3 rounded", SHIFT_COLORS[type])} />
                  {SHIFT_TYPE_LABELS[type]}
                </span>
              ))}
            <span>Grund oder Kürzel (U, FB, Fr, nur …): Abwesenheit oder Einschränkung</span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block size-3 rounded ring-2 ring-inset ring-destructive" />
              Regelverstoß
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block size-3 rounded bg-muted" />
              Wochenende oder Feiertag
            </span>
            <span>Besetzung: zugeteilt/benötigt, rot bei Unterbesetzung</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
