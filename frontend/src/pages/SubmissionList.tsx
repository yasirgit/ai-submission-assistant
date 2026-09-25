import { useEffect, useState } from "react";

import { ApiError, listRuns, listSubmissions } from "../services/api";
import type { AIRun, SubmissionSummary } from "../types/api";

export function SubmissionList({
  userId,
  onOpen,
}: {
  userId: string;
  onOpen: (id: string) => void;
}) {
  const [rows, setRows] = useState<SubmissionSummary[] | null>(null);
  const [runs, setRuns] = useState<AIRun[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setRows(null);
    setError(null);
    Promise.all([listSubmissions(userId), listRuns(userId)])
      .then(([submissions, recent]) => {
        if (!cancelled) {
          setRows(submissions.submissions);
          setRuns(recent.runs);
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : "The list could not be loaded.");
        }
      });
    return () => {
      cancelled = true;
    };
  }, [userId]);

  if (error) {
    return <p className="error">{error}</p>;
  }
  if (rows === null) {
    return <p className="muted">Loading submissions…</p>;
  }
  return (
    <>
      <h2>Submissions</h2>
      {rows.length === 0 ? (
        <p>No submissions are visible to this caller.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Company</th>
              <th>Product</th>
              <th>Status</th>
              <th>Updated</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>
                  <button type="button" className="link" onClick={() => onOpen(row.id)}>
                    {row.company_name}
                  </button>
                </td>
                <td>{row.product}</td>
                <td>{row.status}</td>
                <td>{new Date(row.updated_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      <h2>Recent AI runs</h2>
      {runs.length === 0 ? (
        <p className="muted">No analysis runs for this caller yet.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>When</th>
              <th>Outcome</th>
              <th>Model</th>
              <th>Tools</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((run) => (
              <tr key={run.id}>
                <td>{new Date(run.created_at).toLocaleString()}</td>
                <td>{run.success ? run.outcome : `${run.outcome} (failed)`}</td>
                <td>{run.model}</td>
                <td>{run.tool_calls.join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </>
  );
}
