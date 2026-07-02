# 24/7 Market Briefing Service

This service sends a calm account/market briefing every 8 hours. It uses:

- OpenAI Responses API for the briefing text.
- Twilio Programmable Messaging for SMS delivery.
- Yahoo Finance via `yfinance` for portfolio/index prices.
- RSS feeds for global/business headlines.
- APScheduler interval jobs inside a single-worker FastAPI service.

The service is account-aware but not a trading bot. It summarizes the documented rules and current holdings; it does not invent live orders.

## Local Setup

```bash
cp briefing.env.example .env
cp config/holdings.example.json config/holdings.local.json
```

Fill in `.env` locally:

```bash
OPENAI_API_KEY="your-openai-platform-key"
BRIEF_TO_PHONE="+1..."
TWILIO_ACCOUNT_SID="AC..."
TWILIO_AUTH_TOKEN="replace-with-twilio-auth-token"
TWILIO_FROM_PHONE="+1..."
BRIEFING_DRY_RUN="true"
```

Important: ChatGPT Pro and OpenAI API usage are separate products. The service needs an API key from the OpenAI platform account and billable API access.

Then fill in `config/holdings.local.json` with actual shares/current values. This file is ignored by Git.

## Run Once

```bash
PYTHONPATH=src python -m qlab.briefing_service.main once --dry-run
```

To send one real SMS after credentials are configured:

```bash
BRIEFING_DRY_RUN=false PYTHONPATH=src python -m qlab.briefing_service.main once --send
```

## Run 24/7

```bash
PYTHONPATH=src python -m qlab.briefing_service.main serve --host 0.0.0.0 --port 8080
```

Endpoints:

- `GET /health`
- `GET /briefing/preview` with `X-Admin-Token`
- `POST /briefing/send` with `X-Admin-Token`

Use one process/one worker. Multiple workers would start multiple schedulers and duplicate texts.

## Cloud Deploy

Any long-running container host works: Fly.io, Render, Railway, ECS, GCP Cloud Run with min instances, or a small VM.

Required deployment settings:

- Set every secret as an environment variable, not in Git.
- Set `BRIEFING_DRY_RUN=false` only after one dry-run preview looks sane.
- Set `BRIEF_TO_PHONE` to the real E.164 number in the cloud secret manager.
- Use one worker.
- Keep the process alive 24/7; do not use a request-only serverless target that sleeps through scheduled jobs.

Docker command:

```bash
docker build -t quant-briefing .
docker run --env-file .env -p 8080:8080 quant-briefing
```

## Message Contract

Each SMS should contain:

- One calm opening, addressing the user as "Master Wayne" once.
- Global market tone.
- Account/holding movers.
- Strategy state: hold/tranche/gate status.
- Risk note if a real rule is near trigger.
- Reassurance without pretending losses cannot happen.

No new discretionary trades should come from the LLM layer. The strategy docs and tranche tool are the source of truth.
