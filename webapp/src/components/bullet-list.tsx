export function BulletList({ items, label }: { items: string[]; label?: string }) {
  return (
    <ul className="list-disc space-y-0.5 pl-5" aria-label={label}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}
