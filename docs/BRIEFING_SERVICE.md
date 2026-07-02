# 24/7 Market Briefing Service

This service sends a calm account/market briefing every 8 hours. It uses:

- OpenAI Responses API for the briefing text.
- Twilio Programmable Messaging for SMS delivery.
- Yahoo Finance via `yfinance` for portfolio/index prices.
- RSS feeds for global/business headlines.
- APScheduler interval jobs inside a single-worker FastAPI service.

The service is account-aware but not a trading bot. It summarizes the documented rules and current holdings; it does not invent live orders.

## Current Deployment Status

The repo contains a deployable cloud worker, but this Codex environment does not contain the live secrets or a configured cloud CLI. These were checked and are currently absent:

- `OPENAI_API_KEY`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_FROM_PHONE` or `TWILIO_MESSAGING_SERVICE_SID`
- `BRIEF_TO_PHONE`
- cloud provider token/CLI

So the service is not live-sending from this machine yet. The remaining activation step is adding those secrets to the cloud host and flipping `BRIEFING_DRY_RUN=false`.

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

For cloud deployment, put the full contents of `config/holdings.local.json` into the secret env var `HOLDINGS_JSON`. That avoids committing or baking private holdings into the Docker image.

## Config Doctor

Local dry-run config check:

```bash
HOLDINGS_PATH=config/holdings.example.json PYTHONPATH=src python -m qlab.briefing_service.main doctor --briefing
```

Live-SMS readiness check:

```bash
BRIEFING_DRY_RUN=false PYTHONPATH=src python -m qlab.briefing_service.main doctor --live
```

`doctor --live` exits non-zero until OpenAI, Twilio, destination phone, sender, and holdings config are all present.

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

For background-worker hosts, prefer:

```bash
PYTHONPATH=src python -m qlab.briefing_service.main scheduler
```

## Cloud Deploy

Any long-running container host works: Render Worker, Fly.io Machine, Railway service, ECS service, GCP Cloud Run with min instances, or a small VM.

This repo includes `render.yaml` for a Render Docker background worker:

1. Create a new Render Blueprint from this GitHub repo.
2. Use the `quant-market-briefing` worker.
3. Fill every `sync: false` secret.
4. Put private holdings JSON in `HOLDINGS_JSON`.
5. Let the first deploy run with `BRIEFING_DRY_RUN=true`.
6. Inspect logs for `doctor`/dry-run behavior if needed.
7. Set `BRIEFING_DRY_RUN=false` only when the preview is correct.

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

Worker command:

```bash
docker run --env-file .env quant-briefing python -m qlab.briefing_service.main scheduler
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
