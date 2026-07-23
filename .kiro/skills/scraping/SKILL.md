---
name: scraping
description: LinkedIn job scraping via Apify or Bright Data. Load when working on scraper, changing actor params, debugging scrape issues, or adding new job sources.
---

# Scraping

## Backend switch

The scraper has two interchangeable backends, selected by `SCRAPER_PROVIDER`
in `.env` (`apify` = default, `brightdata`). `scrape_linkedin_jobs(...)` in
`app/services/scraper.py` is a thin dispatcher; both backends return the same
`list[dict]` shape, so `_run_scrape` and the DB are unaffected.

```
SCRAPER_PROVIDER=apify        # default, unchanged behavior
SCRAPER_PROVIDER=brightdata   # use Bright Data instead
```

Switch on EC2 (then restart so settings reload):
```bash
ssh -i ~/.ssh/linkedin-job-hunter.pem ubuntu@<ec2-ip> \
  "cd ~/app && sed -i 's/^SCRAPER_PROVIDER=.*/SCRAPER_PROVIDER=<provider>/' .env && sudo systemctl restart linkedin-job-hunter"
```

> Note: Bright Data calls fail from local WSL because Cloudflare Gateway
> intercepts `api.brightdata.com` with an untrusted CA. Apify is bypassed by
> that policy, so it works locally. Run/test Bright Data from EC2.

---

## Apify backend (`_scrape_apify`)

### Actor: `cheap_scraper~linkedin-job-scraper`

### Input Schema
```python
{
    "keyword": ["Software Engineer"],     # Required: array of keywords
    "locations": ["Stockholm"],           # Optional: array of locations
    "publishedAt": "r86400",             # Optional: "r86400" (24h), "r604800" (week), "r2592000" (month)
    "maxItems": 150,                      # Optional: set to max_results (no floor)
    "saveOnlyUniqueItems": True,          # Dedup within the run
    "enrichCompanyData": False,           # Skip extra company page requests
    "jobType": ["full-time"],            # Optional filter
    "experienceLevel": ["mid-senior"],   # Optional filter
    "workType": ["remote", "hybrid"],    # Optional filter
}
```

### Output Fields → DB Mapping
| Actor field | DB column |
|---|---|
| `jobId` | `linkedin_id` |
| `jobTitle` | `title` |
| `companyName` | `company` |
| `companyLogo` | `company_logo` |
| `companyUrl` | `company_url` |
| `location` | `location` |
| `jobUrl` | `url` |
| `applyUrl` | `apply_url` |
| `jobDescription` | `description` |
| `salaryInfo` (array) | `salary` (joined string) |
| `publishedAt` | `posted_at` |
| `experienceLevel` | `seniority_level` |
| `contractType` | `employment_type` |
| `workType` | `job_function` |
| `sector` | `industries` |
| `applicationsCount` | `applicants_count` |
| `posterFullName` | `job_poster_name` |
| `posterProfileUrl` | `job_poster_profile_url` |

### Flow (in `app/services/scraper.py`)
1. POST to `https://api.apify.com/v2/actors/cheap_scraper~linkedin-job-scraper/runs`
2. Poll `GET /actor-runs/{run_id}` every 10s until SUCCEEDED/FAILED
3. Fetch `GET /datasets/{dataset_id}/items`
4. Map fields and return list of dicts

### Background Task (`_run_scrape` in `app/routers/jobs.py`)
- Deduplicates by `linkedin_id` + `user_id`
- Scores each job if `cv_text` available (serial, one LLM call per job)
- Logs run in `scrape_runs` table
- **Single commit at the very end** — all jobs are staged with `db.add()` and
  committed once after the loop (NOT per-batch). New jobs therefore only appear
  on the dashboard once the whole run + scoring finishes.
- Previously scraped jobs stay visible during a run thanks to SQLite WAL mode
  (see database skill). Before WAL, the long-held write transaction caused
  "database is locked" read failures and the dashboard showed 0 jobs mid-scrape.

### Limitations
- Public scraper: ~300-500 results per search (LinkedIn pagination cap)
- `maxItems`: request any number — the code no longer clamps it up to 150
- No login cookies needed (public LinkedIn)

### Available Actor Filters (not yet exposed in UI)
- `filterUnder10Applicants: true`
- `filterEasyApply: true`
- `companyInclude` / `companyExclude`
- `jobTitleExclude`
- `subLocationExclude`
- `salaryBase` (minimum salary)
- `resumeKeywords` (built-in keyword matching with match %)

---

## Bright Data backend (`_scrape_brightdata`)

### Dataset: `gd_lpfll7v5hcqtkxl6l` (LinkedIn jobs)

Env: `BRIGHTDATA_API_TOKEN`, `BRIGHTDATA_DATASET_ID` (default set),
`BRIGHTDATA_COUNTRY` (default `SE`, LinkedIn geo hint).
Falls back to demo data if the token is missing/placeholder.

### Flow (Dataset API v3)
1. `POST /datasets/v3/trigger?dataset_id=...&type=discover_new&discover_by=keyword`
   with header `Authorization: Bearer <token>` and a JSON array of input rows
   (one per keyword × location). Optional `limit_per_input` (unless `scrape_all`).
2. Poll `GET /datasets/v3/progress/{snapshot_id}` every 10s until `status == "ready"`
   (`failed`/`error`/`canceled` → return []).
3. `GET /datasets/v3/snapshot/{snapshot_id}?format=json`.

> The `/scrape` endpoint is not reliably synchronous — it times out its wait
> and hands back a `snapshot_id`. So we use trigger → poll → snapshot.

### Input row fields
`location`, `keyword`, `country` (`BRIGHTDATA_COUNTRY`), `time_range`
(`"Past 24 hours"`|`"Past week"`|`"Past month"`, mapped from `publishedAt`),
plus empty `job_type`/`experience_level`/`remote`/`company`/`location_radius`.

### Output Fields → DB Mapping
| Bright Data field | DB column | Notes |
|---|---|---|
| `job_posting_id` | `linkedin_id` | cast `str()` |
| `job_title` | `title` | |
| `company_name` | `company` | |
| `company_logo` | `company_logo` | |
| `company_url` | `company_url` | |
| `job_location` | `location` | |
| `url` | `url` | |
| `apply_link` | `apply_url` | often `null` → `""` |
| `job_summary` | `description` | |
| `job_description_formatted` | `description_html` | |
| `job_posted_date` | `posted_at` | ISO datetime |
| `job_seniority_level` | `seniority_level` | |
| `job_employment_type` | `employment_type` | |
| `job_function` | `job_function` | |
| `job_industries` | `industries` | |
| `job_num_applicants` | `applicants_count` | int → `str()`, `is not None` guard keeps `0` |

Skipped (blank/None): `salary`, `company_website`, `company_description`,
`company_address`, `company_employees_count`, `benefits`, `job_poster_name`,
`job_poster_profile_url`. `job_poster` and `base_salary` come back as `null`.
