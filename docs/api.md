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

### `GET /api/jobs?min_score=0`
List all jobs sorted by relevance score descending.

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
