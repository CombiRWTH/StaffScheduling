import { cn } from "@/lib/utils";

/** The look of a disclosure that stands on the page like a card, rather than inside one. */
export const CARD_DISCLOSURE =
  "rounded-xl bg-card text-card-foreground shadow-sm [&>summary]:px-6 [&>summary]:py-4 [&>div]:px-6";

/** A titled section that starts collapsed: optional detail that should not crowd the page. */
export function Disclosure({
  title,
  children,
  className,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <details className={cn("group rounded-lg border", className)}>
      <summary className="cursor-pointer list-none rounded-lg [&::-webkit-details-marker]:hidden px-4 py-3 font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
        <span aria-hidden className="mr-2 inline-block transition-transform group-open:rotate-90">
          ›
        </span>
        {title}
      </summary>
      <div className="space-y-3 px-4 pb-4">{children}</div>
    </details>
  );
}
