---
name: frontend
description: React frontend patterns, routing, auth flow, and component structure. Load when modifying UI, adding pages, or debugging frontend issues.
---

# Frontend

## Tech: React 18 + TypeScript + Vite

## Key Files

### `api.ts` — Central API client
- `authFetch()` — wraps fetch with auth headers + auto-logout on 401
- All API functions use `authFetch`
- Token stored in `localStorage.getItem("token")`

### `App.tsx` — Routing
- `ProtectedRoute` — redirects to `/login` if no token
- Routes: `/`, `/jobs/:id`, `/scrape`, `/cover-letter`, `/schedule`, `/profile`, `/signup`, `/login`

### `components/RefineBox.tsx` — Shared refine input + button
- Used by BOTH JobDetail and CoverLetter so refine behavior is defined once.
- Props: `refineFn(message) => Promise<{content}>` and `onRefined(content)`.
- Owns its own `message`/`refining` state; resets the button in a `finally`
  block so it never gets stuck on "Refining..." if a request fails.
- When changing refine UX, edit this component — do NOT reintroduce inline handlers.

### `components/CopyButton.tsx` — Shared copy-to-clipboard button
- Used by the cover letter views (JobDetail + CoverLetter) and by each assistant
  reply in `ChatBox`.
- Prop: `text` (string to copy), optional `style`. Shows a brief "Copied!"
  confirmation, then reverts after 2s.
- Falls back to a hidden `<textarea>` + `execCommand("copy")` when the async
  Clipboard API is unavailable (e.g. non-HTTPS contexts). On failure it leaves
  the label unchanged rather than misreporting success.

### `components/ChatBox.tsx` — Shared Q&A chat widget
- Used by BOTH JobDetail and CoverLetter for a stateless Q&A chat about the job + CV.
- Prop: `sendFn(messages) => Promise<{reply}>` (caller decides context). Optional `placeholder`.
- Owns the conversation history + input + `sending` state in component state only —
  **nothing is persisted**. Has a **Reset** button to clear the conversation (useful
  after the underlying context, e.g. a pasted job description, changes).
- JobDetail wires it to `jobChat(jobId, messages)` (context = that job's description).
- CoverLetter wires it to `chat(messages, description, title, company)` (context =
  whatever's in the description box; CV-only when empty). The card is always shown,
  regardless of whether a cover letter has been generated.
- Each assistant reply has a `CopyButton` to copy that reply's text.

## Pages

| Page | File | Purpose |
|------|------|---------|
| Dashboard | `Dashboard.tsx` | Paginated job list, server-side filters, opens in new tab |
| JobDetail | `JobDetail.tsx` | Full job view, score, cover letter, refine, PDF, delete, apply, ask-about-job chat |
| Scrape | `Scrape.tsx` | Keywords + locations + filters → trigger scrape |
| CoverLetter | `CoverLetter.tsx` | Standalone cover letter from a pasted job description (stateless, not stored) + ask-about-job chat |
| Schedule | `Schedule.tsx` | Create daily/weekly schedules, view history |
| Profile | `Profile.tsx` | Username display, CV update |
| Signup | `Signup.tsx` | Username + password + CV PDF upload |
| Login | `Login.tsx` | Username + password → stores JWT |

## Dashboard filtering & pagination (server-side)
- Filtering, sorting, and paging happen on the SERVER, not in the browser.
  `fetchJobs(filters)` sends the filter + `limit`/`offset` params and returns
  `{ items, total, limit, offset }`. Only one page (50 jobs) is transferred.
- Filters: text search (title/company), seniority dropdown, employment type
  dropdown, location text, applied status (default "Not Applied"), time period,
  min relevance score slider.
- Text inputs (search, location) are debounced ~300ms. Any filter change resets
  to page 0.
- Dropdown options come from `GET /api/jobs/filter-options` (distinct values),
  NOT derived from the loaded page.
- Pagination UI: Prev/Next + numbered pages (with ellipses), "Showing X–Y of total".
- Page size constant: `PAGE_SIZE = 50` in `Dashboard.tsx`.

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
- Plain CSS in `index.css`
- Classes: `.card`, `.btn`, `.btn-green`, `.btn-outline`, `.score`, `.container`, `.job-card`
- No framework — consider Tailwind if it grows complex

## Build
```bash
cd frontend && npm run build  # → frontend/dist/
```

Vite dev server proxies `/api` to `http://localhost:8000` (see `vite.config.ts`).
