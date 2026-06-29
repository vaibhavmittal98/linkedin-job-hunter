# LLM Integration

Uses [OpenRouter](https://openrouter.ai/) — an OpenAI-compatible API that supports multiple models.

## Setup

1. Create account at https://openrouter.ai/
2. Get API key
3. Set in `.env`:
```
LLM_API_KEY=sk-or-v1-your-key
LLM_MODEL=deepseek/deepseek-v4-flash
```

## How It Works

Single function `_call_llm(prompt)` in `app/services/scorer.py`:

```python
response = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {settings.llm_api_key}"},
    json={"model": settings.llm_model, "messages": [{"role": "user", "content": prompt}]},
)
return response.json()["choices"][0]["message"]["content"]
```

Used by both scorer and cover letter generator.

## Scoring

Multi-criteria scoring (each 0-10, weighted):
- Skills Match (30%)
- Experience Level (25%)
- Tech Stack Overlap (20%)
- Domain Relevance (10%)
- Disqualifiers (15%, halves total if < 5)

Returns JSON: `{"skills_match": 8, "experience_level": 7, ...}`

## Cover Letters

Prompt rules: conversational, no buzzwords, no CV regurgitation, max 3 paragraphs, specific facts only. Iteratively refinable via chat.

## Cost (deepseek-v4-flash)

- Scoring: ~$0.001 per job
- Cover letter: ~$0.002 per generation
- Nightly scrape (20 jobs): ~$0.02/day
