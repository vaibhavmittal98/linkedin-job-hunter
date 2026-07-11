# Configuration

All configuration via environment variables, loaded from `.env`.

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `sqlite:///./jobs.db` | SQLAlchemy DB URL |
| `SCRAPER_PROVIDER` | No | `apify` | Scraper backend: `apify` or `brightdata` |
| `APIFY_API_TOKEN` | If Apify | — | Apify API token |
| `BRIGHTDATA_API_TOKEN` | If Bright Data | — | Bright Data API token |
| `BRIGHTDATA_DATASET_ID` | No | `gd_lpfll7v5hcqtkxl6l` | Bright Data LinkedIn-jobs dataset ID |
| `BRIGHTDATA_COUNTRY` | No | `SE` | LinkedIn geo hint for Bright Data discovery |
| `LLM_API_KEY` | Yes | — | OpenRouter API key |
| `LLM_PROVIDER` | No | `openrouter` | LLM provider |
| `LLM_MODEL` | No | `deepseek/deepseek-v4-flash` | Model for scoring/letters/chat |
| `LLM_REASONING_EFFORT` | No | `""` (off) | Extended thinking for scoring only. `minimal`\|`low`\|`medium`\|`high`\|`xhigh`\|`max`. Prod: `high` |
| `SECRET_KEY` | No | `change-me-in-production` | JWT signing key |

## `.env.example`

```
DATABASE_URL=sqlite:///./jobs.db
SCRAPER_PROVIDER=apify
APIFY_API_TOKEN=your_apify_token_here
BRIGHTDATA_API_TOKEN=your_brightdata_token_here
BRIGHTDATA_DATASET_ID=gd_lpfll7v5hcqtkxl6l
BRIGHTDATA_COUNTRY=SE
LLM_API_KEY=your_openrouter_key_here
LLM_PROVIDER=openrouter
LLM_MODEL=deepseek/deepseek-v4-flash
LLM_REASONING_EFFORT=
SECRET_KEY=change-me-in-production
```

## Switching scraper backend

Set `SCRAPER_PROVIDER` to `apify` (default) or `brightdata`, then restart the
service (settings are read at startup). Both backends return the same job
shape, so no other changes are needed.

> Bright Data (`api.brightdata.com`) is intercepted by Cloudflare Gateway on
> local WSL with an untrusted CA, so calls fail there. It works on EC2, which
> isn't behind the Gateway. Apify is bypassed by the policy and works in both.

## Changing LLM Model

Any model on [OpenRouter](https://openrouter.ai/models) works. Just change `LLM_MODEL`:

```
LLM_MODEL=openai/gpt-4o-mini
LLM_MODEL=anthropic/claude-3.5-sonnet
LLM_MODEL=meta-llama/llama-3-8b-instruct
```
