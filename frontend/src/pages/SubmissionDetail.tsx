import { useCallback, useEffect, useState } from "react";

import { AnalysisPanel } from "../components/AnalysisPanel";
import { AuditHistory } from "../components/AuditHistory";
import { ReviewForm } from "../components/ReviewForm";
import { ApiError, analyze, getRecommendation, getSubmission, listAudit, review } from "../services/api";
import type { AuditEvent, Recommendation, ReviewAction, SubmissionDetail as Detail } from "../types/api";

function euro(amount: number): string {
  return new Intl.NumberFormat("en-GB", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  }).format(amount);
}

export function SubmissionDetail({
  userId,
  submissionId,
  onBack,
}: {
  userId: string;
  submissionId: string;
  onBack: () => void;
}) {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [submission, draft, audit] = await Promise.all([
        getSubmission(userId, submissionId),
        getRecommendation(userId, submissionId),
        listAudit(userId, submissionId),
      ]);
      setDetail(submission);
      setRecommendation(draft);
      setEvents(audit.events);
    } catch (caught) {
      setDetail(null);
      setError(caught instanceof ApiError ? caught.message : "The submission could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, [submissionId, userId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAnalysis() {
    setAnalyzing(true);
    setAnalyzeError(null);
    try {
      const draft = await analyze(userId, submissionId);
      setRecommendation(draft);
      const [submission, audit] = await Promise.all([
        getSubmission(userId, submissionId),
        listAudit(userId, submissionId),
      ]);
      setDetail(submission);
      setEvents(audit.events);
    } catch (caught) {
      setAnalyzeError(caught instanceof ApiError ? caught.message : "Analysis failed.");
    } finally {
      setAnalyzing(false);
    }
  }

  async function submitReview(action: ReviewAction, comment: string, editedSummary: string) {
    setSaving(true);
    setReviewError(null);
    try {
      const body =
        action === "EDIT"
          ? { action, comment, edited: { summary: editedSummary.trim() } }
          : { action, comment };
      const updated = await review(userId, submissionId, body);
      setRecommendation(updated);
      const [submission, audit] = await Promise.all([
        getSubmission(userId, submissionId),
        listAudit(userId, submissionId),
      ]);
      setDetail(submission);
      setEvents(audit.events);
    } catch (caught) {
      setReviewError(caught instanceof ApiError ? caught.message : "The decision could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <button type="button" className="link" onClick={onBack}>
        Back to submissions
      </button>
      {loading && <p className="muted">Loading submission…</p>}
      {error && <p className="error">{error}</p>}
      {detail && (
        <>
          <h2>{detail.company.name}</h2>
          <p className="meta">
            {detail.status} · {detail.requested_coverage.product} · limit {euro(detail.requested_coverage.limit_eur)}
          </p>
          <section className="facts">
            <p>Industry {detail.company.industry}</p>
            <p>Revenue {euro(detail.company.annual_revenue_eur)}</p>
            <p>Employees {detail.company.employee_count}</p>
            <p>Countries {detail.company.countries.join(", ")}</p>
            <p>Assignee {detail.assigned_underwriter_id}</p>
          </section>
          <h3>Narrative</h3>
          <p>{detail.narrative}</p>
          <h3>Claims</h3>
          {detail.claims.length === 0 ? (
            <p className="muted">No claims on file.</p>
          ) : (
            <ul>
              {detail.claims.map((claim) => (
                <li key={claim.id}>
                  {claim.year} {claim.claim_type} {euro(claim.amount_eur)}
                </li>
              ))}
            </ul>
          )}
          {detail.status !== "APPROVED" && detail.status !== "REJECTED" && (
            <p>
              <button type="button" onClick={() => void runAnalysis()} disabled={analyzing}>
                {analyzing ? "Analyzing…" : recommendation ? "Analyze again" : "Analyze"}
              </button>
            </p>
          )}
          {analyzing && <p className="muted">The assistant is drafting. This is not a decision.</p>}
          {analyzeError && (
            <p className="error">
              {analyzeError}{" "}
              <button type="button" onClick={() => void runAnalysis()}>
                Retry
              </button>
            </p>
          )}
          {recommendation && <AnalysisPanel recommendation={recommendation} />}
          {recommendation && !recommendation.human_review && detail.status === "READY_FOR_REVIEW" && (
            <ReviewForm pending={saving} error={reviewError} onSubmit={(action, comment, summary) => void submitReview(action, comment, summary)} />
          )}
          <AuditHistory events={events} />
        </>
      )}
    </>
  );
}
