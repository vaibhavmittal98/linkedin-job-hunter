---
name: ind-sponsors
description: IND recognised-sponsor matching for jobs (Netherlands visa sponsorship). Load when changing the sponsor list, the name-matching logic, or the Dashboard sponsor filter.
---

# IND Sponsors

Flags each job as an IND-recognised visa sponsor (or not) so the Dashboard can
filter to companies that can actually sponsor a work visa in the Netherlands.

## Data source
- Official IND public register:
  `https://ind.nl/en/public-register-recognised-sponsors/public-register-work`
  (a single HTML `<table>` of ~12,900 organisations: name + KvK number).
- Scraped and normalized into `app/data/ind_sponsors.json` — a list of
  `{name, kvk, key}` records. `key` is the normalized match key.
- ~12,871 distinct keys. Refresh by re-fetching the page and regenerating the
  JSON (see "Refreshing" below). The list is **not** collapsed/deduped — matching
  handles variants at lookup time.

## Matcher: `app/services/sponsor.py`
Pure, read-only, no DB/network. Loads the list once at import into module-level
sets. Key functions:
- `normalize(name)` — lowercase, strip accents, `&`→`and`, drop punctuation, drop
  legal-entity tokens (b.v., n.v., holding, group, …). e.g.
  `Coöperatieve Rabobank U.A.` → `rabobank`, `Booking.com B.V.` → `booking com`.
- `is_sponsor(company) -> bool` (LRU-cached) and `match_sponsor(company) -> key|None`.

### Matching rules (tuned for RECALL — a few false positives are acceptable, misses are not)
1. **exact** normalized key match.
2. **sponsor-prefix**: a sponsor key is a leading whole-word prefix of the job key
   (`Nedap Beveiligingstechniek` → `nedap`).
3. **job-prefix**: the job key is a leading whole-word prefix of a *multi-word*
   sponsor key (`CGI` → `cgi nederland`, `Spotify` → `spotify netherlands`).
4. **token-subset**: all tokens of a multi-word sponsor key appear in the job
   tokens, with ≥1 distinctive (non-generic) shared token
   (`Just Eat Takeaway.com` → `takeaway com`).

> Word-boundary matching only — NEVER raw substring (substring flags
> "ing"∈"training", "one"∈"components", etc.). This was validated against 2,599
> real companies: ~30% match, and the bad substring matches don't occur.

### Why not collapse the list?
Collapsing (e.g. folding `booking com` into `booking`) caused missed matches
(a LinkedIn "Booking.com" → `booking com` wouldn't equal a collapsed `booking`).
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
2. Normalize each name → `key`; write `app/data/ind_sponsors.json`
   (`[{name, kvk, key}, …]`).
3. Redeploy; restart. To re-flag existing jobs, re-run the backfill.

## Gotchas
- The list must exist wherever scrapes run (EC2), because `_run_scrape` calls the
  matcher on every new job.
- Some global brands are simply NOT in the register (e.g. NN Group,
  Nationale-Nederlanden, MediaMarkt) — they legitimately can't be matched.
- `is_sponsor` is LRU-cached; if you hot-swap the JSON in a live process, the
  cache/module sets won't refresh until restart.
