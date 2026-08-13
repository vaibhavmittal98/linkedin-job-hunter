---
name: database
description: SQLite database schema, models, and migration patterns. Load when modifying schema, adding columns, or debugging data issues.
---

# Database

## Engine: SQLite (`./jobs.db`)
- Connection: `check_same_thread=False`
- ORM: SQLAlchemy 2.0
- Tables auto-created via `Base.metadata.create_all()` on startup
- **WAL mode enabled** via a `connect` event listener in `app/db.py` that runs
  `PRAGMA journal_mode=WAL`, `PRAGMA busy_timeout=30000`,
  `PRAGMA synchronous=NORMAL` on every connection.
  - Why: a large scrape holds one long write transaction (autoflush opens it
    early; it stays open through all serial per-job scoring until the single
    final commit). In the default rollback-journal mode this made concurrent
    dashboard reads fail with "database is locked", so the dashboard showed 0
    jobs until the scrape finished. WAL lets readers and the single writer run
    concurrently; `busy_timeout` makes writers wait instead of erroring.
  - Side effect: creates `jobs.db-wal` / `jobs.db-shm` sidecar files next to the
    DB. The nightly `sqlite3 .backup` job is WAL-safe.

## Tables

### `jobs`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | INTEGER FK | Links to user_profile.id |
| linkedin_id | VARCHAR | Dedup key (per user) |
| title | VARCHAR | |
| company | VARCHAR | |
| company_logo | VARCHAR | |
| company_url | VARCHAR | |
| company_website | VARCHAR | |
| company_description | TEXT | |
| company_address | TEXT | |
| company_employees_count | INTEGER | |
| location | VARCHAR | |
| url | VARCHAR | Full LinkedIn job URL |
| apply_url | VARCHAR | |
| description | TEXT | Plain text |
| description_html | TEXT | |
| salary | VARCHAR | |
| posted_at | VARCHAR | ISO date or "2 days ago" |
| seniority_level | VARCHAR | |
| employment_type | VARCHAR | |
| job_function | VARCHAR | |
| industries | VARCHAR | |
| applicants_count | VARCHAR | |
| benefits | TEXT | |
| job_poster_name | VARCHAR | |
| job_poster_profile_url | VARCHAR | |
| relevance_score | FLOAT | 0-100 |
| score_reason | TEXT | Breakdown string |
| applied | BOOLEAN | Default False |
| ind_sponsor | BOOLEAN | IND recognised-sponsor match; NULL = not evaluated |
| scraped_at | DATETIME | |

### `cover_letters`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| job_id | INTEGER FK (unique) | One per job |
| content | TEXT | |
| created_at | DATETIME | |

### `user_profile`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| username | VARCHAR (unique) | |
| password_hash | VARCHAR | bcrypt |
| cv_text | TEXT | Extracted from PDF |
| name, title, summary, skills, experience, preferences | Various | Legacy, mostly unused |

### `scheduled_scrapes`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| job_id | VARCHAR (unique) | Schedule identifier |
| user_id | INTEGER | |
| username | VARCHAR | |
| keywords | TEXT | JSON array |
| locations | TEXT | JSON array |
| max_results | INTEGER | |
| scrape_all | BOOLEAN | |
| published_at | VARCHAR | |
| hour | INTEGER | |
| minute | INTEGER | |
| frequency | VARCHAR | "daily" or "weekly" |
| day_of_week | VARCHAR | |
| cv_text | TEXT | Snapshot |

### `scrape_runs`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| job_id | VARCHAR | schedule ID or "manual" |
| ran_at | DATETIME | |
| jobs_added | INTEGER | |
| total_scraped | INTEGER | |
| status | VARCHAR | "success"/"error" |
| error_message | TEXT | |

## Schema Changes

**NEVER drop the database without explicit permission.**

Use ALTER TABLE for additive changes:
```python
from sqlalchemy import text
from app.db import engine
with engine.connect() as conn:
    conn.execute(text('ALTER TABLE jobs ADD COLUMN new_col TYPE'))
    conn.commit()
```

SQLite limitations:
- Cannot DROP columns
- Cannot RENAME columns
- Cannot change column types
- Use new table + copy for destructive changes (last resort)
