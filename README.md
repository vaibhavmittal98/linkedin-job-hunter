# Job Application Automator

Automates the job hunting pipeline: scrapes LinkedIn jobs via Apify, scores them on screening likelihood using an LLM, and generates tailored cover letters.

## Features

- **LinkedIn job scraping** — Pulls listings via Apify (`curious_coder/linkedin-jobs-scraper`), only jobs from the last 24h
- **Relevance scoring** — LLM-powered multi-criteria scoring (skills match, experience level, tech stack, domain, disqualifiers) against your CV
- **Cover letter generation** — Conversational, human-sounding letters with iterative refinement chat + PDF export
- **Scheduled scrapes** — Daily automated scrapes with persistent schedules and run history
- **Dashboard** — Search, filter (seniority, type, location, applied status), sorted by score
- **Authentication** — Signup with CV upload, JWT-based auth
- **Application tracking** — Mark jobs as applied/not applied

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI, SQLAlchemy |
| Frontend | React, TypeScript, Vite |
| Database | SQLite |
| Scraping | Apify (`curious_coder/linkedin-jobs-scraper`) |
| LLM | OpenRouter (deepseek-v4-flash default) |
| Scheduling | APScheduler |
| Auth | JWT (python-jose) + bcrypt |

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Apify](https://apify.com/) account with API token
- [OpenRouter](https://openrouter.ai/) account with API key

### One-command setup

```bash
./setup.sh
```

Creates venv, installs Python + Node dependencies, copies `.env.example` to `.env`.

### Configure

Edit `.env`:
```
DATABASE_URL=sqlite:///./jobs.db
APIFY_API_TOKEN=your_apify_token
LLM_API_KEY=sk-or-v1-your-openrouter-key
LLM_MODEL=deepseek/deepseek-v4-flash
SECRET_KEY=your-random-secret-key
```

### Run

```bash
./run.sh
```

Starts backend (http://localhost:8000) and frontend (http://localhost:5173). Ctrl+C stops both.

## Usage

1. **Sign up** — `/signup` with username, password, and CV (PDF)
2. **Scrape jobs** — `/scrape` — keywords, location, options
3. **Browse & filter** — `/` — jobs sorted by relevance score
4. **Score jobs** — click "Generate Score" on any job
5. **Generate cover letters** — one-click generation with refinement chat
6. **Download PDF** — export cover letters as PDF
7. **Schedule** — `/schedule` — set up daily automated scrapes
8. **Track applications** — mark jobs as applied

## Project Structure

```
app/
├── main.py                 # FastAPI app, startup, router registration
├── models.py               # SQLAlchemy models
├── schemas.py              # Pydantic request/response schemas
├── config.py               # Environment settings
├── db.py                   # Database connection
├── auth.py                 # JWT auth utilities
├── routers/
│   ├── jobs.py             # Job CRUD, scrape, score, cover letter endpoints
│   ├── auth.py             # Signup, login, profile, CV update
│   └── schedule.py         # Schedule CRUD + history
└── services/
    ├── scraper.py          # Apify integration (async run/poll/abort)
    ├── scorer.py           # Multi-criteria LLM scoring via OpenRouter
    ├── cover_letter.py     # LLM cover letter generation
    ├── pdf_generator.py    # Cover letter PDF export
    └── scheduler.py        # APScheduler management + DB persistence
frontend/src/
├── api.ts                  # Typed API client with auth headers
├── App.tsx                 # Router + protected routes
└── pages/
    ├── Dashboard.tsx       # Job list with filters
    ├── JobDetail.tsx       # Job view + score + cover letter + refine
    ├── Scrape.tsx          # Manual scrape trigger
    ├── Schedule.tsx        # Scheduled scrapes + history
    ├── Profile.tsx         # Username + CV update
    ├── Signup.tsx          # Account creation
    └── Login.tsx           # Authentication
```

## License

MIT
