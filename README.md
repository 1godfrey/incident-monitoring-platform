# Incident Monitoring Platform

A production-style uptime and latency monitoring platform built to demonstrate SRE engineering practices. Monitors external HTTP endpoints, tracks response times and status codes, stores results in PostgreSQL, visualises trends on a live dashboard, and sends Discord alerts on state changes.

---

## Screenshots

> Dashboard showing service cards with uptime percentage, latency charts, and real-time status indicators.

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Backend API | Python 3.11 + FastAPI | Async REST API with OpenAPI docs |
| Database | PostgreSQL 15 | Persistent storage for services and check history |
| ORM | SQLAlchemy 2 (async) | Type-safe, async database access |
| Scheduler | APScheduler | Runs polling jobs on a configurable interval |
| HTTP probing | httpx | Async HTTP client with timeout control |
| Alerting | Discord webhooks | State-transition alerts (up → down, down → up) |
| Frontend | React 18 + Vite | Dashboard with live-polling and Recharts latency graphs |
| Deployment | Docker Compose | Single-command local and production deployment |

---

## Features

- **HTTP uptime monitoring** — polls any public URL on a configurable interval (default 60 s)
- **Content-based health checks** — validate a JSON field in the response body (e.g. GitHub's `status.indicator`) in addition to HTTP status
- **Latency tracking** — stores response time in milliseconds for every check
- **Live dashboard** — React frontend auto-refreshes every 30 s; shows green/red status, uptime %, avg latency, and a per-service latency chart
- **Discord alerts** — fires on state transitions only (up → down / down → up) to prevent alert fatigue
- **Structured JSON logs** — every log line is machine-parseable for ingestion into Datadog, Loki, or CloudWatch
- **No-downtime schema updates** — `ALTER TABLE … ADD COLUMN IF NOT EXISTS` applied at startup so existing DB volumes are migrated automatically

---

## Quick Start

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (includes Docker Compose)

### 1. Clone and configure

```bash
git clone <repo-url>
cd incident-monitoring-platform
cp .env.example .env
```

Open `.env` and set `DISCORD_WEBHOOK_URL` if you want alerting (optional — leave blank to disable).

### 2. Start the full stack

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:3000 |
| API | http://localhost:8000 |
| Interactive API docs | http://localhost:8000/docs |

### 3. Add a service to monitor

Via the dashboard: click **Add Service** in the top-right corner.

Via curl:

```bash
# Basic HTTP check
curl -X POST http://localhost:8000/services/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My API", "url": "https://example.com"}'

# Content-based check (GitHub status API)
curl -X POST http://localhost:8000/services/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub",
    "url": "https://www.githubstatus.com/api/v2/status.json",
    "json_path": "status.indicator",
    "expected_value": "none"
  }'
```

The scheduler picks up new services on its next cycle (within `CHECK_INTERVAL_SECONDS`).

### 4. Stop

```bash
docker compose down          # stops containers, keeps DB volume
docker compose down -v       # stops containers and deletes DB volume
```

---

## Content-Based Health Checks

Some services always return HTTP 200 but embed their real status in a JSON field — GitHub's status API is a common example.

When `json_path` and `expected_value` are provided, the scheduler:

1. Makes the HTTP request as normal
2. Parses the JSON response body
3. Resolves the dot-notation path (e.g. `status.indicator` → `response["status"]["indicator"]`)
4. Compares the resolved value to `expected_value` (case-insensitive)
5. Marks the check **failed** if they don't match — even if HTTP returned 200

The Discord alert includes the actual vs. expected value so the on-call engineer has context immediately.

| Field | Example |
|---|---|
| JSON path | `status.indicator` |
| Expected value (healthy) | `none` |
| GitHub API values | `none` · `minor` · `major` · `critical` |

---

## API Reference

### Services

| Method | Path | Description |
|---|---|---|
| `GET` | `/services/` | List all monitored services |
| `POST` | `/services/` | Register a new service |

**POST /services/ — request body**

```json
{
  "name": "GitHub",
  "url": "https://www.githubstatus.com/api/v2/status.json",
  "json_path": "status.indicator",
  "expected_value": "none"
}
```

`json_path` and `expected_value` are optional. Omit both for a standard HTTP status check.

### Health & Summary

| Method | Path | Description |
|---|---|---|
| `GET` | `/health/{service_id}` | Recent health checks for a service (newest first) |
| `GET` | `/summary` | Uptime % and avg latency for all services |

**Query parameters**

| Endpoint | Param | Default | Range | Description |
|---|---|---|---|---|
| `/health/{id}` | `limit` | 100 | 1 – 1000 | Max checks returned |
| `/summary` | `window_hours` | 24 | 1 – 168 | Lookback window |

---

## Environment Variables

| Variable | Default | Required | Description |
|---|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:postgres@db:5432/incident_monitor` | Yes | Async PostgreSQL DSN |
| `DISCORD_WEBHOOK_URL` | _(empty)_ | No | Discord channel webhook URL; leave blank to disable alerts |
| `CHECK_INTERVAL_SECONDS` | `60` | No | How often each service is polled (seconds) |
| `LOG_LEVEL` | `INFO` | No | `DEBUG` · `INFO` · `WARNING` · `ERROR` |

---

## Project Structure

```
incident-monitoring-platform/
├── docker-compose.yml
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py            # FastAPI app, CORS, lifespan hooks
│       ├── config.py          # Pydantic settings — all config from env vars
│       ├── database.py        # Async SQLAlchemy engine, session, init_db
│       ├── models.py          # ORM models: MonitoredService, HealthCheck
│       ├── schemas.py         # Pydantic I/O schemas
│       ├── crud.py            # All DB query functions
│       ├── logging_config.py  # Structured JSON logging
│       ├── routes/
│       │   ├── services.py    # GET/POST /services
│       │   └── health.py      # GET /health/{id}, GET /summary
│       └── scheduler/
│           └── jobs.py        # APScheduler job, content checks, Discord alerts
│
└── frontend/
    ├── Dockerfile             # Multi-stage: node build → nginx serve
    ├── nginx.conf             # Proxies /api/* → backend, SPA fallback
    ├── package.json
    ├── vite.config.js         # /api proxy for local dev
    └── src/
        ├── App.jsx            # Root — polls /summary + /health every 30 s
        ├── index.css          # Dark theme, CSS custom properties
        ├── api/client.js      # Fetch wrappers for all API endpoints
        └── components/
            ├── Header.jsx
            ├── ServiceCard.jsx
            ├── LatencyChart.jsx   # Recharts LineChart with per-point status dots
            └── AddServiceModal.jsx
```

---

## Database Schema

### `monitored_services`

| Column | Type | Notes |
|---|---|---|
| `id` | integer | Primary key |
| `name` | varchar(255) | Display name |
| `url` | varchar(2048) | Unique; must include scheme (`https://`) |
| `json_path` | varchar(500) | Optional dot-notation path for content checks |
| `expected_value` | varchar(255) | Optional healthy value for content checks |
| `created_at` | timestamptz | Set by the database server |

### `health_checks`

| Column | Type | Notes |
|---|---|---|
| `id` | integer | Primary key |
| `service_id` | integer | Foreign key → `monitored_services.id` (cascade delete) |
| `status_code` | integer | Nullable — no value on network/timeout errors |
| `response_time_ms` | float | Wall-clock time from request start to response |
| `success` | boolean | False if HTTP ≥ 400, timeout, network error, or content check fails |
| `checked_at` | timestamptz | Set by the database server |

---

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Point to a local Postgres instance
export DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/incident_monitor

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev    # http://localhost:5173 — proxies /api → localhost:8000
```

---

## SRE Design Decisions

| Decision | Rationale |
|---|---|
| Alert only on state transitions | Prevents Discord notification spam — a team that ignores noisy alerts misses real incidents |
| `pool_pre_ping=True` | Detects stale DB connections before each query; prevents silent failures after network blips |
| `max_instances=1` on scheduler job | Stops cycles from overlapping when a slow endpoint causes a check to exceed the interval |
| `status_code` nullable | A timeout or DNS failure produces no HTTP status; the schema reflects reality |
| Single aggregation query in `/summary` | One SQL round-trip regardless of service count; avoids N+1 as the service list grows |
| `Promise.allSettled` in the frontend | One broken service ID never blocks the rest of the dashboard from loading |
| `ALTER TABLE … ADD COLUMN IF NOT EXISTS` | New schema columns apply to existing DB volumes without a data wipe or migration tooling |

---

## Production Hardening Checklist

Before deploying beyond a local environment:

- [ ] Replace `init_db()` / `create_all` with [Alembic](https://alembic.sqlalchemy.org/) for versioned, reversible migrations
- [ ] Restrict `allow_origins` in `main.py` to your actual frontend origin (remove the `"*"` wildcard)
- [ ] Move all secrets out of `.env` files into a secrets manager (AWS SSM Parameter Store, HashiCorp Vault, Docker Secrets)
- [ ] Add a data retention policy — at 60 s intervals a single service generates ~1 440 rows/day; partition or prune `health_checks` accordingly
- [ ] Put nginx or a load balancer in front of Uvicorn for TLS termination
- [ ] Extract the scheduler to a separate worker process or use Celery Beat if monitoring more than ~50 services
- [ ] Add a `GET /health` liveness endpoint for container orchestrator health probes
- [ ] Set resource limits (`mem_limit`, `cpus`) on Docker Compose services

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push and open a pull request

---

## License

MIT
