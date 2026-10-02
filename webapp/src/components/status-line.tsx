import { CircleAlert, CircleCheck, CircleX, LoaderCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type Tone = "busy" | "success" | "warning" | "error";

const TONES: Record<Tone, { icon: typeof CircleCheck; className: string }> = {
  busy: { icon: LoaderCircle, className: "text-foreground" },
  success: { icon: CircleCheck, className: "text-green-700" },
  warning: { icon: CircleAlert, className: "text-amber-700" },
  error: { icon: CircleX, className: "text-destructive" },
};

/** One outcome sentence: an icon and title in the outcome's tone, then what it means or what to do next. */
export function StatusLine({ tone, title, hint }: { tone: Tone; title: string; hint: string }) {
  const { icon: Icon, className } = TONES[tone];
  return (
    <p className="pt-1">
      <Icon
        className={cn("mr-1.5 inline size-4 align-[-3px]", className, tone === "busy" && "animate-spin")}
        aria-hidden
      />
      <span className={cn("font-medium", className)}>{title}</span>
      <span className="text-muted-foreground"> · {hint}</span>
    </p>
  );
}
