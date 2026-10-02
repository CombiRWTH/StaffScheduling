import { BulletList } from "@/components/bullet-list";
import { cn } from "@/lib/utils";

/** Why a run or schedule is not usable, as titled lists; sections without items are left out. */
export function ProblemBox({ sections }: { sections: [string, string[]][] }) {
  const shown = sections.filter(([, items]) => items.length > 0);
  if (!shown.length) return null;
  return (
    <div
      className={cn(
        "grid gap-4 rounded-lg border border-destructive/30 bg-destructive/5 p-4",
        shown.length > 1 && "md:grid-cols-2",
      )}
    >
      {shown.map(([title, items]) => (
        <div key={title} className="space-y-1.5">
          <p className="font-medium">{title}</p>
          <div className="max-h-64 overflow-y-auto">
            <BulletList items={items} />
          </div>
        </div>
      ))}
    </div>
  );
}
