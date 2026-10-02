/** A labelled list of facts, e.g. scores or settings; `title` heads the list when given. */
export function Facts({ title, facts }: { title?: string; facts: [string, string][] }) {
  return (
    <div className="space-y-1.5">
      {title && <p className="text-muted-foreground">{title}</p>}
      <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
        {facts.map(([label, value]) => (
          <div key={label} className="contents">
            <dt className="text-muted-foreground">{label}</dt>
            <dd className="break-words tabular-nums">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
