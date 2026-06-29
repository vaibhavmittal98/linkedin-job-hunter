# Database Schema

SQLite database stored at `./jobs.db`. Auto-created on first server start.

## Tables

### `jobs`

| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `linkedin_id` | VARCHAR (unique) | LinkedIn job ID, used for deduplication |
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
| `username` | VARCHAR | Owner |
| `keywords` | VARCHAR | Search keywords |
| `location` | VARCHAR | Search location |
| `max_results` | INTEGER | Job count limit |
| `scrape_all` | BOOLEAN | Ignore count limit |
| `split_by_location` | BOOLEAN | Split by cities |
| `split_country` | VARCHAR | Country code for split |
| `hour` | INTEGER | Run hour (CET) |
| `minute` | INTEGER | Run minute |
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
