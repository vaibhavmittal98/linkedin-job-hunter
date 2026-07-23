# Frontend

React + TypeScript + Vite SPA with JWT authentication.

## Structure

```
frontend/src/
├── main.tsx            # Entry point
├── App.tsx             # Routes + protected route wrapper
├── api.ts              # Typed API client with auth headers
├── index.css           # Global styles
├── components/
│   ├── RefineBox.tsx   # Shared cover-letter refine input + button
│   ├── ChatBox.tsx     # Shared stateless Q&A chat widget (job + CV context)
│   └── CopyButton.tsx  # Shared copy-to-clipboard button (cover letters + chat replies)
└── pages/
    ├── Dashboard.tsx   # Paginated job list, server-side filters, search
    ├── JobDetail.tsx   # Job view, score, cover letter, refine, PDF, ask-about-job chat
    ├── Scrape.tsx      # Manual scrape with options
    ├── CoverLetter.tsx # Standalone cover letter from a pasted job description + ask-about-job chat
    ├── Schedule.tsx    # Scheduled scrapes + run history
    ├── Profile.tsx     # Username display + CV update
    ├── Signup.tsx      # Account creation with CV upload
    └── Login.tsx       # Authentication
```

## Routes

| Path | Page | Auth required |
|------|------|:---:|
| `/` | Dashboard | ✓ |
| `/jobs/:id` | JobDetail | ✓ |
| `/scrape` | Scrape | ✓ |
| `/cover-letter` | CoverLetter | ✓ |
| `/schedule` | Schedule | ✓ |
| `/profile` | Profile | ✓ |
| `/signup` | Signup | ✗ |
| `/login` | Login | ✗ |

## Dashboard pagination

Filtering, sorting, and paging are server-side (50 jobs/page). `fetchJobs`
returns `{ items, total, limit, offset }`; dropdown options come from
`/api/jobs/filter-options`. UI has Prev/Next + numbered pages.

## Auth Flow

- Token stored in `localStorage`
- `authHeaders()` adds `Authorization: Bearer <token>` to all API calls
- `ProtectedRoute` component redirects to `/login` if no token
- Logout clears token and redirects

## Development

```bash
cd frontend
npm run dev      # Dev server :5173 (proxies /api to :8000)
npm run build    # Production build
```
