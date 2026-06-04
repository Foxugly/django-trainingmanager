#!/usr/bin/env bash
# =============================================================================
# TrainingManager (wp.foxugly.com) — one-time cutover to the fleet ops model.
#
# Converts the already-running, drifted deployment to: SSM env, systemd
# env-fetch + gunicorn (EnvironmentFile/UMask), least-priv sudoers, nginx from
# the committed vhost. Idempotent — safe to re-run.
#
# Run as 'ubuntu' (needs sudo), ON THE BOX:
#   sudo -v
#   bash /var/www/django_websites/old/django_trainingmanager/deploy/setup-server.sh
#
# PREREQUISITES (do these FIRST — see OPERATIONS.md §3.12 + the handoff):
#   1. main pushed with the reconstructed config-package tree (this repo).
#   2. SSM /trainingmanager/prod/* seeded (deploy/seed-parameter-store.sh) with a
#      FRESH SECRET_KEY (the old one is leaked), DEBUG=False, STATE=PROD,
#      ALLOWED_HOSTS=wp.foxugly.com, CSRF_TRUSTED_ORIGINS=https://wp.foxugly.com,
#      WEBSITE=wp.foxugly.com.
#   3. EC2 instance role (quizonline-ec2) allowed ssm:GetParametersByPath on BOTH
#      …:parameter/trainingmanager/prod and …/trainingmanager/prod/* (+ kms:Decrypt).
#
# §3.10-safe: every root-owned file is installed from the COMMITTED git blob
# (`git show origin/main:<path>`), never cp'd from the mutable working tree.
# =============================================================================
set -euo pipefail
umask 027

APP_DIR="/var/www/django_websites/old/django_trainingmanager"
APP_USER="django"
APP_GROUP="www-data"
BRANCH="main"

command -v aws >/dev/null || { echo "Installing awscli..."; sudo apt-get update -y && sudo apt-get install -y awscli; }
command -v /usr/bin/wkhtmltopdf >/dev/null || { echo "Installing wkhtmltopdf..."; sudo apt-get update -y && sudo apt-get install -y wkhtmltopdf; }

echo "=== 1/8 Move the tree to origin/$BRANCH (config-package canonical) ==="
# The box's pre-cutover tree is dirty (drifted, with untracked migrations now
# tracked in $BRANCH). -f forces past modified AND "untracked files in the way";
# all of it is already captured in $BRANCH. gitignored data (db.sqlite3,
# db.sqlite3.bak-*) is NOT touched and survives the switch.
sudo -u "$APP_USER" git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
sudo -u "$APP_USER" git -C "$APP_DIR" checkout -f -B "$BRANCH" "origin/$BRANCH"
sudo -u "$APP_USER" git -C "$APP_DIR" reset --hard --quiet "origin/$BRANCH"

echo "=== 2/8 venv deps (adds django-environ, sentry-sdk to the existing venv) ==="
[ -d "$APP_DIR/.venv" ] || sudo -u "$APP_USER" python3 -m venv "$APP_DIR/.venv"
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
sudo -u "$APP_USER" "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

echo "=== 3/8 Install the env-fetch script to /usr/local/sbin (root, from git blob) ==="
sudo -u "$APP_USER" git -C "$APP_DIR" show "origin/$BRANCH:deploy/fetch-env-from-ssm.sh" \
    | sudo install -m 0755 -o root -g root /dev/stdin /usr/local/sbin/trainingmanager-env-fetch.sh

echo "=== 4/8 Install systemd units (root, from git blob) ==="
for unit in trainingmanager-env-fetch.service trainingmanager-gunicorn.service; do
    sudo -u "$APP_USER" git -C "$APP_DIR" show "origin/$BRANCH:deploy/systemd/$unit" \
        | sudo install -m 0644 -o root -g root /dev/stdin "/etc/systemd/system/$unit"
done
sudo systemctl daemon-reload

echo "=== 5/8 Install least-priv sudoers (root, out-of-band; validated) ==="
SUDOERS_FILE="/etc/sudoers.d/trainingmanager-deploy"
# Quoted heredoc keeps the '\' continuations and '!' negations literal. Paths are
# matched literally by sudo — keep /bin/systemctl and /usr/sbin/nginx as proven.
sudo tee "$SUDOERS_FILE" > /dev/null <<'EOF'
# TrainingManager deploy.sh privileges — restart its unit + nginx control only.
Cmnd_Alias TRAININGMANAGER_CTRL = \
    /bin/systemctl restart trainingmanager-gunicorn, \
    /usr/sbin/nginx -t, \
    /bin/systemctl reload nginx
django ALL=(root) NOPASSWD: TRAININGMANAGER_CTRL
Defaults!TRAININGMANAGER_CTRL !setenv, !env_keep
EOF
sudo visudo -c -f "$SUDOERS_FILE"
sudo chmod 440 "$SUDOERS_FILE"

echo "=== 6/8 Fetch env from SSM (FAILS HERE if SSM not seeded / role not granted) ==="
sudo systemctl enable trainingmanager-env-fetch
if ! sudo systemctl restart trainingmanager-env-fetch; then
    echo "ERROR: trainingmanager-env-fetch failed — seed SSM /trainingmanager/prod and" >&2
    echo "       grant the EC2 role read access, then re-run. The OLD gunicorn process" >&2
    echo "       is still serving (not restarted yet). journalctl -u trainingmanager-env-fetch" >&2
    exit 1
fi
test -s /run/trainingmanager/.env || { echo "ERROR: /run/trainingmanager/.env empty." >&2; exit 1; }

echo "=== 7/8 Initial migrate + collectstatic (env sourced from /run) ==="
# Back up sqlite before the first migrate of the cutover.
[ -f "$APP_DIR/db.sqlite3" ] && sudo -u "$APP_USER" cp -p "$APP_DIR/db.sqlite3" "$APP_DIR/db.sqlite3.bak-cutover-$(date +%Y%m%d-%H%M%S)"
sudo -u "$APP_USER" bash -c "set -a
while IFS='=' read -r k v || [ -n \"\$k\" ]; do case \"\$k\" in ''|\#*) continue;; esac; export \"\$k=\$v\"; done < /run/trainingmanager/.env
set +a
'$APP_DIR/.venv/bin/python' '$APP_DIR/manage.py' migrate --noinput && \
'$APP_DIR/.venv/bin/python' '$APP_DIR/manage.py' collectstatic --noinput"
sudo chown -R "$APP_USER":"$APP_GROUP" "$APP_DIR"
sudo chmod -R g-w,o-rwx "$APP_DIR"

echo "=== 8/8 nginx vhost (from git blob) + restart gunicorn ==="
sudo -u "$APP_USER" git -C "$APP_DIR" show "origin/$BRANCH:deploy/nginx/wp.foxugly.com.conf" \
    | sudo install -m 0644 -o root -g root /dev/stdin /etc/nginx/sites-available/wp.foxugly.com
sudo ln -sf ../sites-available/wp.foxugly.com /etc/nginx/sites-enabled/wp.foxugly.com
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl enable trainingmanager-gunicorn
sudo systemctl restart trainingmanager-gunicorn

echo ""
echo "=== Cutover complete ==="
echo "  Verify: curl -sS https://wp.foxugly.com/health/   # -> {\"status\":\"ok\",\"db\":\"ok\"}"
echo "  Logs:   journalctl -u trainingmanager-gunicorn -f ; journalctl -u trainingmanager-env-fetch"
