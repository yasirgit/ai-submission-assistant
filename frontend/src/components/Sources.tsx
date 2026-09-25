import type { SourceReference } from "../types/api";

export function Sources({ sources }: { sources: SourceReference[] }) {
  return (
    <section>
      <h3>Sources</h3>
      {sources.length === 0 ? (
        <p className="muted">No retrieved guideline was cited.</p>
      ) : (
        <ul className="sources">
          {sources.map((source) => (
            <li key={source.chunk_id}>
              <strong>{source.title}</strong>
              <span className="muted">
                {source.document_id} · {source.chunk_id}
              </span>
              {source.excerpt && <p>{source.excerpt}</p>}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
