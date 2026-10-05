# Copilot instructions for Zendesk Webhook

## Project context

This repo is a Flask-based Zendesk integration service. The app is centered in `app.py`, which defines the HTTP endpoints, fetches ticket data from Zendesk, and renders the dashboards and ticket pages. The OAuth/auth logic lives in `zendesk_auth.py`; it handles both the modern client-credentials flow and the legacy API-token fallback. UI templates are in `templates/`, and frontend behavior is in `static/`.

The service is designed around a single environment model: configuration is loaded from `.env` for local work and from Docker secrets mounted at `/run/secrets/*` in deployment. The app expects Zendesk credentials such as `SUBDOMAIN`, `ZENDESK_CLIENT_ID`, `ZENDESK_AUTH_SECRET`, and optional `ZENDESK_USER`/`ZENDESK_API_KEY` values.

## Build, test, and lint commands

Use the repo's venv and the package metadata in `pyproject.toml`:

```bash
# Create/activate environment
uv venv
# On Windows:
.\.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install project + dev tools
uv pip install -e ".[dev]"
```

Run a single test file:

```bash
pytest tests/test_app.py -q
pytest tests/test_zendesk_auth.py -q
```

Run a single test case by name:

```bash
pytest tests/test_app.py -k webhook_endpoint -q
pytest tests/test_zendesk_auth.py -k token_thread_safety -q
```

Run the full suite:

```bash
pytest -q
```

Lint/format/type-check commands supported by the repo config:

```bash
python -m black --check .
python -m flake8 .
python -m mypy .
```

Local dev server:

```bash
python app.py
```

## High-level architecture

- `app.py`
  - Creates the Flask app and loads secrets/env values.
  - Normalizes the base Zendesk domain via `normalize_base_domain()`.
  - Builds the `ZendeskAuth` instance and the OAuth token manager.
  - Exposes the dashboard routes (`/`, `/dashboard`, `/open-tickets`), API routes (`/tickets/<id>/comments`, `/api/tickets/<id>/comments`, `/debug-api`), and `/zendesk-webhook`.
  - Uses `requests.get()` and `requests.post()` against Zendesk APIs, then renders Jinja templates or returns JSON.

- `zendesk_auth.py`
  - Contains the reusable auth utilities.
  - `ZendeskOAuthTokenManager` fetches and caches OAuth access tokens using `client_credentials` and refreshes on 401 responses.
  - `ZendeskAuth` injects credentials into outbound requests as either OAuth bearer tokens or Basic auth for the legacy API-key mode.
  - `clean_secret()` and `normalize_base_domain()` keep secret values and subdomains consistent across local and Docker-based environments.

- `templates/`
  - Contains the HTML for the recent-ticket dashboard, KPI dashboard, and open-tickets monitor.
  - The pages are tightly coupled to the values returned by `app.py` and rely on the same Zendesk payload shapes.

- `static/`
  - Contains the JavaScript/CSS used by the dashboards for refresh logic, responsive layouts, and filtering behavior.

- `tests/`
  - Covers both the Flask routes and the auth/token logic.
  - Tests mock Zendesk HTTP calls; keep new tests in this style instead of hitting real Zendesk endpoints.

- Deployment config (`docker-compose*.yml`, `Dockerfile`, `secrets/`)
  - Local and containerized deployments rely on the same environment variables/secrets model.
  - When changing configuration, preserve compatibility with both `.env` and `/run/secrets` loading.

## Key conventions in this repo

- Prefer the OAuth2 client-credentials flow when `ZENDESK_CLIENT_ID` and `ZENDESK_AUTH_SECRET` are set; fall back to `ZENDESK_USER` + `ZENDESK_API_KEY` only when OAuth is unavailable.
- Preserve `clean_secret()` behavior: stripped quotes and whitespace are expected when reading secrets from file-based sources.
- Keep the Zendesk base domain normalized with `normalize_base_domain()` so URLs are built consistently from `SUBDOMAIN`, `https://...`, or bare domain strings.
- Match the existing route/data contract: many templates expect response fields such as `tickets`, `results`, `requester_id`, `assignee_id`, `status`, and `created_at` to be present in Zendesk payloads.
- When adding routes or helper functions, keep the app's current pattern of returning `render_template(...)` for HTML pages and `jsonify(...)` for API responses.
- When touching auth behavior, preserve the 401 retry flow and token caching semantics; the tests explicitly cover these paths.
- Keep the dashboard logic and data-fetching code local to `app.py` unless a concrete refactor requires extracting shared behavior; the repo does not currently use a larger service package or application factory.

## Relevant repo files

- `README.md`: project overview, setup steps, and runtime guidance.
- `CLAUDE.MD`: repo-specific Zendesk endpoint notes and reminder to run tests before finishing work.
- `pyproject.toml`: dependency and tooling configuration for Flask, pytest, black, flake8, and mypy.
- `app.py`: primary application entry point and endpoint logic.
- `zendesk_auth.py`: auth and OAuth token handling.
