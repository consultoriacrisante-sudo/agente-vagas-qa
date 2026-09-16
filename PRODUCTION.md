# Production activation

The agent is fail-closed: missing credentials must not cause invented vacancies or unprotected delivery.

## Required deployment secrets

Configure these in the deployment platform. Never commit real values:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_WEBHOOK_SECRET`
- `SUPABASE_URL`
- `SUPABASE_KEY`
- `CRON_SECRET`

For broad web discovery also configure:

- `TAVILY_API_KEY`

Runtime tuning:

- `MIN_MATCH_SCORE=60`
- `MAX_JOBS_PER_USER=8`
- `TZ=America/Sao_Paulo`

## Database

Apply `supabase/schema.sql` before enabling the cron. Candidate profiles and delivery history are per Telegram user. Raw resume files are not stored in the database by the onboarding runtime.

## Telegram

Create the bot with Telegram's official BotFather. Configure the production webhook to:

`https://<production-host>/telegram/webhook`

Set the webhook secret token to the same value as `TELEGRAM_WEBHOOK_SECRET`.

Smoke test `/start`, upload one PDF/DOCX resume, then set the candidate country explicitly with `/pais Brasil` (or the actual country). Do not infer country from IP or device location.

## Daily runtime

The protected endpoint is:

`GET /cron/daily`

It requires `Authorization: Bearer <CRON_SECRET>`. The Vercel schedule runs on weekdays. Discovery results still pass through URL, remote, geographic eligibility, track, match-score and per-user dedupe gates before Telegram delivery.

## End-to-end acceptance

Production is ready only when all of these are observed with real infrastructure:

1. `/health` returns OK.
2. Telegram webhook rejects an invalid secret.
3. Resume upload creates/updates one candidate profile.
4. Candidate country is explicit.
5. Discovery returns real vacancy URLs or safely returns zero.
6. Hybrid/on-site/ambiguous remote jobs are not delivered.
7. Ineligible geography is not delivered.
8. Salesforce senior roles are not delivered through the junior track.
9. A delivered job has a clickable real application URL.
10. Running the same vacancy again does not resend it to the same user.

Do not enable live delivery until required secrets and the Supabase schema are configured.