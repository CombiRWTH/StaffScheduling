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
const staffingKey = (stationId: number, shiftId: number, date: string) => `${stationId}|${shiftId}|${date}`;
/** `HH:MM` of an offset timestamp: its Europe/Berlin wall-clock time. */
const clock = (timestamp: string) => timestamp.slice(11, 16);

// Where a duty is worked relative to the employee's dated origin.
type Placement = "home" | "transfer" | "unknown";
// The employee column's text: one line each, as wide as needed up to a cap that is smaller on narrow screens.
const NAME_CELL = "max-w-36 truncate whitespace-nowrap md:max-w-56";
// The dashed border of a transfer, in the cell's text color; shared by cells and legend.
const TRANSFER_BORDER = "outline-2 -outline-offset-2 outline-dashed outline-current";

/**
 * Short labels for the selected stations, so a transfer cell can name its station: a short name as is, a longer
 * one by its initials; full names when initials would collide.
 */
function stationCodes(stations: { planning_unit_id: number; display_name: string }[]) {
  const code = (name: string) =>
    name.length <= 6
      ? name
      : name
          .split(/[\s-]+/)
          .map((word) => word[0]?.toUpperCase() ?? "")
          .join("");
  const codes = stations.map((unit) => code(unit.display_name));
  const distinct = new Set(codes).size === codes.length;
  return new Map(stations.map((unit, index) => [unit.planning_unit_id, distinct ? codes[index] : unit.display_name]));
}

/** The backend leaves the origin empty only for a duty on a date without any membership. */
function placement(duty: DutyRow): Placement {
  if (duty.origin_unit_id === null) return "unknown";
  return duty.origin_unit_id === duty.planning_unit_id ? "home" : "transfer";
}

function dutyTitle(duty: DutyRow) {
  return [
    duty.planning_unit_name,
    `${SHIFT_TYPE_LABELS[duty.shift_type]} ${duty.shift_code} ${clock(duty.start_at)}–${clock(duty.end_at)}`,
    STAFF_LEVEL_LABELS[duty.staff_level],
    duty.origin_unit_name ? `Herkunft ${duty.origin_unit_name}` : "Herkunft unbekannt",
  ].join(" · ");
}

/** The corner tag of a duty whose origin the backend could not date. */
function UnknownOriginTag() {
  return (
    <span
      aria-hidden
      className="absolute -right-1.5 -top-1.5 flex size-3 items-center justify-center rounded-full border border-foreground bg-background text-[8px] font-bold leading-none text-foreground"
    >
      ?
    </span>
  );
}

/** Employees by date with their duties, absences and findings, and each station's staffing per shift. */
export function ScheduleGrid({ review }: { review: ScheduleReview }) {
  const [search, setSearch] = useState("");
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
  // Only with several stations does a transfer cell say where it is worked.
  const codes = stations.length > 1 ? stationCodes(stations) : null;
  const codeLegend = codes
    ? stations
        .filter((unit) => codes.get(unit.planning_unit_id) !== unit.display_name)
        .map((unit) => `${codes.get(unit.planning_unit_id)} = ${unit.display_name}`)
    : [];
  const duties = new Map(tables.duties.map((row) => [key(row.employee_id, row.date), row]));
  const availability = new Map<string, Availability[]>();
  for (const employee of tables.employees) {
    for (const row of employee.hard_availability) {
      const at = key(row.employee_id, row.date);
      availability.set(at, [...(availability.get(at) ?? []), row]);
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
  // Every home unit of the month (the backend only lists memberships of the schedule's units); a duty's own
  // dated origin decides whether it is a transfer.
  const homeOf = new Map(
    employees.map((employee) => [
      employee.employee_id,
      [
        ...new Set(
          employee.memberships
            .filter((row) => row.is_home)
            .flatMap((row) => units.get(row.planning_unit_id)?.display_name ?? []),
        ),
      ].join(", "),
    ]),
  );
  // Staffing per station and shift: required and assigned counts per date over all qualifications.
  const staffing = new Map<string, { required: number; assigned: number; levels: string[] }>();
  for (const row of tables.staffing) {
    const at = staffingKey(row.planning_unit_id, row.shift_id, row.date);
    const cell = staffing.get(at) ?? {
      required: 0,
      assigned: 0,
      levels: [],
    };
    cell.required += row.required_count;
    cell.assigned += row.assigned_count;
    cell.levels.push(`${STAFF_LEVEL_LABELS[row.staff_level]} ${row.assigned_count}/${row.required_count}`);
    staffing.set(at, cell);
  }
  const staffedShifts = (stationId: number) =>
    review.shifts.filter((shift) =>
      tables.staffing.some((row) => row.planning_unit_id === stationId && row.shift_id === shift.shift_id),
    );
  const weekend = (day: (typeof calendar)[number]) => day.weekday >= 6 || day.public_holiday !== null;

  function toggleFullscreen() {
    if (document.fullscreenElement) void document.exitFullscreen();
    else void container.current?.requestFullscreen();
  }

  return (
    <Card aria-label="Dienstplan">
      <CardHeader>
        <CardTitle>Dienstplan</CardTitle>
        <CardDescription>
          Dienste je Mitarbeiter und Tag; Zeiten und Herkunft beim Zeigen auf einen Dienst.
        </CardDescription>
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
            <Button variant="outline" onClick={toggleFullscreen}>
              {fullscreen ? <Minimize /> : <Maximize />}
              {fullscreen ? "Vollbild beenden" : "Vollbild"}
            </Button>
          </div>

          <div className="overflow-x-auto rounded-md border">
            <table className="border-collapse text-xs">
              <thead>
                <tr>
                  <th className="sticky left-0 z-10 border-b bg-background p-2 text-left font-medium">Mitarbeiter</th>
                  {calendar.map((day) => (
                    <th
                      key={day.date}
                      title={day.public_holiday ?? undefined}
                      className={cn(
                        "border-b border-l p-1 text-center font-medium",
                        "min-w-12",
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
                    <th
                      scope="row"
                      className="sticky left-0 z-10 whitespace-nowrap border-b bg-background p-2 text-left font-normal"
                    >
                      {/* The column fits its longest name up to a cap; longer names are cut, the full text on hover. */}
                      <div
                        title={`${employee.employee_id} ${employee.employee_name} · ${homeOf.get(employee.employee_id)}`}
                        className={NAME_CELL}
                      >
                        <span className="text-muted-foreground">{employee.employee_id}</span> {employee.employee_name}
                      </div>
                      <div className={cn(NAME_CELL, "text-muted-foreground")}>{homeOf.get(employee.employee_id)}</div>
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
                            <DutyCell duty={duty} station={codes?.get(duty.planning_unit_id)} />
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
                          const cell = staffing.get(staffingKey(station.planning_unit_id, shift.shift_id, day.date));
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
              .filter((type) => review.shifts.some((shift) => shift.type === type))
              .map((type) => (
                <span key={type} className="flex items-center gap-1.5">
                  <span className={cn("inline-block size-3 rounded", SHIFT_COLORS[type])} />
                  {SHIFT_TYPE_LABELS[type]}
                </span>
              ))}
            <span className="flex items-center gap-1.5">
              <span className={cn("inline-block size-3 rounded", SHIFT_COLORS.other, TRANSFER_BORDER)} />
              Einsatz außerhalb der Herkunft{codes && "; das Kürzel nennt die Station"}
            </span>
            <span className="flex items-center gap-1.5">
              <span className={cn("relative mr-1 inline-block size-3 rounded", SHIFT_COLORS.other)}>
                <UnknownOriginTag />
              </span>
              Herkunft unbekannt
            </span>
            {codeLegend.length > 0 && <span>{codeLegend.join(", ")}</span>}
            <span>{Object.values(AVAILABILITY_SHORT).join(", ")} oder Grund: Abwesenheit oder Einschränkung</span>
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

/**
 * One duty: its shift code and color. The employee column names the origin, so only a duty worked outside it is
 * marked: a dashed border, and with several stations the code of the station where it is worked.
 */
function DutyCell({ duty, station }: { duty: DutyRow; station?: string }) {
  const kind = placement(duty);
  return (
    <div
      title={dutyTitle(duty)}
      // An unknown origin keeps its tag in the right padding, so it never covers the shift code.
      className={cn(
        "relative rounded px-1 py-0.5",
        SHIFT_COLORS[duty.shift_type],
        kind === "unknown" && "pr-3",
        kind === "transfer" && TRANSFER_BORDER,
      )}
    >
      <span aria-hidden>{duty.shift_code}</span>
      <span className="sr-only">
        {dutyTitle(duty)}
        {kind === "transfer" && ", Einsatz außerhalb der Herkunft"}
      </span>
      {kind === "unknown" && <UnknownOriginTag />}
      {station && kind === "transfer" && (
        // A short code such as "BSP-A" stays on one line; only a full name (when codes collide) may wrap.
        <div
          aria-hidden
          className={cn("text-[10px] leading-tight opacity-80", station.length <= 6 && "whitespace-nowrap")}
        >
          {station}
        </div>
      )}
    </div>
  );
}
