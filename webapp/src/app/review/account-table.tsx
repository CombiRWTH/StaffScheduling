import { Disclosure } from "@/components/disclosure";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { STAFF_LEVEL_LABELS, formatHours } from "@/lib/labels";
import type { ScheduleReview } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Every participant's monthly account as the backend computed it, also without duties. */
export function AccountTable({ review }: { review: ScheduleReview }) {
  const tolerance = review.solution.configuration.policy.balance_tolerance_minutes;
  const outside = new Set(
    review.solution.check.findings.filter((row) => row.rule === "monthly_balance").map((row) => row.employee_id),
  );
  const employees = [...review.tables.employees].sort((a, b) =>
    a.employee_name.localeCompare(b.employee_name, "de-DE"),
  );

  return (
    <section aria-label="Monatskonten">
      <Disclosure card title={`Monatskonten (${employees.length} Mitarbeiter)`}>
        <p className="text-sm text-muted-foreground">
          Saldo = Geplant + Gutschriften − Soll; zulässig sind ±{formatHours(tolerance)}.
        </p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Qualifikation</TableHead>
              <TableHead className="text-right">Soll</TableHead>
              <TableHead className="text-right">Gutschriften</TableHead>
              <TableHead className="text-right">Geplant</TableHead>
              <TableHead className="text-right">Saldo</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {employees.map((row) => (
              <TableRow key={row.employee_id}>
                <TableCell>{row.employee_id}</TableCell>
                <TableCell>{row.employee_name}</TableCell>
                <TableCell>{STAFF_LEVEL_LABELS[row.staff_level]}</TableCell>
                <TableCell className="text-right tabular-nums">{formatHours(row.target_minutes)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatHours(row.credited_minutes)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatHours(row.generated_minutes)}</TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums",
                    outside.has(row.employee_id) && "font-semibold text-destructive",
                  )}
                >
                  {formatHours(row.balance_minutes, { signed: true })}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Disclosure>
    </section>
  );
}
