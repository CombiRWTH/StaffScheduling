import { CARD_DISCLOSURE, Disclosure } from "@/components/disclosure";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { WISH_LABELS, WISH_STATUS_LABELS, formatDate } from "@/lib/labels";
import type { ScheduleReview, WishStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const TONES: Record<WishStatus, string> = {
  granted: "text-green-700",
  denied: "text-amber-700",
  not_grantable: "text-muted-foreground",
};

/** What the schedule made of every wish: the counts as the title, one table row per wish when opened. */
export function WishTable({ review }: { review: ScheduleReview }) {
  const { wishes, wish_counts: counts } = review.solution.check;
  if (wishes.length === 0) return null;
  const employeeName = new Map(review.tables.employees.map((row) => [row.employee_id, row.employee_name]));
  const shiftCode = new Map(review.shifts.map((shift) => [shift.shift_id, shift.code]));
  const rows = [...wishes].sort((a, b) => a.date.localeCompare(b.date) || a.employee_id - b.employee_id);

  return (
    <section aria-label="Wünsche">
      <Disclosure
        className={CARD_DISCLOSURE}
        title={`Wünsche: ${counts.granted} erfüllt · ${counts.denied} nicht erfüllt · ${counts.not_grantable} nicht erfüllbar`}
      >
        <p className="text-muted-foreground">
          Wünsche binden nicht; nicht erfüllbare widersprechen einer Verfügbarkeit oder Zuordnung.
        </p>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Datum</TableHead>
              <TableHead>Mitarbeiter</TableHead>
              <TableHead>Wunsch</TableHead>
              <TableHead>Ergebnis</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={`${row.employee_id}-${row.date}`}>
                <TableCell className="tabular-nums">{formatDate(row.date)}</TableCell>
                <TableCell>{employeeName.get(row.employee_id) ?? `Mitarbeiter ${row.employee_id}`}</TableCell>
                <TableCell>
                  {[WISH_LABELS[row.type], row.shift_id !== null && shiftCode.get(row.shift_id)]
                    .filter(Boolean)
                    .join(" ")}
                </TableCell>
                <TableCell className={cn("font-medium", TONES[row.status])}>{WISH_STATUS_LABELS[row.status]}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Disclosure>
    </section>
  );
}
