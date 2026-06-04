# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Template-based Django web app for managing sports training: **agendas, events, rounds,
exercises, members**, with PDF export of events, QR codes, and admin user impersonation.
Server-rendered (Bootstrap 4), **not** an API. Deployed at **wp.foxugly.com**.

Stack: Python 3.12, **Django 6.0.5**, gunicorn, `django-bootstrap4`, `django-hijack`
(impersonation), `django-qr-code`, `django-wkhtmltopdf` (PDF), `django-debug-toolbar`
(DEBUG only), `django-environ`, `psycopg[binary]`, `sentry-sdk`. Custom user model
`customuser.CustomUser`. Languages: `en` / `fr` / `nl`. PostgreSQL (prod) / SQLite (dev).

> **The Django project package is `config/`** (`config.settings`, `config.wsgi`,
> `config.urls`, `config.health`). It was renamed from the original hyphenated
> `django-trainingmanager/` package, which Python can't import as a module — that's why
> gunicorn uses `config.wsgi`. The canonical source on `main` was **reconstructed from the
> running box** (the deployed tree had drifted entirely out of git); the old unrunnable
> lineage is preserved as branch `legacy/hyphenated-package` + tag `archive/ops-modernization-v1`.

## Commands

Activate the venv first (Windows bash): `source .venv/Scripts/activate`

- Install deps: `pip install -r requirements.txt`
- Run dev server: `python manage.py runserver` (DB_* unset → SQLite at `db.sqlite3`)
- Apply migrations: `python manage.py migrate`
- Make migrations after model changes: `python manage.py makemigrations`
- Check for model/migration drift (CI gate): `python manage.py makemigrations --check --dry-run`
- Run tests: `python manage.py test` (no pytest; smoke + model tests in `event/tests.py`, `round/tests.py` — the CI test job gate)
- Create admin user: `python manage.py createsuperuser`

## Architecture

- `config/urls.py` — the **`home` view is inline here** (lists installed app models for the
  dashboard), not in a views module. Also defines `set_lang` (i18n cookie switcher) and wires
  `/health/` + the app includes (`agenda`, `event`, `member`, `round`, `exercise`).
- `config/settings.py` — env-driven (see Environment). `AUTH_USER_MODEL = "customuser.CustomUser"`;
  `HIJACK_REGISTER_ADMIN = False`. `debug_toolbar` is added to INSTALLED_APPS/MIDDLEWARE/urls
  **only when `DEBUG`**. `STATE` (`INT`/`ACC`/`PROD`) is also the Sentry environment.
- `config/health.py` — `/health/` endpoint: `{"status","db"}` 200/503 with a `SELECT 1` DB check.
- Apps: `agenda`, `event`, `round`, `exercise`, `member`, `customuser`. Each owns its models +
  templates. `common_tags.py` sits at the **repo root** and is registered as a template library.
- **PDF generation:** `event.views.PDFEventView` renders `templates/event_raw.html` via
  wkhtmltopdf (`WKHTMLTOPDF_CMD = /usr/bin/wkhtmltopdf`, `enable-local-file-access`). That
  template is shared with the browser `EventRawView` and **branches on the `pdf` context flag**:
  PDF → `file://` built from `STATIC_ROOT` (passed as `logo_uri`); HTML → `{% static %}`.

## Things to know before changing code

- `manage.py` / `config/wsgi.py` default `DJANGO_SETTINGS_MODULE=config.settings` — there is **one**
  settings module (no prod/dev split); prod behaviour is driven entirely by env vars.
- Unset `DB_ENGINE` → SQLite (dev). The app data migrations and the `BigAutoField` id migrations
  are committed; keep `makemigrations --check` clean (CI fails otherwise).
- `static/` (collectstatic output) is currently tracked in git — faithful to the box; the deploy
  re-runs collectstatic anyway.
- `requirements.txt` is **pinned to the stack actually running on the box** (Django 6.0.5, etc.) —
  the pre-reconstruction list was stale fiction (claimed selenium 3.14 / pytz 2018, unused).

## Environment

Env-driven via `django-environ` (bare names; see `.env.example`). Prod values come from SSM
→ `/run/trainingmanager/.env` (systemd EnvironmentFile). Key vars:
- `SECRET_KEY` (required in prod — the old hard-coded key was rotated out), `DEBUG`,
  `STATE` (INT/ACC/PROD), `WEBSITE`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `SECURE_SSL_REDIRECT`, `HSTS_SECONDS`, `HSTS_INCLUDE_SUBDOMAINS`, `HSTS_PRELOAD` (only outside DEBUG)
- `SENTRY_DSN` (optional; opt-in — drops `DisallowedHost` scanner noise in `before_send`)
- `DB_*` 6-var convention (`DB_ENGINE`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`) —
  prod = box-local **PostgreSQL** (`db`/role `trainingmanager`), OPERATIONS.md §3.13.

## Deploy & ops (wp.foxugly.com)

Default branch **`main`**; push → **auto-deploy via GitHub Actions (OIDC → SSM, git-on-box)**.
No manual `git pull`/restart on the box. Server path `/var/www/django_websites/old/django_trainingmanager`,
gunicorn on `127.0.0.1:8003`. The authoritative ops reference is **`OPERATIONS.md`** on the EC2 box.

- `deploy/deploy.sh` (runs as `django`): git reset → pip → load `/run` env (literal parse) →
  **pg_dump backup** (`db-backups/`) → migrate → collectstatic → perms → restart
  `trainingmanager-gunicorn`.
- `deploy/setup-server.sh`: one-time cutover (root, out-of-band) — installs the env-fetch script
  to `/usr/local/sbin`, the systemd units (`trainingmanager-env-fetch` + `-gunicorn`), the sudoers
  drop-in, and the nginx vhost **from the committed git blob** (§3.10-safe). Fails safe if SSM is unreachable.
- `deploy/seed-parameter-store.{sh,ps1}`: seed `/trainingmanager/prod/*` (SECRET_KEY / DB_PASSWORD /
  SENTRY_DSN as SecureString). `deploy/iam/`: the instance-role SSM read + `trainingmanager-deploy`
  OIDC role policies (apply off-box). Monitoring: Sentry `trainingmanager-backend`; box-level
  CloudWatch + Netdata (OPERATIONS.md §3.9b).
