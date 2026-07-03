# LLM Integration

Uses [OpenRouter](https://openrouter.ai/) — an OpenAI-compatible API that supports multiple models.

## Setup

1. Create account at https://openrouter.ai/
2. Get API key
3. Set in `.env`:
```
LLM_API_KEY=sk-or-v1-your-key
LLM_MODEL=deepseek/deepseek-v4-flash
LLM_REASONING_EFFORT=high        # optional; extended thinking for scoring only
```

## How It Works

`_call_llm(prompt, reasoning_effort="")` in `app/services/scorer.py`:

```python
payload = {"model": settings.llm_model, "messages": [{"role": "user", "content": prompt}]}
if reasoning_effort:
    payload["reasoning"] = {"effort": reasoning_effort}
response = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    json=payload,
    timeout=60,
)
return response.json()["choices"][0]["message"]["content"]
```

Used by the scorer and the cover letter generator/refiner. The chat feature uses a
separate `_call_llm_messages()` in `app/services/chat.py` that sends a full
system + conversation message array.

### Extended thinking (reasoning)
`reasoning_effort` is opt-in and only passed by `score_job()` (from
`settings.llm_reasoning_effort`). Cover-letter refine calls leave it empty, so they
are unaffected. Valid OpenRouter effort values: `minimal | low | medium | high |
xhigh | max`. `deepseek-v4-flash` supports reasoning natively. An invalid value
returns HTTP 400 (confirming the param is applied, not ignored).

## Scoring

Multi-criteria scoring (each 0-10, weighted):
- Skills Match (30%)
- Experience Level (25%) — scored strictly against required seniority/years
- Tech Stack Overlap (20%)
- Domain Relevance (10%)
- Disqualifiers (15%)

**Disqualifier gate:** hard blocker (`<= 2`, e.g. a required spoken language the CV
lacks) caps total at 15; soft concern (`3-4`) halves total. Returns JSON:
`{"skills_match": 8, "experience_level": 7, ...}`

## Chat

Stateless Q&A about a job + CV (`app/services/chat.py`). System prompt is built from
the CV + optional job context; when no job description is present it's CV-only.
Backed by `POST /api/jobs/{id}/chat` and `POST /api/chat`. Nothing is persisted.

## Cover Letters

Prompt rules: conversational, no buzzwords, no CV regurgitation, max 3 paragraphs, specific facts only. Iteratively refinable via chat.

## Cost (deepseek-v4-flash)

- Scoring: ~$0.001 per job
- Cover letter: ~$0.002 per generation
- Nightly scrape (20 jobs): ~$0.02/day
