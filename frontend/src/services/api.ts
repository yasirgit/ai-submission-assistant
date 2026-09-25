import type {
  AIRun,
  AuditEvent,
  Recommendation,
  SubmissionDetail,
  SubmissionSummary,
} from "../types/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, userId: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      Accept: "application/json",
      "X-User-Id": userId,
      ...(init?.body ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  const text = await response.text();
  const body = text ? (JSON.parse(text) as unknown) : null;
  if (!response.ok) {
    throw new ApiError(response.status, messageFrom(body, response.status));
  }
  return body as T;
}

function messageFrom(body: unknown, status: number): string {
  if (status === 404) {
    return "This submission is unavailable.";
  }
  if (!body || typeof body !== "object" || !("detail" in body)) {
    return "The request failed.";
  }
  const detail = (body as { detail: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return "The request was rejected.";
      })
      .join(" ");
  }
  return "The request failed.";
}

export function listSubmissions(userId: string): Promise<{ submissions: SubmissionSummary[] }> {
  return request("/api/submissions", userId);
}

export function getSubmission(userId: string, id: string): Promise<SubmissionDetail> {
  return request(`/api/submissions/${id}`, userId);
}

export async function getRecommendation(userId: string, id: string): Promise<Recommendation | null> {
  try {
    return await request(`/api/submissions/${id}/recommendation`, userId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      return null;
    }
    throw error;
  }
}

export function analyze(userId: string, id: string): Promise<Recommendation> {
  return request(`/api/submissions/${id}/analyze`, userId, { method: "POST" });
}

export function review(
  userId: string,
  id: string,
  body: { action: "ACCEPT" | "EDIT" | "REJECT"; comment: string; edited?: { summary: string } },
): Promise<Recommendation> {
  return request(`/api/submissions/${id}/review`, userId, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function listAudit(userId: string, id: string): Promise<{ events: AuditEvent[] }> {
  return request(`/api/submissions/${id}/audit`, userId);
}

export function listRuns(userId: string): Promise<{ runs: AIRun[] }> {
  return request("/api/ai-runs?limit=8", userId);
}
