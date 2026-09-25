import { useEffect, useState } from "react";

import { SubmissionDetail } from "./pages/SubmissionDetail";
import { SubmissionList } from "./pages/SubmissionList";
import { CALLERS, DISCLAIMER } from "./types/api";

const STORAGE_KEY = "insurance-user-id";

function currentPath(): string {
  return window.location.pathname;
}

export function App() {
  const [userId, setUserId] = useState(() => sessionStorage.getItem(STORAGE_KEY) ?? CALLERS[0].id);
  const [path, setPath] = useState(currentPath);

  useEffect(() => {
    sessionStorage.setItem(STORAGE_KEY, userId);
  }, [userId]);

  useEffect(() => {
    const onPop = () => setPath(currentPath());
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
  }, []);

  function go(next: string) {
    window.history.pushState({}, "", next);
    setPath(next);
  }

  const submissionId = path.startsWith("/submissions/") ? decodeURIComponent(path.slice("/submissions/".length)) : null;
  const caller = CALLERS.find((item) => item.id === userId) ?? CALLERS[0];

  return (
    <>
      <header className="top">
        <div>
          <p className="brand">Insurance submission assistant</p>
          <p className="disclaimer">{DISCLAIMER}</p>
        </div>
        <label>
          Caller
          <select value={userId} onChange={(event) => setUserId(event.target.value)}>
            {CALLERS.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label} — {item.role}
              </option>
            ))}
          </select>
          <span className="muted">{caller.id}</span>
        </label>
      </header>
      <main>
        {submissionId ? (
          <SubmissionDetail key={`${userId}:${submissionId}`} userId={userId} submissionId={submissionId} onBack={() => go("/")} />
        ) : (
          <SubmissionList key={userId} userId={userId} onOpen={(id) => go(`/submissions/${id}`)} />
        )}
      </main>
    </>
  );
}
