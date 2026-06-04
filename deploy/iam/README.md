# IAM for trainingmanager (wp.foxugly.com) — reference

Account `362629935151`, region `eu-west-1`, instance `i-0fe664678563bae5f`,
instance role `quizonline-ec2`. Apply from CloudShell (admin) or the console.
These JSONs are the source of truth; the GitHub repo secrets
(`AWS_DEPLOY_ROLE_ARN`, `EC2_INSTANCE_ID`) are already set.

## 1. Let the instance role read this app's SSM (required for the cutover)

```bash
aws iam put-role-policy --role-name quizonline-ec2 \
  --policy-name trainingmanager-ssm-read \
  --policy-document file://instance-role-trainingmanager-ssm-read.json
```
Console: IAM → Roles → `quizonline-ec2` → Permissions → Add permissions →
Create inline policy → JSON → paste `instance-role-trainingmanager-ssm-read.json`
→ name `trainingmanager-ssm-read`. (Both ARNs — the `/prod` node AND `/prod/*` —
matter; the missing node ARN is what broke ical's first bring-up.)

## 2. Create the OIDC deploy role (for push→auto-deploy)

The account-wide OIDC provider `token.actions.githubusercontent.com` already
exists (used by ical/pushit/foxugly).

```bash
aws iam create-role --role-name trainingmanager-deploy \
  --assume-role-policy-document file://deploy-role-trust.json
aws iam put-role-policy --role-name trainingmanager-deploy \
  --policy-name trainingmanager-deploy-ssm \
  --policy-document file://deploy-role-permissions.json
```
Trust is pinned to `repo:Foxugly/django-trainingmanager:environment:production`
(no wildcard); perms are least-priv (SendCommand on this instance + the
AWS-RunShellScript doc, GetCommandInvocation). Mirrors `pushit-deploy`.

## 3. Seed the SSM parameters

See the handoff / `deploy/seed-parameter-store.{sh,ps1}`. Minimal set under
`/trainingmanager/prod/`: `SECRET_KEY` (SecureString, freshly generated — the
old one is leaked), `DEBUG=False`, `STATE=PROD`, `WEBSITE=wp.foxugly.com`,
`ALLOWED_HOSTS=wp.foxugly.com`, `CSRF_TRUSTED_ORIGINS=https://wp.foxugly.com`.
(No `DATABASE_URL` → sqlite default; no `SENTRY_DSN` → Sentry stays off.)
