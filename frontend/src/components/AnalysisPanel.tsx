import { MissingInformation } from "./MissingInformation";
import { RiskFlags } from "./RiskFlags";
import { Sources } from "./Sources";
import type { Recommendation } from "../types/api";

export function AnalysisPanel({ recommendation }: { recommendation: Recommendation }) {
  const review = recommendation.human_review;
  const edited = review?.edited_payload;
  return (
    <div className="analysis">
      <article className="ai-draft">
        <header>
          <p className="eyebrow">AI draft</p>
          <p className="disclaimer">{recommendation.disclaimer}</p>
        </header>
        <p className="meta">
          Status {recommendation.status} · model {recommendation.model} · confidence{" "}
          {recommendation.confidence.toFixed(2)}
        </p>
        <h3>Summary</h3>
        <p>{recommendation.summary}</p>
        <RiskFlags flags={recommendation.risk_flags} />
        <MissingInformation
          missing={recommendation.missing_information}
          questions={recommendation.follow_up_questions}
        />
        <Sources sources={recommendation.source_references} />
      </article>
      {review && (
        <article className="human-decision">
          <header>
            <p className="eyebrow">Underwriter decision</p>
            <p className="disclaimer">{review.disclaimer}</p>
          </header>
          <p className="meta">
            {review.action} by {review.reviewer_id} · {new Date(review.created_at).toLocaleString()}
          </p>
          {review.comment && <p>{review.comment}</p>}
          {edited?.summary && (
            <>
              <h3>Edited summary</h3>
              <p>{edited.summary}</p>
            </>
          )}
          {edited?.missing_information && (
            <MissingInformation missing={edited.missing_information} questions={edited.follow_up_questions ?? []} />
          )}
          {edited?.risk_flags && <RiskFlags flags={edited.risk_flags} />}
        </article>
      )}
    </div>
  );
}
