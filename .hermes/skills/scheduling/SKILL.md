---
name: linkedin-scheduling
description: Use when modifying the scheduled scrape system — APScheduler logic, DB persistence, daily/weekly triggers, or debugging missed runs in linkedin-job-hunter.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, scheduling, apscheduler, cron, automation]
    related_skills: [linkedin-project-overview, linkedin-scraping, linkedin-database]
---

# Scheduling — LinkedIn Job Hunter

## Components
- `app/services/scheduler.py` — APScheduler management
- `app/routers/schedule.py` — CRUD API
- `app/models.py` → `ScheduledScrape` model
- `app/models.py` → `ScrapeRun` model (history)

## How it works
1. User creates schedule → saved to `scheduled_scrapes` table + registered with APScheduler
2. On server startup → `reload_schedules_from_db()` re-registers all saved schedules
3. At scheduled time → APScheduler calls `_run_scrape()` from `app/routers/jobs.py`
4. After completion → logged in `scrape_runs` table

## ScheduledScrape Model
```python
job_id: str (unique)        # "scrape_{username}_{hash}"
user_id: int
username: str
keywords: Text              # JSON array
locations: Text             # JSON array
max_results: int            # default 150
scrape_all: bool
published_at: str           # "", "r86400", "r604800", "r2592000"
hour: int                   # CET timezone
minute: int
frequency: str              # "daily" or "weekly"
day_of_week: str            # "mon"-"sun" (for weekly)
cv_text: Text               # snapshot of user's CV at creation time
```

## Frequency Coupling
- **Daily** → `publishedAt = "r86400"` (last 24h)
- **Weekly** → `publishedAt = "r604800"` (last week)
- Enforced in frontend, not backend

## CronTrigger
```python
if frequency == "weekly":
    trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=minute)
else:
    trigger = CronTrigger(hour=hour, minute=minute)
```

## ScrapeRun (History)
```python
job_id: str          # schedule job_id or "manual"
ran_at: datetime
jobs_added: int
total_scraped: int
status: str          # "success" or "error"
error_message: Text  # if failed
```

## Important Notes
- Schedules are in-memory (APScheduler) + persistent (DB)
- Server restart → all schedules reloaded from DB
- Don't restart during active scrape — kills the background task
- Timezone: server local (Europe/Stockholm, CET)
- cv_text is snapshot — if user updates CV, existing schedules use old CV until recreated

## Common Pitfalls
1. **Restarting during an active scheduled run** — kills the background task mid-scrape. The run is lost (partial data may have been committed).
2. **Stale CV snapshots** — schedules created before a CV update use the old CV. Users must recreate schedules to pick up new CV text.
3. **Timezone assumptions** — schedules use server local time (CET). The frontend should display times accordingly.
4. **Missing `reload_schedules_from_db()` call** — if you modify the startup event in `main.py`, ensure this still runs on boot. Without it, schedules are lost until manually recreated.
5. **Frequency coupling is frontend-only** — the backend accepts any `publishedAt` value regardless of `frequency`. Don't rely on the backend to enforce the coupling.