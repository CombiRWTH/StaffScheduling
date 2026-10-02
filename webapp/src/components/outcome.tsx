import { LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";

/** One outcome of a run: a small label, the value and a muted explanation. */
export function Outcome({
  label,
  value,
  detail,
  tone,
  busy,
}: {
  label: string;
  value: string;
  detail: string;
  tone?: string;
  busy?: boolean;
}) {
  return (
    <div className="rounded-lg border bg-muted/30 p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className={cn("mt-1 flex items-center gap-1.5 font-medium", tone)}>
        {busy && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
        {value}
      </p>
      <p className="mt-0.5 text-sm text-muted-foreground">{detail}</p>
    </div>
  );
}
