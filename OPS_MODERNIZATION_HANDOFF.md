# wp.foxugly.com — ops modernization handoff (option A: keep the UI)

**Goal:** bring wp.foxugly.com (trainingmanager) up to the fleet ops standard
(OPERATIONS.md §3.11/§3.12) — SSM secrets, Sentry, `/health/`, OIDC→SSM CI/CD,
env-fetch in `/usr/local/sbin`, least-priv sudoers, bare env — **while keeping
the template UI** (the API-only `refactor/api-only` branch is left untouched).

## TL;DR of what changed since the first handoff

The original handoff listed four "blockers". Investigating the **box** dissolved
most of them — the situation was a git-hygiene problem, not a code problem:

- The running app was an **uncommitted working tree** on commit `552ad53`, which
  exists nowhere on GitHub. `origin/master` (`c957184`) was an orphaned,
  unrunnable hyphenated-package lineage (a `filter-repo` rewrite had stranded it).
- The box runs a **modern stack** — `Django==6.0.5`, `gunicorn==26.0.0`,
  Python 3.12 — not the ancient `selenium==3.14/pytz==2018.5` the old
  `requirements.txt` *claimed* (the code imports neither).
- The `config/` package **is** the canonical rename (a hyphen isn't importable,
  which is why gunicorn uses `config.wsgi`).

So the canonical source has been **reconstructed from the box's real tree** onto
`main`. Old lineage preserved: branch `legacy/hyphenated-package` + tag
`archive/ops-modernization-v1`.

---

## ✅ Done (on `main`, all committed & pushed; nothing deployed yet)

1. **`import running production tree`** (`bc3b67e`) — git now matches what runs:
   `config/` package, app migrations (were never `git add`ed on the box), the
   small prod edits (PDF `enable-local-file-access`, the `{% if not pdf %}` guard).
2. **env-driven ops** (`5ed2b3a`) — `config/settings.py` via `django-environ`
   (bare names → SSM). Fixes two issues baked into prod: **`DEBUG` was hard-coded
   `True`** and a **leaked `SECRET_KEY`** was hard-coded. Adds prod security
   headers (DEBUG=False only), opt-in Sentry, `/health/`, a **pinned**
   `requirements.txt` (the real stack), and the `BigAutoField` id migrations.
3. **deploy pipeline** (`53e7055`) — env-fetch + systemd units + nginx vhost +
   `deploy.sh` (with a pre-migrate sqlite backup) + `setup-server.sh` cutover +
   SSM seed scripts + `.github/workflows/deploy.yml` (test → OIDC→SSM deploy).

Validated locally (Python 3.14 venv, Django 6.0.5): `manage.py check` clean,
`makemigrations --check` clean, `migrate` OK, `/health/` → `200 {"status":"ok",
"db":"ok"}`, `manage.py test` exit 0.

---

## ⚠️ Risk note — the cutover is a real change to a live site

`setup-server.sh` (and the first git-on-box deploy) **resets the box tree to
`origin/main`** and restarts gunicorn under the new env-driven settings. Effects:

- `SECRET_KEY` switches from the old hard-coded value to the **new SSM value** →
  **all existing sessions are invalidated** (users re-login). This is desired
  (the old key is leaked) but user-visible.
- `DEBUG` flips `True → False`; the debug toolbar disappears; SSL/HSTS headers turn on.
- `db.sqlite3` is gitignored (preserved across the reset); `deploy.sh` also backs
  it up before each `migrate`. The first `migrate` applies the no-op
  `BigAutoField` id alterations.

`setup-server.sh` **fails safe**: if env-fetch can't reach SSM it exits *before*
restarting gunicorn, so the old process keeps serving.

---

## ▶️ YOUR steps — AWS side (mirrors OPERATIONS.md §3.12, do these first)

All off-box (the box's default aws identity is `certbot-route53`, no IAM/SSM):

1. **Seed SSM** `/trainingmanager/prod/*` from this PC — generate a FRESH key:
   ```powershell
   python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
   # put it + the rest in prod.env, then:
   ./deploy/seed-parameter-store.ps1 ./prod.env
   ```
   Minimal `prod.env`: `SECRET_KEY` (fresh), `DEBUG=False`, `STATE=PROD`,
   `WEBSITE=wp.foxugly.com`, `ALLOWED_HOSTS=wp.foxugly.com`,
   `CSRF_TRUSTED_ORIGINS=https://wp.foxugly.com`. Optional: `HSTS_SECONDS=31536000`,
   `SENTRY_DSN`. (`SECRET_KEY`/`SENTRY_DSN` are stored SecureString.)
2. **Instance role** `quizonline-ec2`: allow `ssm:GetParametersByPath` on **both**
   `arn:aws:ssm:eu-west-1:362629935151:parameter/trainingmanager/prod` **and**
   `…/trainingmanager/prod/*` (+ `kms:Decrypt` on `aws/ssm`). (Both ARNs — the
   missing path-node ARN is what broke ical's first bring-up.)
3. **OIDC role** `trainingmanager-deploy`: trust **pinned** to
   `StringEquals … :sub = repo:Foxugly/django-trainingmanager:environment:production`
   (no wildcard); perms least-priv (`ssm:SendCommand` on the instance +
   `AWS-RunShellScript` doc, `ssm:GetCommandInvocation`). No S3 (git-on-box).
4. **GitHub repo secrets**: `AWS_DEPLOY_ROLE_ARN`, `EC2_INSTANCE_ID` (`i-0fe664678563bae5f`).

## ▶️ Then — the cutover (I can run this, or you can)

```bash
ssh … ubuntu@<box>
sudo -v
bash /var/www/django_websites/old/django_trainingmanager/deploy/setup-server.sh
curl -sS https://wp.foxugly.com/health/      # -> {"status":"ok","db":"ok"}
```
After that, every push to `main` auto-deploys (test → OIDC→SSM → `deploy.sh`).
Add a UptimeRobot HTTP monitor on `https://wp.foxugly.com/health/` (§3.9), and a
`trainingmanager-backend` Sentry project if you set `SENTRY_DSN`.

---

## 🧹 Loose ends / notes

- **Verify** (§3.12.9): after cutover,
  `sudo find /var/www/django_websites/old/django_trainingmanager ! -type l \( -perm /020 -o -perm /004 \)` → 0;
  `sudo -l -U django` shows only the `trainingmanager-deploy` grant.
- **Pre-existing PDF logo path bug — FIXED** (`8304336`): `event_raw.html` had a
  wrong hard-coded `file://` path (missing `old/`) that also broke the HTML view.
  Now branches on the `pdf` flag: `file://` from `STATIC_ROOT` for wkhtmltopdf,
  `{% static %}` for the browser. (Ships with the cutover like everything else.)
- **Repo hygiene:** default branch is now `main`. `legacy/hyphenated-package`
  (+ tag `archive/ops-modernization-v1`) preserves the old lineage;
  `refactor/api-only` (the API rewrite) is untouched.
- The box's `static/` is committed (collectstatic output) to keep the cutover a
  faithful no-op; `deploy.sh` re-runs collectstatic each deploy. Gitignoring
  `static/` is a reasonable future cleanup.
