import { cn } from "@/lib/utils";

/**
 * A titled section that starts collapsed: optional detail that should not crowd the page. `card` lets it stand on
 * the page like a card, rather than inside one.
 */
export function Disclosure({
  title,
  children,
  card = false,
}: {
  title: string;
  children: React.ReactNode;
  card?: boolean;
}) {
  return (
    <details
      className={cn("group", card ? "rounded-xl border bg-card text-card-foreground shadow-sm" : "rounded-lg border")}
    >
      <summary
        className={cn(
          "cursor-pointer list-none rounded-lg [&::-webkit-details-marker]:hidden font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          card ? "px-6 py-4" : "px-4 py-3",
        )}
      >
        <span aria-hidden className="mr-2 inline-block transition-transform group-open:rotate-90">
          ›
        </span>
        {title}
      </summary>
      <div className={cn("space-y-3 pb-4", card ? "px-6" : "px-4")}>{children}</div>
    </details>
  );
}
