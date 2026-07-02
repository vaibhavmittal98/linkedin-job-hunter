# API Reference

Base URL: `http://localhost:8000/api`

All endpoints except `/auth/signup` and `/auth/login` require `Authorization: Bearer <token>` header.

---

## Auth

### `POST /api/auth/signup`
Create account. Multipart form: `username`, `password`, `cv` (PDF file).

**Response:** `{"access_token": "...", "token_type": "bearer"}`

### `POST /api/auth/login`
Login. Form data: `username`, `password`.

**Response:** `{"access_token": "...", "token_type": "bearer"}`

### `GET /api/auth/me`
Get current user info.

**Response:** `{"username": "...", "has_cv": true}`

### `POST /api/auth/update-cv`
Upload new CV (PDF). Re-scores all non-applied jobs in background.

**Response:** `{"status": "ok", "message": "CV updated. Re-scoring jobs in background."}`

---

## Jobs

### `GET /api/jobs`
List jobs for the current user with server-side filtering and pagination,
sorted by relevance score descending.

**Query params (all optional):**
- `min_score` (float, default 0)
- `search` (matches title or company, case-insensitive)
- `seniority`, `employment_type` (exact match)
- `location` (case-insensitive substring)
- `applied` — `""` | `"applied"` | `"not_applied"`
- `time_period` — `""` | `"day"` | `"week"` | `"month"` (filters on `posted_at`)
- `limit` (default 50, capped at 200), `offset` (default 0)

**Response:** `{"items": [Job, ...], "total": 3121, "limit": 50, "offset": 0}`

### `GET /api/jobs/filter-options`
Distinct filter values for the current user's jobs (used by dashboard dropdowns).

**Response:** `{"seniority_levels": ["Entry level", ...], "employment_types": ["Full-time", ...]}`

### `GET /api/jobs/{id}`
Get single job with all fields.

### `POST /api/jobs/{id}/score`
Generate relevance score for a job using LLM.

**Response:** `{"score": 72.5, "reason": "Skills: 8/10 | Experience: 7/10 | ..."}`

### `POST /api/jobs/{id}/apply`
Mark job as applied.

### `POST /api/jobs/{id}/unapply`
Mark job as not applied.

---

## Scraping

### `POST /api/scrape`
Start a background scrape.

**Body:**
```json
{
  "keywords": ["Software Engineer"],
  "locations": ["Netherlands"],
  "max_results": 10,
  "scrape_all": false,
  "published_at": ""
}
```

`keywords` and `locations` are arrays. `published_at` sets the time window:
`""` (any), `"r86400"` (last 24h), `"r604800"` (last week), `"r2592000"` (last month).

**Response:** `{"status": "started", "message": "Scraping started. Jobs will appear on the dashboard soon."}`

---

## Cover Letters

### `POST /api/jobs/{id}/cover-letter`
Generate cover letter (or return existing).

### `GET /api/jobs/{id}/cover-letter`
Get existing cover letter.

### `POST /api/jobs/{id}/cover-letter/refine`
Refine cover letter with feedback.

**Body:** `{"message": "make it shorter"}`

**Response:** `{"content": "..."}`

### `GET /api/jobs/{id}/cover-letter/pdf`
Download cover letter as PDF.

---

## Standalone Cover Letters (ad-hoc, not stored)

Generate a cover letter from a pasted job description for a job that is not in
the database. Stateless — nothing is persisted.

### `POST /api/cover-letter/adhoc`
**Body:** `{"description": "...", "title": "optional", "company": "optional"}`

**Response:** `{"content": "..."}`

### `POST /api/cover-letter/adhoc/refine`
**Body:** `{"content": "...", "message": "make it shorter", "title": "optional", "company": "optional"}`

**Response:** `{"content": "..."}`

### `POST /api/cover-letter/adhoc/pdf`
**Body:** `{"content": "...", "title": "optional", "company": "optional"}`

Returns PDF bytes. The "Application for X at Y" line is included only when both
`title` and `company` are provided.

---

## Schedules

### `POST /api/schedules`
Create a daily or weekly scrape schedule.

**Body:**
```json
{
  "keywords": ["Backend Engineer"],
  "locations": ["Stockholm"],
  "max_results": 10,
  "scrape_all": false,
  "published_at": "",
  "hour": 2,
  "minute": 0,
  "frequency": "daily",
  "day_of_week": "mon"
}
```

`frequency` is `"daily"` or `"weekly"`. `day_of_week` (`mon`-`sun`) applies only when weekly.

### `GET /api/schedules`
List user's schedules.

### `DELETE /api/schedules/{job_id}`
Delete a schedule.

### `GET /api/schedules/{job_id}/history`
Get run history (last 20 runs) with jobs_added, total_scraped, status.
