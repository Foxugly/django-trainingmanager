<#
.SYNOPSIS
  Seed AWS SSM Parameter Store (/trainingmanager/prod/*, eu-west-1) from a local .env.

.DESCRIPTION
  Source of truth for prod env vars is SSM, NOT a .env on the server.
  Requires the AWS CLI configured with creds allowing ssm:PutParameter (your IAM
  user / SSO) — NOT the EC2 instance role, and NOT run on the box.
  Idempotent (--overwrite). --overwrite does NOT change a parameter's Type:
  to promote String -> SecureString, delete-parameter first, then re-seed.

  Generate a fresh SECRET_KEY (the old hard-coded one is leaked):
    python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"

  After seeding, apply on the server:
    sudo systemctl restart trainingmanager-env-fetch trainingmanager-gunicorn

.EXAMPLE
  ./deploy/seed-parameter-store.ps1 ./prod.env
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string]$EnvFile
)
$ErrorActionPreference = "Stop"

$SsmPrefix = "/trainingmanager/prod"
$AwsRegion = "eu-west-1"

# Keys whose values are secrets -> SecureString (KMS key aws/ssm). Rest -> String.
$SecretKeys = @("SECRET_KEY", "DATABASE_PASSWORD", "SENTRY_DSN")

if (-not (Test-Path -LiteralPath $EnvFile)) { throw "No such file: $EnvFile" }

foreach ($line in Get-Content -LiteralPath $EnvFile) {
    if ($line -match '^\s*$' -or $line -match '^\s*#') { continue }
    $idx = $line.IndexOf('=')
    if ($idx -lt 1) { continue }

    $key = $line.Substring(0, $idx).Trim()
    $value = $line.Substring($idx + 1)
    if ([string]::IsNullOrWhiteSpace($key)) { continue }

    $type = if ($SecretKeys -contains $key) { "SecureString" } else { "String" }

    Write-Host "  put $SsmPrefix/$key  ($type)"
    aws ssm put-parameter `
        --name "$SsmPrefix/$key" `
        --value "$value" `
        --type $type `
        --overwrite `
        --region $AwsRegion | Out-Null
}

Write-Host "Done. Seeded $SsmPrefix/* in $AwsRegion."
Write-Host "Apply on the server:"
Write-Host "  sudo systemctl restart trainingmanager-env-fetch trainingmanager-gunicorn"
