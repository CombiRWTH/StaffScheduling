import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { STAFF_LEVEL_LABELS } from "@/lib/labels";
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
    <Card aria-label="Monatskonten" className="max-w-5xl">
      <CardHeader>
        <CardTitle>Monatskonten</CardTitle>
        <CardDescription>
          Saldo = geplante Minuten + Gutschriften − Soll; zulässig sind ±{tolerance} min.
        </CardDescription>
      </CardHeader>
      <CardContent>
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
                <TableCell className="text-right tabular-nums">{row.target_minutes} min</TableCell>
                <TableCell className="text-right tabular-nums">{row.credited_minutes} min</TableCell>
                <TableCell className="text-right tabular-nums">{row.generated_minutes} min</TableCell>
                <TableCell
                  className={cn(
                    "text-right tabular-nums",
                    outside.has(row.employee_id) && "font-semibold text-destructive",
                  )}
                >
                  {row.balance_minutes > 0 ? "+" : ""}
                  {row.balance_minutes} min
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
