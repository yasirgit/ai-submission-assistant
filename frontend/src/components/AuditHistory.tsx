import type { AuditEvent } from "../types/api";

export function AuditHistory({ events }: { events: AuditEvent[] }) {
  return (
    <section>
      <h3>Audit history</h3>
      {events.length === 0 ? (
        <p className="muted">No audit events yet.</p>
      ) : (
        <ol className="audit">
          {events.map((event) => (
            <li key={event.id}>
              <div>
                <strong>{event.action}</strong>
                <span className="muted">{new Date(event.timestamp).toLocaleString()}</span>
              </div>
              <span className="muted">{event.user_id ?? "system"}</span>
              <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
