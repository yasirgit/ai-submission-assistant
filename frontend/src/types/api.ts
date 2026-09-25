export type SubmissionStatus =
  | "NEW"
  | "PROCESSING"
  | "READY_FOR_REVIEW"
  | "APPROVED"
  | "REJECTED";

export type RecommendationStatus = "DRAFT" | "ACCEPTED" | "EDITED" | "REJECTED";

export type ReviewAction = "ACCEPT" | "EDIT" | "REJECT";

export interface SubmissionSummary {
  id: string;
  company_id: string;
  company_name: string;
  status: SubmissionStatus;
  assigned_underwriter_id: string;
  team_id: string | null;
  product: string;
  created_at: string;
  updated_at: string;
}

export interface Claim {
  id: string;
  year: number;
  claim_type: string;
  amount_eur: number;
  description: string;
}

export interface SubmissionDetail {
  id: string;
  company: {
    id: string;
    name: string;
    industry: string;
    annual_revenue_eur: number;
    employee_count: number;
    countries: string[];
  };
  status: SubmissionStatus;
  created_by: string;
  assigned_underwriter_id: string;
  team_id: string | null;
  requested_coverage: { product: string; limit_eur: number };
  existing_policy: { carrier: string; limit_eur: number } | null;
  narrative: string;
  claims: Claim[];
  created_at: string;
  updated_at: string;
}

export interface RiskFlag {
  type: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  description: string;
}

export interface SourceReference {
  document_id: string;
  chunk_id: string;
  title: string;
  excerpt: string;
}

export interface HumanReview {
  id: string;
  action: ReviewAction;
  comment: string;
  edited_payload: {
    summary?: string;
    risk_flags?: RiskFlag[];
    missing_information?: string[];
    follow_up_questions?: string[];
  } | null;
  reviewer_id: string;
  created_at: string;
  disclaimer: string;
}

export interface Recommendation {
  id: string;
  submission_id: string;
  summary: string;
  extracted_data: Record<string, unknown>;
  risk_flags: RiskFlag[];
  missing_information: string[];
  follow_up_questions: string[];
  confidence: number;
  source_references: SourceReference[];
  model: string;
  status: RecommendationStatus;
  created_at: string;
  human_review: HumanReview | null;
  disclaimer: string;
}

export interface AuditEvent {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string;
  timestamp: string;
  metadata: Record<string, unknown>;
  request_id: string | null;
}

export interface AIRun {
  id: string;
  request_id: string;
  user_id: string;
  submission_id: string | null;
  model: string;
  latency_ms: number | null;
  retrieved_document_ids: string[];
  tool_calls: string[];
  success: boolean;
  outcome: string;
  token_usage: { prompt_tokens?: number; completion_tokens?: number } | null;
  created_at: string;
}

export const DISCLAIMER =
  "AI-generated assistance — final decision remains with the underwriter.";

export const CALLERS = [
  { id: "user-alice", label: "Alice Berger", role: "Underwriter, North" },
  { id: "user-noah", label: "Noah Keller", role: "Underwriter, North" },
  { id: "user-bob", label: "Bob Steiner", role: "Underwriter, South" },
  { id: "user-mia", label: "Mia Hoffmann", role: "Manager, North" },
  { id: "user-alex", label: "Alex Wagner", role: "Admin" },
] as const;
