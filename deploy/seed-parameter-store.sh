#!/usr/bin/env bash
# =============================================================================
# TrainingManager — Seed AWS SSM Parameter Store from a local .env file.
#
# Source of truth for prod env is SSM (/trainingmanager/prod/*, eu-west-1), NOT
# a .env on the server. This pushes a local prod.env up to SSM.
#
#   bash deploy/seed-parameter-store.sh ./prod.env
#
# Requires AWS creds with ssm:PutParameter (your IAM user / SSO) — NOT the EC2
# instance role, and NOT run on the box (its default identity is certbot-route53).
# Idempotent (--overwrite).
#
# Generate a fresh SECRET_KEY (the old hard-coded one is leaked):
#   python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
#
# Minimal prod.env:
#   SECRET_KEY=<fresh 50-char key>
#   DEBUG=False
#   STATE=PROD
#   WEBSITE=wp.foxugly.com
#   ALLOWED_HOSTS=wp.foxugly.com
#   CSRF_TRUSTED_ORIGINS=https://wp.foxugly.com
#   # HSTS_SECONDS=31536000        # optional
#   # SENTRY_DSN=                  # optional
#
# After seeding, apply on the server:
#   sudo systemctl restart trainingmanager-env-fetch trainingmanager-gunicorn
# =============================================================================
set -euo pipefail

ENV_FILE="${1:?Usage: $0 <path-to-.env>}"
SSM_PREFIX="/trainingmanager/prod"
AWS_REGION="eu-west-1"

# Keys whose values are secrets -> stored as SecureString (KMS key aws/ssm).
SECRET_KEYS=" SECRET_KEY DB_PASSWORD SENTRY_DSN "

[ -f "$ENV_FILE" ] || { echo "No such file: $ENV_FILE" >&2; exit 1; }

while IFS= read -r line || [ -n "$line" ]; do
    [[ -z "${line//[[:space:]]/}" ]] && continue
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    [[ "$line" != *=* ]] && continue

    key="${line%%=*}"
    value="${line#*=}"
    key="${key//[[:space:]]/}"
    [[ -z "$key" ]] && continue

    if [[ "$SECRET_KEYS" == *" $key "* ]]; then
        type="SecureString"
    else
        type="String"
    fi

    echo "  put $SSM_PREFIX/$key  ($type)"
    aws ssm put-parameter \
        --name "$SSM_PREFIX/$key" \
        --value "$value" \
        --type "$type" \
        --overwrite \
        --region "$AWS_REGION" \
        >/dev/null
done < "$ENV_FILE"

echo "Done. Seeded $SSM_PREFIX/* in $AWS_REGION."
echo "Apply on the server: sudo systemctl restart trainingmanager-env-fetch trainingmanager-gunicorn"
