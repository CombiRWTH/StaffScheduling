"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { PlanningInspection } from "@/features/planning/models";

export function EmployeesPageClient({ inspection }: { inspection: PlanningInspection }) {
  const [search, setSearch] = useState("");
  const [unitFilter, setUnitFilter] = useState("");
  const units = new Map(inspection.planning_units.map((unit) => [unit.planning_unit_id, unit]));
  const stations = inspection.selected_station_ids.map((id) => units.get(id)?.display_name).join(", ");
  const pools = inspection.planning_units.filter((unit) => unit.type === "shared_pool");
  const filtered = inspection.employees.filter(
    (employee) =>
      (!unitFilter || employee.memberships.some((row) => row.planning_unit_id === Number(unitFilter))) &&
      `${employee.employee_id} ${employee.display_name} ${employee.staff_level} ${employee.memberships.map((row) => `${units.get(row.planning_unit_id)?.display_name} ${row.staff_level}`).join(" ")}`
        .toLocaleLowerCase("de-DE")
        .includes(search.toLocaleLowerCase("de-DE")),
  );
  return (
    <Card>
      <CardHeader>
        <CardTitle>Mitarbeiter</CardTitle>
        <CardDescription>
          {inspection.planning_month.start} bis {inspection.planning_month.end} · {stations}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p>
          Pool-Kontext:{" "}
          {pools.length
            ? pools.map((pool) => pool.display_name).join(", ")
            : "Kein zugehöriger Pool in den Mitgliedschaften."}
        </p>
        <p className="text-sm text-muted-foreground">
          Nur Lesen. Pool-Herkunft und Einsatzberechtigung auf einer Station sind getrennte Angaben.
        </p>
        <div className="flex flex-wrap gap-3">
          <Input
            aria-label="Mitarbeiter suchen"
            placeholder="Name, ID, Qualifikation oder Einheit"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
          <label>
            Einheit{" "}
            <select
              aria-label="Einheit filtern"
              className="rounded-md border p-2"
              value={unitFilter}
              onChange={(event) => setUnitFilter(event.target.value)}
            >
              <option value="">Alle Einheiten</option>
              {inspection.planning_units.map((unit) => (
                <option key={unit.planning_unit_id} value={unit.planning_unit_id}>
                  {unit.display_name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {!inspection.employees.length ? (
          <p>Keine Mitarbeiter für diese Auswahl vorhanden.</p>
        ) : !filtered.length ? (
          <p>Keine Mitarbeiter für diesen Filter gefunden.</p>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead>Qualifikation</TableHead>
                <TableHead>Details</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((employee) => (
                <TableRow key={employee.employee_id}>
                  <TableCell>{employee.employee_id}</TableCell>
                  <TableCell>{employee.display_name}</TableCell>
                  <TableCell>
                    <Badge>{employee.staff_level}</Badge>
                  </TableCell>
                  <TableCell>
                    <details>
                      <summary className="cursor-pointer">Details für {employee.display_name}</summary>
                      <div className="space-y-3 py-3">
                        <h2 className="font-semibold">Datierte Mitgliedschaften</h2>
                        <ul>
                          {employee.memberships.map((row, index) => (
                            <li key={`${row.planning_unit_id}:${row.valid_from}:${index}`}>
                              {units.get(row.planning_unit_id)?.display_name} ({units.get(row.planning_unit_id)?.type})
                              · {row.valid_from} bis {row.valid_until ?? "offen"} · {row.staff_level} · Heimat:{" "}
                              {row.is_home ? "ja" : "nein"} · Ersatz: {row.is_replacement ? "ja" : "nein"}
                            </li>
                          ))}
                        </ul>
                        <h2 className="font-semibold">Monatskonto (Minuten)</h2>
                        <p>
                          Ziel: {employee.account.target_minutes} · Ist:{" "}
                          {employee.account.actual_minutes ?? "nicht verfügbar"} · Verifizierte Gutschriften:{" "}
                          {employee.account.credited_minutes}
                        </p>
                        <p>Nachweis: {employee.account.evidence_source}</p>
                        {employee.account.credit_details.length ? (
                          <ul>
                            {employee.account.credit_details.map((credit, index) => (
                              <li key={index}>
                                {credit.date} · {credit.minutes} Minuten · {credit.kind} · {credit.source}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p>Explizit keine Gutschriften.</p>
                        )}
                        <h2 className="font-semibold">Harte Einschränkungen</h2>
                        <p>Vollständigkeitsnachweis: {employee.restrictions_source}</p>
                        {employee.hard_restrictions.length ? (
                          <ul>
                            {employee.hard_restrictions.map((row, index) => (
                              <li key={index}>
                                {row.date} · {row.availability_type} · {row.reason ?? "ohne Zusatzgrund"} ·{" "}
                                {row.source ?? employee.restrictions_source}
                                {row.shift_ids ? ` · Erlaubte Schicht-IDs: ${row.shift_ids.join(", ")}` : ""}
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p>Explizit keine harten Einschränkungen.</p>
                        )}
                      </div>
                    </details>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
