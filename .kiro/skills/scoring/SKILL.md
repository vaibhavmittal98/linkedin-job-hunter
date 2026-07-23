---
name: scoring
description: Job relevance scoring system. Load when modifying scoring criteria, weights, prompts, or debugging score issues.
---

# Scoring

## Location: `app/services/scorer.py`

## How it works
1. Sends job description + user's CV to OpenRouter LLM
2. LLM returns JSON with 5 criteria scores (each 0-10)
3. Weighted average computed → 0-100 final score
4. Disqualifier penalty applied if needed

## Criteria & Weights

| Criteria | Weight | What it measures |
|----------|--------|-----------------|
| `skills_match` | 30% | Does candidate have required technical skills? |
| `experience_level` | 25% | Does seniority/years match? |
| `tech_stack` | 20% | Overlap between candidate's tools and job's requirements? |
| `domain_relevance` | 10% | Is industry/domain experience relevant? |
| `disqualifiers` | 15% | Hard blockers (language, certs, clearance)? 10=no blockers, 0-2=hard blocker |

## Disqualifier Gate
Disqualifiers act as a **gate**, not just a weighted criterion:
- **Hard blocker** (`disqualifiers <= 2`): total score is **capped at 15**, regardless of how strong the other criteria are.
- **Soft concern** (`disqualifiers` 3-4): total score is **halved**.
- No blocker (`>= 5`): no penalty.

This ensures jobs requiring a spoken language the CV doesn't have (e.g. Swedish/German fluency) drop to the bottom.

### What counts as a hard blocker (prompt rules)
- **Spoken/working language:** if the job is written in another language OR requires fluency in a spoken language (German, French, Dutch, ...) and the CV does not mention it → hard blocker (0-2). Programming languages are judged under Tech Stack, NOT here.
- Required certifications, licenses, clearance, or work authorization the CV doesn't show.
- Experience Level is also scored strictly: if the role clearly needs much more seniority/years than the CV shows, score `<= 3`.

## Score Calculation
```python
raw_score = (
    skills_match * 0.30 +
    experience_level * 0.25 +
    tech_stack * 0.20 +
    domain_relevance * 0.10 +
    disqualifiers * 0.15
) * 10

if disqualifiers <= 2:
    score = min(raw_score, 15.0)   # hard blocker gate
elif disqualifiers < 5:
    score = raw_score * 0.5        # soft concern
else:
    score = raw_score
```

## LLM Call (`_call_llm`)
```python
payload = {"model": settings.llm_model, "messages": [{"role": "user", "content": prompt}]}
if reasoning_effort:                       # scoring passes settings.llm_reasoning_effort
    payload["reasoning"] = {"effort": reasoning_effort}
httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    json=payload,
    timeout=60,
)
```

### Extended thinking (reasoning)
- `_call_llm(prompt, reasoning_effort="")` takes an **opt-in** `reasoning_effort` arg.
  Only `score_job()` passes it (`settings.llm_reasoning_effort`); cover-letter refine
  (which also calls `_call_llm`) leaves it empty, so those calls are unchanged.
- Controlled by env var `LLM_REASONING_EFFORT` (default `""` = off). Valid OpenRouter
  values: `minimal | low | medium | high | xhigh | max` (`xhigh`/`max` = maximum).
  Currently set to `high` in production.
- `deepseek-v4-flash` supports reasoning natively (`high` and `xhigh`).
- Verified live: an invalid effort value returns HTTP 400 from OpenRouter, confirming
  the param is parsed/applied (not silently ignored).

## Output Format (from LLM)
```json
{"skills_match": 8, "experience_level": 7, "tech_stack": 9, "domain_relevance": 5, "disqualifiers": 10, "reason": "Strong backend fit, lacks frontend focus"}
```

## Stored in DB
- `Job.relevance_score` — float 0-100
- `Job.score_reason` — formatted breakdown string: "Skills: 8/10 | Experience: 7/10 | ..."

## Endpoints
- `POST /api/jobs/{id}/score` — score single job (requires auth)
- Auto-scored during scrape if CV available

## Tuning Tips
- Adjust weights in `score_job()` function
- Modify prompt for different scoring philosophies
- Current focus: "likelihood of passing screening" not "how much you'd like the job"
