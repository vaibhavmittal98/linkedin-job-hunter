---
name: linkedin-frontend
description: Use when modifying the React UI, adding pages, debugging frontend issues, or understanding component structure in linkedin-job-hunter.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, frontend, react, typescript, vite]
    related_skills: [linkedin-project-overview, linkedin-scoring, linkedin-cover-letters]
---

# Frontend — LinkedIn Job Hunter

## Tech: React 18 + TypeScript + Vite

## Key Files

### `frontend/src/api.ts` — Central API client
- `authFetch()` — wraps fetch with auth headers + auto-logout on 401
- All API functions use `authFetch`
- Token stored in `localStorage.getItem("token")`

### `frontend/src/App.tsx` — Routing
- `ProtectedRoute` — redirects to `/login` if no token
- Routes: `/`, `/jobs/:id`, `/scrape`, `/cover-letter`, `/schedule`, `/profile`, `/signup`, `/login`

### `frontend/src/components/RefineBox.tsx` — Shared refine input + button
- Used by BOTH JobDetail and CoverLetter. Refine behavior defined once.
- Props: `refineFn(message) => Promise<{content}>` and `onRefined(content)`.
- Owns its own `message`/`refining` state; resets in a `finally` block so the button never gets stuck on "Refining...".
- When changing refine UX, edit this component — do NOT reintroduce inline handlers.

### `frontend/src/components/CopyButton.tsx` — Shared copy-to-clipboard button
- Used by cover letter views (JobDetail + CoverLetter) and by each assistant reply in `ChatBox`.
- Prop: `text` (string to copy), optional `style`. Shows brief "Copied!" confirmation, then reverts after 2s.
- Falls back to hidden `<textarea>` + `execCommand("copy")` when async Clipboard API is unavailable.

### `frontend/src/components/ChatBox.tsx` — Shared Q&A chat widget
- Used by BOTH JobDetail and CoverLetter for stateless Q&A chat about the job + CV.
- Prop: `sendFn(messages) => Promise<{reply}>` (caller decides context). Optional `placeholder`.
- Owns conversation history + input + `sending` state in component state only — **nothing persisted**.
- Has a **Reset** button to clear the conversation.
- JobDetail wires it to `jobChat(jobId, messages)`. CoverLetter wires it to `chat(messages, description, title, company)`.
- Each assistant reply gets a `CopyButton`.

## Pages

| Page | File | Purpose |
|------|------|---------|
| Dashboard | `Dashboard.tsx` | Paginated job list, server-side filters, opens in new tab |
| JobDetail | `JobDetail.tsx` | Full job view, score, cover letter, refine, PDF, delete, apply, chat |
| Scrape | `Scrape.tsx` | Keywords + locations + filters → trigger scrape |
| CoverLetter | `CoverLetter.tsx` | Standalone cover letter from pasted description (stateless, not stored) + chat |
| Schedule | `Schedule.tsx` | Create daily/weekly schedules, view history |
| Profile | `Profile.tsx` | Username display, CV update |
| Signup | `Signup.tsx` | Username + password + CV PDF upload |
| Login | `Login.tsx` | Username + password → stores JWT |

## Dashboard Filtering & Pagination (server-side)
- Filtering, sorting, and paging happen on the SERVER.
- `fetchJobs(filters)` sends filter + `limit`/`offset` and returns `{ items, total, limit, offset }`.
- Page size constant: `PAGE_SIZE = 50` in `Dashboard.tsx`.
- Filters: text search (title/company), seniority dropdown, employment type dropdown, location text, applied status (default "Not Applied"), time period, min relevance score slider.
- Text inputs debounced ~300ms. Any filter change resets to page 0.
- Dropdown options from `GET /api/jobs/filter-options` (distinct values, NOT derived from loaded page).
- Pagination UI: Prev/Next + numbered pages (with ellipses), "Showing X–Y of total".

## Patterns

### Date formatting (relative)
```typescript
if (diff === 0) return "Today";
if (diff === 1) return "Yesterday";
if (diff < 7) return `${diff} days ago`;
if (diff < 30) { const w = Math.floor(diff/7); return `${w} ${w===1 ? "week" : "weeks"} ago`; }
return d.toLocaleDateString();
```

### Auth flow
1. Signup/Login → get token → `localStorage.setItem("token", token)`
2. All API calls → `authFetch` adds Bearer header
3. 401 response → clear token → redirect to /login

### PDF download (with auth)
```typescript
const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
const blob = await res.blob();
const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
a.download = filename; a.click();
```

## Styling
- Plain CSS in `frontend/src/index.css`
- Classes: `.card`, `.btn`, `.btn-green`, `.btn-outline`, `.score`, `.container`, `.job-card`
- No framework — consider Tailwind if it grows complex

## Build
```bash
cd frontend && npm run build  # → frontend/dist/
```

Vite dev server proxies `/api` to `http://localhost:8000` (see `vite.config.ts`).

## Common Pitfalls
1. **Forgetting to rebuild frontend** — backend-only deploy won't pick up UI changes. Always rebuild `frontend/dist/`.
2. **Duplicating refine/chat logic** — use the shared `RefineBox` and `ChatBox` components. Don't inline handlers in pages.
3. **Stale filter options** — dropdown options come from a dedicated endpoint, not client-side derivation from loaded data.
4. **authFetch timeout assumptions** — 401 triggers auto-logout. Don't add separate timeout logic that conflicts.
5. **CopyButton falling back incorrectly** — the fallback uses `execCommand("copy")`. If it silently fails on a platform, the label stays unchanged rather than lying about success.