# Architecture Overview

## System Design

```
┌─────────────────────────────────────────────────────────────────────┐
│                        React Frontend                                │
│  (Dashboard, JobDetail, Scrape, CoverLetter, Schedule, Profile, Login, Signup) │
│  http://localhost:5173                                               │
└────────────────────────┬────────────────────────────────────────────┘
                         │ HTTP (proxied via Vite, JWT auth)
                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                                  │
│  http://localhost:8000                                               │
├─────────────────────────────────────────────────────────────────────┤
│  Routers              │  Services                │  Data Layer        │
│  ──────────           │  ────────                │  ──────────        │
│  /api/jobs            │  scraper.py (Apify)      │  SQLAlchemy ORM    │
│  (paginated+filtered) │  scorer.py (OpenRouter)  │  SQLite (jobs.db)  │
│  /api/scrape          │  cover_letter.py         │                    │
│  /api/cover-letter    │  pdf_generator.py        │                    │
│    /adhoc             │  scheduler.py (APSched)  │                    │
│  /api/auth            │                          │                    │
│  /api/schedules       │                          │                    │
└─────────────────────────────────────────────────────────────────────┘
                         │                │
                         ▼                ▼
                  ┌────────────┐   ┌─────────────┐
                  │   Apify    │   │ OpenRouter   │
                  │  (scraping)│   │  (LLM API)  │
                  └────────────┘   └─────────────┘
```

## Request Flow

1. User triggers action in React UI
2. Frontend sends request with JWT Bearer token
3. FastAPI validates token, resolves user
4. Router delegates to service with user's CV text
5. Service calls external APIs (Apify, OpenRouter) or DB
6. Response returns; background tasks continue independently

## Background Tasks

- **Scraping** — runs in FastAPI `BackgroundTasks`, doesn't block the response
- **Scheduled scrapes** — APScheduler fires cron jobs, calls the same scrape function
- **Re-scoring** — opt-in on CV update (`rescore=true` on `/api/auth/update-cv`), scores all non-applied jobs in background

## Design Principles

- **CV-centric** — all scoring and cover letters use the user's uploaded CV directly (no manual profile fields)
- **Deduplication** — jobs are deduped by `linkedin_id` per user (in `_run_scrape`, not a DB-level unique constraint)
- **Background-first** — scraping never blocks the UI; results appear asynchronously
- **Persistent schedules** — stored in DB, reloaded on server restart
- **Cost-aware** — scrape time window is configurable per request/schedule via `published_at` (any / last 24h `r86400` / week `r604800` / month `r2592000`); scoring is per-job on demand or during scrape

## Extension Points

- **New job sources** — add scraper functions in `app/services/`
- **Different LLM** — change `LLM_MODEL` in `.env` (any OpenRouter model)
- **Notifications** — hook into `_run_scrape` to send alerts on new high-scoring jobs
