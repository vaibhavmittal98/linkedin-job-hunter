# Services

## `app/services/scraper.py`

**Purpose:** Fetch LinkedIn jobs via Apify.

**Actor:** `curious_coder/linkedin-jobs-scraper`

**Flow:**
1. Start actor run via `POST /actors/{id}/runs`
2. Poll `GET /actor-runs/{runId}` every 5s until SUCCEEDED/FAILED
3. Abort after 5 min if still running (saves credits)
4. Fetch dataset items from `GET /datasets/{id}/items`

**Key params:**
- `urls` — LinkedIn search URL (includes `f_TPR=r86400` for last 24h)
- `count` — limit results (min 10)
- `scrapeCompany: true` — full company details
- `splitByLocation` / `splitCountry` — bypass 1000 job limit

**Deduplication:** By `linkedin_id` (unique DB constraint).

---

## `app/services/scorer.py`

**Purpose:** Score jobs on screening likelihood (0-100).

**LLM:** OpenRouter API (`https://openrouter.ai/api/v1/chat/completions`)

**Scoring criteria (weighted):**
| Criteria | Weight | Description |
|----------|--------|-------------|
| Skills Match | 30% | Required technical skills |
| Experience Level | 25% | Seniority alignment |
| Tech Stack Overlap | 20% | Tools/languages match |
| Domain Relevance | 10% | Industry fit |
| Disqualifiers | 15% | Hard blockers (language, certs) |

**Disqualifier penalty:** If disqualifiers score < 5, total score is halved.

**Output:** `(score: float, reason: str)` — reason shows per-criteria breakdown.

---

## `app/services/cover_letter.py`

**Purpose:** Generate tailored cover letters.

**Style rules in prompt:**
- Conversational, professional
- No buzzwords, no metrics/numbers from CV
- Don't regurgitate CV bullet points
- Show WHY you'd be effective, not WHAT you did
- Max 3 paragraphs, under 150 words
- Ends with "Best regards, [Name]"

**Refinement:** Users can iteratively edit via chat — feedback is sent back to LLM with current letter + CV.

---

## `app/services/pdf_generator.py`

**Purpose:** Export cover letters as PDF.

Uses `fpdf2`. Layout: name header, contact info, separator, "Application for X at Y", body paragraphs. Handles unicode sanitization.

---

## `app/services/scheduler.py`

**Purpose:** Manage scheduled daily scrapes.

Uses APScheduler `BackgroundScheduler` with `CronTrigger`. Schedules are persisted in `scheduled_scrapes` table and reloaded on server startup via `reload_schedules_from_db()`.
