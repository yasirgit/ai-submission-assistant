import type { RiskFlag } from "../types/api";

export function RiskFlags({ flags }: { flags: RiskFlag[] }) {
  if (flags.length === 0) {
    return (
      <section>
        <h3>Risk flags</h3>
        <p className="muted">No risk flags on this draft.</p>
      </section>
    );
  }
  return (
    <section>
      <h3>Risk flags</h3>
      <ul className="flags">
        {flags.map((flag) => (
          <li key={`${flag.type}-${flag.description}`}>
            <span className={`severity severity-${flag.severity.toLowerCase()}`}>{flag.severity}</span>
            <strong>{flag.type}</strong>
            <span>{flag.description}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}
