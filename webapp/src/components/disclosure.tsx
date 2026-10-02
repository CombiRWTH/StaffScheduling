/** A titled section that starts collapsed: optional detail that should not crowd the page. */
export function Disclosure({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <details className="group rounded-lg border">
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
