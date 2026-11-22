# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Template-based Django web app for managing sports training: **agendas, events, rounds,
exercises, members**, with PDF export of events, QR codes, and admin user impersonation.
Server-rendered (Bootstrap 4), **not** an API. Deployed at **wp.foxugly.com**.

Stack: Python 3.12, **Django 6.1** (exact pins in `requirements.in`), gunicorn, `django-bootstrap4`, `django-hijack`
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

- Install deps: `pip install --require-hashes -r requirements.txt` (hash-pinned Linux lock; on Windows
  use `pip install --require-hashes --no-deps -r requirements.txt` then `pip install -r requirements.in`
  to fill Windows-only deps such as `colorama`)
- Run dev server: `python manage.py runserver` (DB_* unset → SQLite at `db.sqlite3`)
- Apply migrations: `python manage.py migrate`
- Make migrations after model changes: `python manage.py makemigrations`
- Check for model/migration drift (CI gate): `python manage.py makemigrations --check --dry-run`
- Run tests: `python manage.py test` (no pytest; smoke + model tests in `*/tests.py`, security in `event/test_security.py`, admin 2FA in `admin_2fa/tests/` + `event/test_admin_2fa_site.py`, unit hardening in `agenda/test_systemd_hardening.py` — the CI test job gate). CI (`.github/workflows/deploy.yml`) runs `test`, `pip-audit` and CodeQL; there is no lint job.
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
- **PDF generation:** `event.views.PDFEventView` (login required) renders `templates/event_raw.html`
  via wkhtmltopdf (`WKHTMLTOPDF_CMD = /usr/bin/wkhtmltopdf`) with `--disable-javascript` and
  `--disable-local-file-access`. **Never re-enable local file access**: the HTML carries user text
  and wkhtmltopdf runs as `django`, which can read every `/run/<app>/.env`. That template is shared
  with the browser `EventRawView` and **branches on the `pdf` context flag**: PDF → logo inlined as
  a `data:` URI (`logo_uri`); HTML → `{% static %}`.
- **HTML builders** (`Event.get_table*`, `get_title_raw`, `Round.get_row`) return SafeStrings built
  with `format_html` — every value escaped; templates render them **without `|safe`**.
  `Exercise.get_row` is plain text.
- **Auth is global:** `LoginRequiredMiddleware` — every view needs a login unless decorated
  `@login_not_required` (`/health/`, `/lang/`; Django's login/password-reset/admin-login already
  are). `next` redirects go through `tools.generic_views.safe_next_url` (same-host only).

## Admin 2FA

`/admin/` requires a TOTP second factor for **every** staff account (django-otp 1.7.5 + qrcode 8.2,
app `admin_2fa/`, ported from the fleet reference in `Poker_server`). The site itself
(`/accounts/login/` + the app pages) still needs a password only.

- **Wiring**: `'admin_2fa.apps.OTPAdminConfig'` *replaces* `'django.contrib.admin'` (it makes
  `admin.site` an `Admin2FASite`, whose `has_permission` also needs `user.is_verified()`); plus
  `django_otp`, `otp_totp`, `otp_static`, `admin_2fa` in INSTALLED_APPS and
  `django_otp.middleware.OTPMiddleware` right after `AuthenticationMiddleware`. `OTP_TOTP_ISSUER` is
  the label in the authenticator app. A missing piece fails `manage.py check` (`admin_2fa.E001-E004`).
- **LoginRequiredMiddleware**: `Admin2FASite.login` and the `/admin/2fa/` views are
  `@login_not_required` (an overridden `login` loses Django's marker — without it `/admin/login/`
  bounced to `/accounts/login/`). The 2FA views gate on active staff themselves. Covered by
  `event/test_admin_2fa_site.py` and `admin_2fa/tests/`.
- **Flow**: password on `/admin/login/` → `/admin/2fa/setup/` (first time: QR code + key, confirm one
  code, 10 single-use backup codes shown **once**) or `/admin/2fa/verify/` (TOTP code or a backup
  code). Server-rendered admin templates, CSRF, `never_cache`, no inline script/style.
- **Brute force**: django-otp throttles each device (1 s, 2 s, 4 s… after each wrong code) and nginx
  puts `/admin/2fa/` in the same `wp_login` zone as the logins (10 r/min per IP).
- **Lost phone / locked out** (on the box, as the unit runs it; `<username>` is case-insensitive):

  ```bash
  sudo systemd-run --wait --pipe --quiet --uid=django --gid=www-data \
    -p EnvironmentFile=/run/trainingmanager/.env \
    -p WorkingDirectory=/var/www/django_websites/old/django_trainingmanager \
    /var/www/django_websites/old/django_trainingmanager/.venv/bin/python manage.py admin_2fa_reset <username>
  ```

  deletes the user's devices (re-enrolment at the next admin login); `--unlock` only clears the delay.
- **Tests on admin pages**: use `admin_2fa.testing.force_admin_login(self.client, user)`, not
  `client.force_login` (the admin would redirect to the second factor).
- **Secrets**: never log or send to Sentry the TOTP key, the QR code or a backup code — the views keep
  them in `Redacted` wrappers and the form field is named `token` (scrubbed by Sentry).

## Things to know before changing code

- `manage.py` / `config/wsgi.py` default `DJANGO_SETTINGS_MODULE=config.settings` — there is **one**
  settings module (no prod/dev split); prod behaviour is driven entirely by env vars.
- Unset `DB_ENGINE` → SQLite (dev). The app data migrations and the `BigAutoField` id migrations
  are committed; keep `makemigrations --check` clean (CI fails otherwise).
- `static/` (collectstatic output) is currently tracked in git — faithful to the box; the deploy
  re-runs collectstatic anyway.
- Direct deps live in **`requirements.in`** (pinned to the stack running on the box); `requirements.txt`
  is the **hash-pinned lock** generated from it — never edit it by hand, regenerate with the `uv pip compile`
  command in its header. `deploy.sh` installs it with `--require-hashes --no-deps` + `pip check`; CI's
  "Lock is complete" step does the same in a clean venv. The pre-reconstruction list was stale fiction
  (claimed selenium 3.14 / pytz 2018, unused — still present in the box venv, never imported).

## Environment

Env-driven via `django-environ` (bare names; see `.env.example`). Prod values come from SSM
→ `/run/trainingmanager/.env` (systemd EnvironmentFile). Key vars:
- `SECRET_KEY` (required unless `DEBUG` — startup fails without it), `DEBUG`,
  `STATE` (INT/ACC/PROD), `WEBSITE`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`
- `SECURE_SSL_REDIRECT`, `HSTS_SECONDS` (default 31536000), `HSTS_INCLUDE_SUBDOMAINS`, `HSTS_PRELOAD` (only outside DEBUG)
- `SENTRY_DSN` (optional; opt-in — drops `DisallowedHost` scanner noise in `before_send`)
- `DB_*` 6-var convention (`DB_ENGINE`/`DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT`) —
  prod = box-local **PostgreSQL** (`db`/role `trainingmanager`), OPERATIONS.md §3.13.

## Deploy & ops (wp.foxugly.com)

Default branch **`main`**; push → **auto-deploy via GitHub Actions (OIDC → SSM, git-on-box)**.
No manual `git pull`/restart on the box. Server path `/var/www/django_websites/old/django_trainingmanager`,
gunicorn on `127.0.0.1:8003`. The authoritative ops reference is **`OPERATIONS.md`** (source of truth: private repo `Foxugly/foxugly-ops`; the copy on the box is a mirror).

- `deploy/deploy.sh` (runs as `django`): git reset → pip → load `/run` env (literal parse) →
  **pg_dump backup** (`db-backups/`) → migrate → collectstatic → perms → restart
  `trainingmanager-gunicorn`. Then the SSM step (root) installs `deploy/nginx/wp-limits.conf`
  (`wp_login` zone, 10r/m on `/accounts/login/`, `/admin/login/` + `/admin/2fa/`) and the vhost from root's own
  mirror `/var/lib/fleet-deploy/django-trainingmanager.git` at the pushed SHA, then `nginx -t && reload`.
- `deploy/setup-server.sh`: one-time cutover (root, out-of-band) — installs the env-fetch script
  to `/usr/local/sbin`, the systemd units (`trainingmanager-env-fetch` + `-gunicorn`), the sudoers
  drop-in, and the nginx vhost **from the committed git blob** (§3.10-safe). Fails safe if SSM is unreachable.
- `deploy/seed-parameter-store.{sh,ps1}`: seed `/trainingmanager/prod/*` (SECRET_KEY / DB_PASSWORD /
  SENTRY_DSN as SecureString). `deploy/iam/`: the instance-role SSM read + `trainingmanager-deploy`
  OIDC role policies (apply off-box). Monitoring: Sentry `trainingmanager-backend`; box-level
  CloudWatch + Netdata (OPERATIONS.md §3.9b).
