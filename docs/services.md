# Services

## `app/services/scraper.py`

**Purpose:** Fetch LinkedIn jobs via Apify.

**Actor:** `cheap_scraper~linkedin-job-scraper`

**Flow:**
1. Start actor run via `POST /actors/{id}/runs`
2. Poll `GET /actor-runs/{runId}` every 10s until SUCCEEDED (FAILED/ABORTED/TIMED-OUT → return [])
3. Fetch dataset items from `GET /datasets/{id}/items`
4. If no valid `APIFY_API_TOKEN` is set, returns demo data instead of calling Apify.

**Key run_input params:**
- `keyword` — array of search keywords
- `locations` — array of locations
- `saveOnlyUniqueItems: true` — dedupe within the run
- `enrichCompanyData: false` — skip extra company page requests
- `maxItems` — set to `max(max_results, 150)` unless `scrape_all` is true
- `publishedAt` — time window (`r86400` 24h, `r604800` week, `r2592000` month)

**Deduplication:** By `linkedin_id` + `user_id` in `_run_scrape` (see routers/jobs.py).

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
| Disqualifiers | 15% | Hard blockers (spoken language, certs, clearance) |

**Disqualifier gate:** `<= 2` (hard blocker, e.g. a required spoken language the CV lacks) caps total at 15; `3-4` (soft concern) halves total. Programming languages are judged under Tech Stack, not Disqualifiers.

**Extended thinking:** `_call_llm(prompt, reasoning_effort="")` — scoring passes `settings.llm_reasoning_effort` (`LLM_REASONING_EFFORT` env, `high` in prod). Opt-in, so cover-letter refine (also uses `_call_llm`) is unaffected.

**Output:** `(score: float, reason: str)` — reason shows per-criteria breakdown.

---

## `app/services/chat.py`

**Purpose:** Stateless Q&A chat about a job + the candidate's CV. Nothing persisted.

- `chat_about_job(history, cv_text, title, company, description)` builds a system prompt from the CV + optional job context (CV-only when no description), then calls `_call_llm_messages()` with the full system + conversation array.
- `_call_llm_messages()` is separate from `scorer._call_llm` so scoring/cover-letter flows are untouched.
- Backs `POST /api/jobs/{id}/chat` (job context from DB) and `POST /api/chat` (CV + optional pasted description).

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

**Standalone (ad-hoc):** `refine_cover_letter_adhoc()` supports the stateless
cover-letter flow (pasted job description, nothing stored). Generation reuses
`generate_cover_letter()`.

---

## `app/services/pdf_generator.py`

**Purpose:** Export cover letters as PDF.

Uses `fpdf2`. Layout: name header, contact info, separator, "Application for X at Y", body paragraphs. Handles unicode sanitization.

`generate_pdf_adhoc()` is the standalone variant: same layout, but the
"Application for X at Y" line is rendered only when both title and company are
supplied. Kept separate so the job-based `generate_pdf()` is unaffected.

---

## `app/services/scheduler.py`

**Purpose:** Manage scheduled daily scrapes.

Uses APScheduler `BackgroundScheduler` with `CronTrigger`. Schedules are persisted in `scheduled_scrapes` table and reloaded on server startup via `reload_schedules_from_db()`.
