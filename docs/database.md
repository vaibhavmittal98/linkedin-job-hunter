# Database Schema

SQLite database stored at `./jobs.db`. Auto-created on first server start.

## Engine configuration

Configured in `app/db.py`. A SQLAlchemy `connect` event listener runs these
PRAGMAs on every connection:

- `journal_mode=WAL` — readers and the single writer run concurrently. Without
  WAL, a large scrape holds one long write transaction (autoflush opens it
  early; it stays open through all serial per-job scoring until the single final
  commit), which made concurrent dashboard reads fail with "database is locked"
  and show 0 jobs until the scrape finished.
- `busy_timeout=30000` — a writer waits up to 30s for a lock instead of erroring
  immediately.
- `synchronous=NORMAL` — safe default under WAL.

WAL creates `jobs.db-wal` / `jobs.db-shm` sidecar files next to the DB. The
nightly `sqlite3 .backup` job is WAL-safe.

## Tables

### `jobs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | INTEGER FK | Owner (references `user_profile.id`) |
| `linkedin_id` | VARCHAR | LinkedIn job ID, used for deduplication |
| `title` | VARCHAR | Job title |
| `company` | VARCHAR | Company name |
| `company_logo` | VARCHAR | Logo URL |
| `company_url` | VARCHAR | Company LinkedIn page |
| `company_website` | VARCHAR | Company website |
| `company_description` | TEXT | About the company |
| `company_address` | TEXT | JSON address object |
| `company_employees_count` | INTEGER | Company size |
| `location` | VARCHAR | Job location |
| `url` | VARCHAR (unique) | Full LinkedIn job URL |
| `apply_url` | VARCHAR | Direct application URL |
| `description` | TEXT | Plain text description |
| `description_html` | TEXT | HTML description |
| `salary` | VARCHAR | Salary (often empty) |
| `posted_at` | VARCHAR | Post date |
| `seniority_level` | VARCHAR | e.g. "Mid-Senior level" |
| `employment_type` | VARCHAR | e.g. "Full-time" |
| `job_function` | VARCHAR | e.g. "Information Technology" |
| `industries` | VARCHAR | e.g. "Information Services" |
| `applicants_count` | VARCHAR | Number of applicants |
| `benefits` | TEXT | JSON array |
| `job_poster_name` | VARCHAR | Recruiter name |
| `job_poster_profile_url` | VARCHAR | Recruiter LinkedIn |
| `relevance_score` | FLOAT | 0-100 weighted score |
| `score_reason` | TEXT | Breakdown of scoring criteria |
| `applied` | BOOLEAN | Application status |
| `scraped_at` | DATETIME | When we scraped it |

### `cover_letters`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `job_id` | INTEGER FK (unique) | One letter per job |
| `content` | TEXT | Cover letter text |
| `created_at` | DATETIME | Generation timestamp |

### `user_profile`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `username` | VARCHAR (unique) | Login username |
| `password_hash` | VARCHAR | bcrypt hash |
| `cv_text` | TEXT | Extracted CV text for LLM |
| `name`, `title`, `summary`, `skills`, `experience`, `preferences` | Various | Legacy fields (unused) |

### `scheduled_scrapes`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `job_id` | VARCHAR (unique) | Schedule identifier |
| `user_id` | INTEGER | Owner user id |
| `username` | VARCHAR | Owner username |
| `keywords` | TEXT | JSON array of search keywords |
| `locations` | TEXT | JSON array of locations (default `"[]"`) |
| `max_results` | INTEGER | Job count limit (default 150) |
| `scrape_all` | BOOLEAN | Ignore count limit |
| `published_at` | VARCHAR | Time window: `""`, `r86400` (24h), `r604800` (week), `r2592000` (month) |
| `hour` | INTEGER | Run hour (CET) |
| `minute` | INTEGER | Run minute |
| `frequency` | VARCHAR | `"daily"` or `"weekly"` |
| `day_of_week` | VARCHAR | `mon`-`sun` (used when weekly) |
| `cv_text` | TEXT | CV snapshot for scoring |

### `scrape_runs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `job_id` | VARCHAR | Schedule job_id or "manual" |
| `ran_at` | DATETIME | Execution timestamp |
| `jobs_added` | INTEGER | New jobs stored |
| `total_scraped` | INTEGER | Total from Apify |
| `status` | VARCHAR | "success" or "error" |
| `error_message` | TEXT | Error details if failed |

## Backups

The production database (`~/app/jobs.db` on the EC2 box) is backed up nightly to S3.

### Mechanism
- **Script:** `/usr/local/bin/backup-jobs-db.sh` (owned by root).
- **Schedule:** root cron, daily at **07:00** (server TZ is `Europe/Berlin`, so this stays correct across DST). Logs to `/var/log/jobs-db-backup.log`.
- **Method:** `sqlite3 jobs.db ".backup ..."` — a safe online backup that won't corrupt a DB that is being written to.
- **Local copies:** newest **7** kept in `/home/ubuntu/backups/`; older ones pruned on each run.
- **S3:** uploaded to `s3://linkedin-job-hunter-backups-810299942836/jobs.db/jobs-<timestamp>.db` (region `eu-north-1`).

### Retention
Rolling **7-day** window on both sides (not a weekly wipe):
- Local: script keeps the newest 7 files.
- S3: bucket lifecycle rule `expire-backups-7-days` expires each object 7 days after it was created (lifecycle runs on a daily batch, so an object may linger up to ~24h past the 7-day mark).

To change the window, update `KEEP` in the script **and** the S3 lifecycle rule.

### Bucket hardening
- Block Public Access: all four settings ON.
- Default encryption: SSE-S3 (AES256).

### Access model
- The EC2 instance uses IAM **instance role** `linkedin-job-hunter-backup` (no long-lived keys on the box).
- Its policy is scoped to only `s3:PutObject` on `.../jobs.db/*`. It intentionally **cannot** list, read, or delete objects — so a compromised box can't exfiltrate or wipe existing backups. (This is why `aws s3 ls`/`cp`-down from the box is denied; use admin credentials for those.)

### Restore
Backups are NOT auto-restored. To restore manually (uses admin creds, not the instance role):
```bash
# stop the app so the DB isn't being written during the swap
sudo systemctl stop linkedin-job-hunter
aws s3 cp s3://linkedin-job-hunter-backups-810299942836/jobs.db/jobs-<timestamp>.db \
  /home/ubuntu/app/jobs.db --region eu-north-1
sudo systemctl start linkedin-job-hunter
```

> Note: this is a **recovery** guardrail, not a deletion lock. Because the app must write to `jobs.db`, the live file cannot be made truly immutable — but nightly off-box copies mean at most ~1 day of data is at risk. **Never delete `jobs.db` without explicit permission.**
