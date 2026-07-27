---
name: linkedin-scoring
description: Use when modifying the job relevance scoring system — criteria, weights, prompts, disqualifier logic, or debugging score issues in linkedin-job-hunter.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [linkedin-job-hunter, scoring, llm, openrouter, relevance]
    related_skills: [linkedin-project-overview, linkedin-scraping]
---

# Scoring — LinkedIn Job Hunter

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
- **Hard blocker** (`disqualifiers <= 2`): total score capped at **15**, regardless of other criteria strength.
- **Soft concern** (`disqualifiers` 3-4): total score **halved**.
- No blocker (`>= 5`): no penalty.

### What counts as a hard blocker
- **Spoken/working language:** if the job is written in another language OR requires fluency in a spoken language (German, French, Dutch, ...) and the CV does not mention it → hard blocker (0-2). Programming languages are judged under Tech Stack, NOT here.
- Required certifications, licenses, clearance, or work authorization the CV doesn't show.
- Experience Level scored strictly: if the role clearly needs much more seniority/years than the CV shows, score `<= 3`.

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

## LLM Call (`_call_llm` in `app/services/scorer.py`)
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
- `_call_llm(prompt, reasoning_effort="")` takes an **opt-in** `reasoning_effort` arg. Only `score_job()` passes it (`settings.llm_reasoning_effort`); cover-letter refine leaves it empty.
- Controlled by env var `LLM_REASONING_EFFORT` (default `""` = off). Valid values: `minimal | low | medium | high | xhigh | max`. Currently `high` in production.
- `deepseek-v4-flash` supports reasoning natively (`high` and `xhigh`). An invalid effort value returns HTTP 400 from OpenRouter.

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

## Common Pitfalls
1. **Confusing programming languages with spoken languages** — disqualifiers gate is for spoken language requirements only. Programming language gaps go under Tech Stack.
2. **Changing weights without updating the gate** — the disqualifier logic is separate from the weighted average. Changing criteria weights doesn't change the cap/halve thresholds.
3. **Expecting scores instantly** — each job gets a serial LLM call. A 100-job scrape scores one at a time.
4. **Reasoning effort leaking to non-scoring calls** — `_call_llm` only applies reasoning when `score_job()` passes it. Cover letter refine and chat don't use it.
5. **Hard blocker threshold is strict** — `disqualifiers <= 2` means the LLM deemed the job has a genuine blocker. Adjust the prompt, not the threshold, if false positives.