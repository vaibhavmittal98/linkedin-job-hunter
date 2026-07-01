# Database Schema

SQLite database stored at `./jobs.db`. Auto-created on first server start.

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
