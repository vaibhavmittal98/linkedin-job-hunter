# Frontend

React + TypeScript + Vite SPA with JWT authentication.

## Structure

```
frontend/src/
├── main.tsx            # Entry point
├── App.tsx             # Routes + protected route wrapper
├── api.ts              # Typed API client with auth headers
├── index.css           # Global styles
└── pages/
    ├── Dashboard.tsx   # Job list, filters, search
    ├── JobDetail.tsx   # Job view, score, cover letter, refine, PDF
    ├── Scrape.tsx      # Manual scrape with options
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
| `/schedule` | Schedule | ✓ |
| `/profile` | Profile | ✓ |
| `/signup` | Signup | ✗ |
| `/login` | Login | ✗ |

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
