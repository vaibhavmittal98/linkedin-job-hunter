---
name: linkedin-ind-sponsors
description: Use when changing the IND recognised-sponsor list, the company name-matching logic, the ind_sponsor column, or the Dashboard sponsor filter in linkedin-job-hunter (Netherlands visa sponsorship).
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, ind-sponsors, netherlands, visa, matching]
    related_skills: [linkedin-project-overview, linkedin-database, linkedin-scraping, linkedin-frontend]
---

# IND Sponsors — LinkedIn Job Hunter

Flags each job as an IND-recognised visa sponsor (or not) so the Dashboard can
filter to companies that can actually sponsor a work visa in the Netherlands.

## Data source
- Official IND public register:
  `https://ind.nl/en/public-register-recognised-sponsors/public-register-work`
  (a single HTML `<table>` of ~12,900 organisations: name + KvK number).
- Scraped and normalized into `app/data/ind_sponsors.json` — a list of
  `{name, kvk, key}` records. `key` is the normalized match key.
- ~12,871 distinct keys. The list is **not** collapsed/deduped — matching
  handles variants at lookup time.

## Matcher: `app/services/sponsor.py`
Pure, read-only, no DB/network. Loads the list once at import into module-level
sets. Key functions:
- `normalize(name)` — lowercase, strip accents, `&`→`and`, drop punctuation, drop
  legal-entity tokens (b.v., n.v., holding, group, …). e.g.
  `Coöperatieve Rabobank U.A.` → `rabobank`, `Booking.com B.V.` → `booking com`.
- `is_sponsor(company) -> bool` (LRU-cached) and `match_sponsor(company) -> key|None`.

### Matching rules (tuned for RECALL — a few false positives acceptable, misses are not)
1. **exact** normalized key match.
2. **sponsor-prefix**: a sponsor key is a leading whole-word prefix of the job key
   (`Nedap Beveiligingstechniek` → `nedap`).
3. **job-prefix**: the job key is a leading whole-word prefix of a *multi-word*
   sponsor key (`CGI` → `cgi nederland`, `Spotify` → `spotify netherlands`).
4. **token-subset**: all tokens of a multi-word sponsor key appear in the job
   tokens, with ≥1 distinctive (non-generic) shared token
   (`Just Eat Takeaway.com` → `takeaway com`).

> Word-boundary matching only — NEVER raw substring (substring flags
> "ing"∈"training", "one"∈"components"). Validated against 2,599 real companies:
> ~30% match, no bad substring matches.

### Why not collapse the list?
Collapsing (folding `booking com` into `booking`) caused missed matches: a
LinkedIn "Booking.com" → `booking com` wouldn't equal a collapsed `booking`.
Keep the full key set; let the 4 rules handle variants.

## Storage of the result
- `jobs.ind_sponsor` BOOLEAN column: `True`/`False` when evaluated, `NULL` if not.
- Set at scrape time in `_run_scrape` (`app/routers/jobs.py`) via
  `is_sponsor(raw["company"])`.
- Backfilled on existing rows with a one-off script (normalize + match).

## Filter
- `/api/jobs?ind_sponsor=sponsor|non_sponsor` (empty = all). `non_sponsor`
  includes NULL (treated as non-sponsor).
- Dashboard dropdown: "All companies / IND sponsors only / Non-sponsors".
- JobDetail shows a green "IND Sponsor" badge when `ind_sponsor` is true.

## Refreshing the list
1. `curl` the register page, extract the single `<table>` (name, KvK).
2. Normalize each name → `key`; write `app/data/ind_sponsors.json`.
3. Redeploy; restart. Re-run the backfill to re-flag existing jobs.

## Common Pitfalls
1. The list must exist wherever scrapes run (EC2) — `_run_scrape` calls the
   matcher on every new job.
2. Some global brands are NOT in the register (NN Group, Nationale-Nederlanden,
   MediaMarkt) — they legitimately can't be matched.
3. `is_sponsor` is LRU-cached; hot-swapping the JSON in a live process won't
   refresh the cache/module sets until restart.
4. Adding the column via ALTER TABLE also requires the `Job` model update in
   `app/models.py` (already done) or SQLAlchemy won't know about it.
