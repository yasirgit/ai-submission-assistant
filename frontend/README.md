# Frontend

React, TypeScript, and Vite. The screen calls the API with `X-User-Id`. That header is a demo stand-in, not a bank login.

```bash
npm install
npm run dev
```

The dev server proxies `/api` to `http://127.0.0.1:8000`. Start the API first. Docker Compose serves this UI on port 8080 and proxies `/api` inside the network.

The page states: **AI-generated assistance — final decision remains with the underwriter.** An amber panel is the model draft. A green panel is the underwriter's accept, edit, or reject. A missing submission says it is unavailable.
