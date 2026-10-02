"use client";

import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { Employee, PlanningInspection, PlanningUnit, WorkCredit } from "@/lib/types";
import { AVAILABILITY_LABELS, STAFF_LEVEL_LABELS, formatDate, formatHours } from "@/lib/labels";
import { MONTHS } from "@/lib/selection";

const UNIT_TYPE_LABELS: Record<PlanningUnit["type"], string> = { station: "Station", jumper_pool: "Springerpool" };
const CREDIT_LABELS: Record<WorkCredit["kind"], string> = {
  approved_absence: "Genehmigte Abwesenheit",
  trusted_work: "Anerkannte Arbeit",
};
const ALL_UNITS = "all";

function formatMonth(value: string) {
  const [year, month] = value.split("-");
  return `${MONTHS[Number(month) - 1]} ${year}`;
}

export function EmployeeTable({ inspection }: { inspection: PlanningInspection }) {
  const [search, setSearch] = useState("");
  const [unitFilter, setUnitFilter] = useState(ALL_UNITS);
  const [expanded, setExpanded] = useState<number | null>(null);
  const units = new Map(inspection.planning_units.map((unit) => [unit.planning_unit_id, unit]));
  const unitName = (id: number) => units.get(id)?.display_name ?? `Einheit ${id}`;
  const stations = inspection.selected_station_ids.map(unitName).join(", ");
  const needle = search.toLocaleLowerCase("de-DE");
  const filtered = inspection.employees.filter(
    (employee) =>
      (unitFilter === ALL_UNITS || employee.memberships.some((row) => row.planning_unit_id === Number(unitFilter))) &&
      [
        employee.employee_id,
        employee.display_name,
        STAFF_LEVEL_LABELS[employee.staff_level],
        ...employee.memberships.map((row) => unitName(row.planning_unit_id)),
      ]
        .join(" ")
        .toLocaleLowerCase("de-DE")
        .includes(needle),
  );

  return (
    <div>
      <Card>
        <CardHeader>
          <CardTitle>{inspection.employees.length} Mitarbeiter</CardTitle>
          <CardDescription>
            {formatMonth(inspection.planning_month.start)} · {stations}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-3">
            <div className="relative min-w-64 flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                aria-label="Mitarbeiter suchen"
                placeholder="Suche nach Name, ID, Qualifikation oder Einheit…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
                className="pl-9"
              />
            </div>
            <Select value={unitFilter} onValueChange={setUnitFilter}>
              <SelectTrigger className="w-56" aria-label="Einheit filtern">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_UNITS}>Alle Einheiten</SelectItem>
                {inspection.planning_units.map((unit) => (
                  <SelectItem key={unit.planning_unit_id} value={String(unit.planning_unit_id)}>
                    {unit.display_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {!inspection.employees.length ? (
            <p className="py-12 text-center text-muted-foreground">Keine Mitarbeiter für diese Auswahl vorhanden.</p>
          ) : !filtered.length ? (
            <p className="py-12 text-center text-muted-foreground">Keine Mitarbeiter für diesen Filter gefunden.</p>
          ) : (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-10" />
                    <TableHead>ID</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Qualifikation</TableHead>
                    <TableHead>Einheiten</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((employee) => {
                    const open = expanded === employee.employee_id;
                    return (
                      <Fragment key={employee.employee_id}>
                        <TableRow>
                          <TableCell>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="size-7"
                              aria-expanded={open}
                              aria-label={`Details für ${employee.display_name}`}
                              onClick={() => setExpanded(open ? null : employee.employee_id)}
                            >
                              {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                            </Button>
                          </TableCell>
                          <TableCell className="tabular-nums text-muted-foreground">{employee.employee_id}</TableCell>
                          <TableCell className="font-medium">{employee.display_name}</TableCell>
                          <TableCell>{STAFF_LEVEL_LABELS[employee.staff_level]}</TableCell>
                          <TableCell className="text-muted-foreground">
                            {[...new Set(employee.memberships.map((row) => unitName(row.planning_unit_id)))].join(", ")}
                          </TableCell>
                        </TableRow>
                        {open && (
                          <TableRow className="bg-muted/30 hover:bg-muted/30">
                            <TableCell colSpan={5} className="whitespace-normal">
                              <EmployeeDetails employee={employee} unitName={unitName} units={units} />
                            </TableCell>
                          </TableRow>
                        )}
                      </Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function EmployeeDetails({
  employee,
  unitName,
  units,
}: {
  employee: Employee;
  unitName: (id: number) => string;
  units: Map<number, PlanningUnit>;
}) {
  const { account } = employee;
  return (
    <div className="grid gap-6 px-2 py-3 md:grid-cols-3">
      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Zuordnungen</h3>
        <ul className="space-y-1.5 text-sm">
          {employee.memberships.map((row) => {
            const type = units.get(row.planning_unit_id)?.type;
            return (
              <li key={`${row.planning_unit_id}:${row.valid_from}:${row.valid_until}:${row.staff_level}`}>
                <span className="font-medium">{unitName(row.planning_unit_id)}</span>
                {type && <span className="text-muted-foreground"> ({UNIT_TYPE_LABELS[type]})</span>}
                <div className="text-muted-foreground">
                  {formatDate(row.valid_from)} – {row.valid_until ? formatDate(row.valid_until) : "offen"} ·{" "}
                  {STAFF_LEVEL_LABELS[row.staff_level]}
                  {row.is_home && " · Heimat"}
                  {row.is_replacement && " · Ersatz"}
                </div>
              </li>
            );
          })}
        </ul>
      </section>
      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Monatskonto</h3>
        <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 text-sm">
          <dt className="text-muted-foreground">Soll</dt>
          <dd>{formatHours(account.target_minutes)}</dd>
          <dt className="text-muted-foreground">Ist</dt>
          <dd>{account.actual_minutes === null ? "nicht verfügbar" : formatHours(account.actual_minutes)}</dd>
          <dt className="text-muted-foreground">Gutschriften</dt>
          <dd>{formatHours(account.credited_minutes)}</dd>
        </dl>
        {account.credit_details.length ? (
          <ul className="space-y-1 text-sm">
            {account.credit_details.map((credit) => (
              <li key={`${credit.date}:${credit.kind}:${credit.source}`}>
                {formatDate(credit.date)} · {formatHours(credit.minutes)} · {CREDIT_LABELS[credit.kind]}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Keine Gutschriften.</p>
        )}
      </section>
      <section className="space-y-2">
        <h3 className="text-sm font-semibold">Verfügbarkeit</h3>
        {employee.availability.length ? (
          <ul className="space-y-1 text-sm">
            {employee.availability.map((row) => (
              <li key={`${row.date}:${row.availability_type}:${row.reason}:${row.source}:${row.shift_ids}`}>
                {formatDate(row.date)} · {AVAILABILITY_LABELS[row.availability_type]}
                {row.reason && ` · ${row.reason}`}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">Keine Abwesenheiten oder Einschränkungen.</p>
        )}
      </section>
    </div>
  );
}
