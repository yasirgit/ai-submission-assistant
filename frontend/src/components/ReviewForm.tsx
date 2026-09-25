import { useState } from "react";

import type { ReviewAction } from "../types/api";

export function ReviewForm({
  pending,
  error,
  onSubmit,
}: {
  pending: boolean;
  error: string | null;
  onSubmit: (action: ReviewAction, comment: string, editedSummary: string) => void;
}) {
  const [action, setAction] = useState<ReviewAction>("ACCEPT");
  const [comment, setComment] = useState("");
  const [editedSummary, setEditedSummary] = useState("");

  const rejectBlocked = action === "REJECT" && comment.trim() === "";
  const editBlocked = action === "EDIT" && editedSummary.trim() === "";

  return (
    <form
      className="review-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(action, comment, editedSummary);
      }}
    >
      <h3>Underwriter review</h3>
      <p className="muted">This is the only action that approves or rejects the submission.</p>
      <div className="choices">
        {(["ACCEPT", "EDIT", "REJECT"] as const).map((choice) => (
          <label key={choice}>
            <input
              type="radio"
              name="action"
              value={choice}
              checked={action === choice}
              onChange={() => setAction(choice)}
            />
            {choice === "ACCEPT" ? "Accept draft" : choice === "EDIT" ? "Edit, then accept" : "Reject"}
          </label>
        ))}
      </div>
      {action === "EDIT" && (
        <label className="stack">
          Your summary
          <textarea
            value={editedSummary}
            onChange={(event) => setEditedSummary(event.target.value)}
            rows={4}
            required
          />
        </label>
      )}
      <label className="stack">
        Comment {action === "REJECT" ? "(required)" : "(optional)"}
        <textarea value={comment} onChange={(event) => setComment(event.target.value)} rows={3} />
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={pending || rejectBlocked || editBlocked}>
        {pending ? "Saving…" : "Record decision"}
      </button>
    </form>
  );
}
