#!/usr/bin/env bash
# =============================================================================
# TrainingManager (wp.foxugly.com) — app deploy script.
#
# Called by GitHub Actions via OIDC -> SSM (AWS-RunShellScript runs as root,
# which invokes this as the django user), or manually:
#   sudo -u django bash /var/www/django_websites/old/django_trainingmanager/deploy/deploy.sh
#
# Root-side install of units / nginx / the env-fetch script is a ONE-TIME job
# done out-of-band by deploy/setup-server.sh (§3.10) — not repeated here.
# =============================================================================
set -euo pipefail
umask 027   # new dirs 750 / files 640 from git/pip/collectstatic (OPERATIONS.md §3.1/§3.2)

APP_DIR="/var/www/django_websites/old/django_trainingmanager"
VENV="$APP_DIR/.venv"

cd "$APP_DIR"

echo ">>> Pulling latest code..."
git fetch origin main
git reset --hard origin/main

echo ">>> Installing dependencies..."
"$VENV/bin/pip" install --quiet -r requirements.txt

# Load the SSM-fetched env so manage.py has SECRET_KEY, STATE, ALLOWED_HOSTS,
# etc. systemd injects this for the service via EnvironmentFile, but a manual
# command does not get it — parse it here. (trainingmanager-env-fetch.service
# writes this file at boot from SSM /trainingmanager/prod/*.)
ENV_FILE="/run/trainingmanager/.env"
if [ -f "$ENV_FILE" ]; then
    echo ">>> Loading env from $ENV_FILE..."
    # Parse literally (key=value), NOT `source`: this is a systemd
    # EnvironmentFile, and values (e.g. SECRET_KEY) may contain shell-special
    # chars ($ ` ( ) …) that `.` would expand/mangle — which silently emptied a
    # SECRET_KEY and broke `migrate` on pushit. Mirrors systemd parsing.
    while IFS='=' read -r _k _v || [ -n "$_k" ]; do
        case "$_k" in ''|\#*) continue ;; esac
        export "$_k=$_v"
    done < "$ENV_FILE"
    unset _k _v
else
    echo "WARNING: $ENV_FILE missing — has trainingmanager-env-fetch run? Trying without it." >&2
fi

# Back up the sqlite DB before migrating (this site is sqlite-backed). Keep the
# last 5 backups. Skipped automatically if a non-sqlite DATABASE_URL is set.
if [ -f "$APP_DIR/db.sqlite3" ] && [ -z "${DATABASE_URL:-}" ]; then
    TS="$(date +%Y%m%d-%H%M%S)"
    cp -p "$APP_DIR/db.sqlite3" "$APP_DIR/db.sqlite3.bak-$TS"
    echo ">>> Backed up db.sqlite3 -> db.sqlite3.bak-$TS"
    ls -1t "$APP_DIR"/db.sqlite3.bak-* 2>/dev/null | tail -n +6 | xargs -r rm -f
fi

echo ">>> Running migrations..."
"$VENV/bin/python" manage.py migrate --noinput

echo ">>> Collecting static files..."
"$VENV/bin/python" manage.py collectstatic --noinput

echo ">>> Normalizing permissions (idempotent: dirs 750 / files 640, no o-rwx, no g-w)..."
# deploy.sh runs as django, which OWNS the whole tree (primary group www-data),
# so this needs NO sudo. chown first (fixes group drift), then chmod (drop
# group-write + all "other"). Owner bits untouched -> execute preserved on
# .venv/bin, manage.py, deploy/*.sh.
chown -R django:www-data "$APP_DIR"
chmod -R g-w,o-rwx "$APP_DIR"

# trainingmanager-env-fetch is intentionally NOT restarted here — a code deploy
# keeps the env already in /run/trainingmanager/.env. To pick up changed SSM
# values: `sudo systemctl restart trainingmanager-env-fetch` then restart gunicorn.
echo ">>> Restarting service..."
sudo /bin/systemctl restart trainingmanager-gunicorn

echo ">>> Deploy complete."
