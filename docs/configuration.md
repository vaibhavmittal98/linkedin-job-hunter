# Configuration

All configuration via environment variables, loaded from `.env`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./jobs.db` | SQLAlchemy DB URL |
| `APIFY_API_TOKEN` | Yes | — | Apify API token |
| `LLM_API_KEY` | Yes | — | OpenRouter API key |
| `LLM_PROVIDER` | No | `openrouter` | LLM provider |
| `LLM_MODEL` | No | `deepseek/deepseek-v4-flash` | Model for scoring/letters |
| `SECRET_KEY` | No | `change-me-in-production` | JWT signing key |

## `.env.example`

```
DATABASE_URL=sqlite:///./jobs.db
APIFY_API_TOKEN=your_apify_token_here
LLM_API_KEY=your_openrouter_key_here
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-v4-flash
SECRET_KEY=change-me-in-production
```

## Changing LLM Model

Any model on [OpenRouter](https://openrouter.ai/models) works. Just change `LLM_MODEL`:

```
LLM_MODEL=openai/gpt-4o-mini
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_MODEL=meta-llama/llama-3-8b-instruct
```
