# CampusPath backend services

Each child directory is a deployment boundary with its own application package, dependencies, lockfile, configuration, tests, and container image. Services communicate over HTTP and never import one another's Python modules.

- **auth_service** (port 8001): Google authentication, access/refresh sessions, revocation, and authorization policy. Owns the `identity` PostgreSQL schema and its Alembic history. No dashboard tables or provider keys.
- **platform_service** (port 8000): dashboards, comparisons, university directory, and durable research jobs. Calls auth for session/policy decisions and enforces owner-scoped data access. Owns the `platform` PostgreSQL schema and its Alembic history. No Google credentials, JWT signing key, or AI dependencies.
- **research_service** (no inbound port): claims jobs from platform and returns researched answers. Owns provider keys and agent execution. No database credentials or identity implementation.

The frontend has two public base URLs: `NEXT_PUBLIC_API_URL` for platform and `NEXT_PUBLIC_AUTH_URL` for auth. Research uses `PLATFORM_SERVICE_URL`; platform uses `AUTH_SERVICE_URL`. Those internal URLs can differ from the public URLs.

## Authentication and authorization boundary

Platform forwards the access cookie to `POST /internal/auth/v1/authorize` using `PLATFORM_SERVICE_TOKEN`. Auth verifies the signature, current session, revocation, and action policy. Resource requests also provide the owner ID loaded from platform-owned data. Auth rejects mismatched owners. Platform continues to scope list and object queries to the authorized subject so other users' data cannot leak. An auth outage fails closed with a service-unavailable response.

Supported policy actions are `platform:read` and `platform:write` for authenticated users accessing their own resources. No administrator or tenant roles are assumed. Browser mutations require the exact configured frontend Origin. Internal authorization requests require a separate service bearer token and do not use browser cookies for service authentication.

## Research boundary and storage

Platform stores all answer values, per-pair statuses, citations, timestamps, and safe error codes in `chats.research_results`, one JSONB document per session. Universities and question definitions remain separate editable records. The frontend still receives a `cells` array per university; platform projects that array from the session document. There are no active per-cell database records.

Each session has exactly one reusable `research_jobs` row, uniquely keyed by `chat_id`. Clicking research snapshots the full set of university/question definitions and a list of target IDs. Completed answers are retained; only missing, stale, or failed pairs are selected. Each enqueue gets a new session revision, so an older completion cannot overwrite a new run or subsequent edits. Adding/removing rows or columns also invalidates outstanding snapshots.

Research uses its own `RESEARCH_SERVICE_TOKEN` and the version 2 protocol:

- `POST /internal/research/v2/claim` with `{timeout_seconds}` returns `{id, attempt, revision, payload}` or 204 when idle.
- `payload` contains `session_id`, `revision`, `major`, `universities` (id/name/country/major), `questions` (id/label), and `targets` (row_id/column_id).
- `POST /internal/research/v2/jobs/{id}/complete` accepts `{attempt, revision, result, error_code}`. `result.cells` contains exactly one completed or failed result for every target. IDs must match the snapshot with no duplicates or unknown pairs.

Completed cell results include a nonempty `answer` and `sources`. Failed results include an `error_code`, not an invented answer. Empty structured output or a provider's "No content found" error becomes `no_content`. Platform persists a safe, user-visible explanation. Provider exception text and credentials never cross into stored results.

Partial success is saved in one JSON write. The same session job is retried with only failed targets, up to three attempts; successful subagents are not rerun. Duplicate/old completions return 409. Claiming, editing, and completing lock the session before its job to keep snapshots consistent. A lease is the configured session timeout plus 30 seconds; a crashed worker can be reclaimed after expiry.

## Parallel subagents

`app/agent/agent.py` is the session coordinator. It explicitly schedules each requested pair concurrently through `unit_level_research`; every pair gets an independent LangChain subagent using the research prompt and date/search/extract tools. Dispatch and result assembly happen in code so a coordinator model cannot omit cells or confuse duplicate university names. `main_agent_prompt.py` remains the orchestration policy reference; only the unit research prompt is sent to models.

`MAX_PARALLEL_UNITS` defaults to 16 (range 1–128). All targets are scheduled, with this limit on simultaneously active subagents. `UNIT_TIMEOUT_SECONDS` defaults to 120. `AGENT_TIMEOUT_SECONDS` now bounds the entire session invocation, defaults to 600, and allows up to 3600 seconds. Set it high enough for the number of waves and provider latency. A whole-process timeout retries outstanding targets; per-unit failures preserve other unit results.

The configured callable is `app.agent.agent:research`. `app/agent/sub_agent.py` builds subagents lazily; `app/tools/sub_agents_tool.py` invokes them. `app/runtime/runner.py` accepts async or sync coordinators and validates session output. `app/runtime/executor.py` bounds the child process and classifies missing/malformed output. `app/clients/platform.py` owns HTTP transport; `app/worker.py` owns claim/execute/complete orchestration.

## Database ownership and migration

Auth and platform have independent `DATABASE_URL` settings. Local configuration uses the existing PostgreSQL database with separate `identity` and `platform` schemas. Each service can instead use its own database when deployed. Separate schemas with the same local database credentials are logical isolation; production should use separate service database roles with access only to their owned schema, or separate databases.

Auth migrations adopt the old public identity tables into `identity` while preserving user/session IDs. Platform migrations adopt public comparison/job tables and the old platform migration history into `platform`. No cross-service foreign key is introduced: platform stores the opaque user ID returned by auth. Migrations fail rather than merge if both source and destination tables already exist.

Run migrations once per service before starting the new deployment. They move data in the configured database; if switching auth to a different database, export/import the existing identity records while preserving IDs before switching traffic. The migration cannot copy records between database URLs automatically. Existing service processes must be stopped during the schema cutover.

## Independent deployment

Build each image from its own directory. Configure the service's `.env` values as hosting secrets; environment files are excluded from image builds. Auth and platform expose their own health endpoint. Research is a supervised worker deployment, with no public web port. Keep both internal API routes private to the service network where supported and use TLS across untrusted networks.

For browser cookies across independently hosted auth and platform services, use HTTPS subdomains of the same site, such as `auth.example.com` and `platform.example.com`, with frontend `app.example.com`. Set auth's `COOKIE_DOMAIN=.example.com`, `COOKIE_SECURE=true`, and both services' `FRONTEND_ORIGIN=https://app.example.com`. Access cookies are shared across the site; refresh and OAuth-state cookies remain host-only on auth. On localhost, omit COOKIE_DOMAIN. Unrelated provider domains require a same-site custom-domain or reverse-proxy setup for this cookie-based login flow.

Set Google OAuth's registered redirect URI to the auth service callback, locally `http://localhost:8001/auth/callback`. The frontend login link now goes directly to auth.

## Local containers

From the project root, after configuring all three service environment files:

```sh
docker compose -f backend/compose.yaml build
docker compose -f backend/compose.yaml run --rm --no-deps auth uv run --no-sync alembic upgrade head
docker compose -f backend/compose.yaml run --rm --no-deps platform uv run --no-sync alembic upgrade head
docker compose -f backend/compose.yaml up -d
```

Compose uses externally configured PostgreSQL and starts auth, platform, and research independently. Each service has automatic restarts. Run the frontend separately.

## Integration test across all microservices

From the repository root, after syncing each service and configuring auth/platform `.env.test` URLs:

```sh
backend/platform_service/.venv/bin/python -m pytest backend/integration_tests -q -ra
```

This starts real auth and platform HTTP processes, seeds real test identities, calls the dashboard API, runs the research worker and agent child process, and verifies PostgreSQL persistence. It uses the real LangChain graph, date tool, and subagent dispatch. Only external model and web responses are deterministic fixtures, so no Google, Anthropic, or Tavily credentials are used. All fixture-owned comparisons and users are cleaned up. The test fails if test URLs are missing instead of silently skipping.

Coverage includes parallel 2×2 dispatch, duplicate university names, row major overrides, owner isolation, one session job and result document, exact grid coverage, no-content errors, partial-result retries, safe error messages, revision changes, and stale/duplicate completion rejection. It applies migrations only to the explicitly configured test databases. The old `scripts/check_service_boundaries.py` command now runs this suite instead of fake-persistence smoke checks.

Before deploying this change, stop old platform/research processes and run platform's migration `0003`. It aggregates existing cell answers into the session JSON document, changes pending cells to stale, consolidates old jobs into one superseded job per session, and removes the legacy per-cell tables. Requeue research after restarting both services with protocol v2. Back up the deployment database before this schema cutover.
