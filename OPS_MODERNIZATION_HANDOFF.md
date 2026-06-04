# wp.foxugly.com — ops modernization handoff (option A)

**Goal:** modernize the OPS of wp.foxugly.com to the fleet standard (OPERATIONS.md §3.11/§3.12)
— SSM secrets, Sentry, `/health`, OIDC→SSM CI/CD, env-fetch in `/usr/local/sbin`, least-priv
sudoers, bare env — **while keeping the template UI** (the API-only `refactor/api-only` rewrite
was deliberately *not* deployed; that branch is preserved untouched).

Branch: **`feat/ops-modernization`** (off `master`). Nothing deployed; the live site is unchanged.

---

## ✅ Done (committed on `feat/ops-modernization`, commit 24fba37)

- **settings.py → env-driven (bare names)** via `django-environ`: `SECRET_KEY`, `DEBUG`,
  `ALLOWED_HOSTS`, `STATE`, `WEBSITE`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL` now read from the
  environment (so prod values come from SSM → `/run/trainingmanager/.env`). All app config
  (INSTALLED_APPS, templates, bootstrap4, hijack…) preserved.
- **Prod security headers** (only when `DEBUG=False`, behind nginx TLS): `SECURE_SSL_REDIRECT`,
  HSTS (env-tunable), secure cookies, `SECURE_PROXY_SSL_HEADER`, nosniff.
- **Opt-in Sentry** (`SENTRY_DSN`, no-op if empty) with a `DisallowedHost` noise filter.
- **`/health/` endpoint** (`django-trainingmanager/health.py`, DB check, 200/503) wired in urls.
- **requirements.txt**: + `django-environ`, `gunicorn`, `sentry-sdk`.

---

## 🔴 BLOCKERS — must be resolved before any deploy (your decisions)

The repo and the live box have **diverged**, and the repo `master` may not even be runnable as-is:

1. **Box ≠ repo (rewritten history).** The deployed box is on `master` at commit **`552ad53`** with
   a Django project package named **`config/`** (`gunicorn config.wsgi:application`). That commit
   **does not exist in the repo** ("Not a valid object name"), and there are `backup/before-filter-repo-*`
   branches → a `git filter-repo` rewrote history. So **the running code is a different lineage** than
   the repo's `master` (commit `c957184`, package `django-trainingmanager/`).

2. **Repo master's package name has a hyphen** (`django-trainingmanager`). Python can't import a
   submodule of a hyphenated package the normal way, so `gunicorn django-trainingmanager.wsgi:application`
   would fail — which is exactly why the **box uses `config.wsgi`**. → The repo `master` is likely
   **not cleanly runnable**; the box's `config`-package version is the real deployable one.

   **Decision needed:** which is the canonical version to deploy?
   - (a) The box's `config`-package version — then I should port the settings/health/Sentry changes
     onto *that* layout (need its source — is it in a branch/backup? or pull from the box tree?).
   - (b) The repo's `django-trainingmanager` master — then the package must be **renamed to an
     importable name** (e.g. `config` or `trainingmanager`) before it can run under gunicorn.

3. **Broken local venv** (`venv/` points at a missing `Python310`) → I couldn't run
   `manage.py check`/tests locally. Recreate a venv to validate.

4. **Ancient deps** (`selenium==3.14.0`, `pytz==2018.5`, `django-wkhtmltopdf`…) may not install on
   a modern Python → CI/test setup will need a pinned Python (3.10/3.11) or dep bumps. This is
   app-modernization, beyond pure ops.

---

## ▶️ Next steps

**You — resolve the version question (blocker 1/2):** tell me the canonical layout (config vs
django-trainingmanager + rename), and how the box should be reconciled (likely a clean re-clone of
the chosen branch, since histories are disjoint).

**You — AWS (when ready, mirrors the §3.12 checklist):**
1. Seed SSM `/trainingmanager/prod/*` (bare names; **generate a NEW `SECRET_KEY`** — the old
   hard-coded one is leaked in git history): `SECRET_KEY` (SecureString), `DEBUG=False`,
   `STATE=PROD`, `ALLOWED_HOSTS=wp.foxugly.com`, `CSRF_TRUSTED_ORIGINS=https://wp.foxugly.com`,
   `WEBSITE=wp.foxugly.com`, `DATABASE_URL` (if not sqlite), `HSTS_SECONDS`, `SENTRY_DSN`.
2. Grant the instance role `quizonline-ec2` `ssm:GetParametersByPath` on **both**
   `…:parameter/trainingmanager/prod` and `…/trainingmanager/prod/*` (+ `kms:Decrypt`).
3. Create OIDC role `trainingmanager-deploy` (trust pinned to
   `repo:Foxugly/django-trainingmanager:environment:production`, SSM-only perms).
4. GitHub secrets: `AWS_DEPLOY_ROLE_ARN`, `EC2_INSTANCE_ID`.

**Me — after the above:** build env-fetch (`/usr/local/sbin/trainingmanager-env-fetch.sh`), the two
units (env-fetch oneshot + gunicorn with the *correct* wsgi + UMask + EnvironmentFile), ssm-deploy.sh,
nginx (+`/health/`; the box-wide `00-default-deny` already covers unknown-Host), sudoers
`trainingmanager-deploy`, ci.yml + deploy.yml (OIDC→SSM), then deploy + verify. Also: rename the
default branch `master`→`main` for fleet consistency.

> ⚠️ The leaked `SECRET_KEY` (`ke2rim3a…`) in git history should be considered compromised —
> the SSM value must be freshly generated, and old sessions/tokens will be invalidated on cutover.
