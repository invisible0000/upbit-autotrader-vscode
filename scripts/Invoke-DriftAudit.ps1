<#!
.SYNOPSIS
  Run all drift audit scripts and aggregate latest JSON reports.
.DESCRIPTION
  Executes architecture, DB schema, and doc freshness audits. Creates reports directory if missing.
.NOTES
  Requires Python in PATH and project dependencies installed.
#>
param(
  # 스크립트 자신이 위치한 디렉터리 상위(프로젝트 루트) 기준으로 설정
  [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)),
  [string]$ReportsDir = "docs/drift_audit/reports"
)

Write-Host "[DriftAudit] Repository Root: $RepoRoot" -ForegroundColor Cyan
if (-not (Test-Path (Join-Path $RepoRoot 'docs'))) {
  Write-Host "[DriftAudit] ERROR: docs 폴더를 찾을 수 없습니다. RepoRoot 계산 오류 가능" -ForegroundColor Red
  exit 2
}
$archScript = Join-Path $RepoRoot 'docs/drift_audit/scripts/architecture_drift_audit.py'
$dbScript   = Join-Path $RepoRoot 'docs/drift_audit/scripts/db_schema_check.py'
$docScript  = Join-Path $RepoRoot 'docs/drift_audit/scripts/doc_freshness_scan.py'
$top5Script = Join-Path $RepoRoot 'docs/drift_audit/scripts/top5_drift_report.py'
$weightsFile = Join-Path $RepoRoot 'docs/drift_audit/config/drift_weights.json'

if (-not (Test-Path $ReportsDir)) { New-Item -ItemType Directory -Force -Path $ReportsDir | Out-Null }

# 1. Architecture audit
$archOut = Join-Path $ReportsDir 'latest_arch.json'
Write-Host "[DriftAudit] Architecture audit..." -ForegroundColor Yellow
python $archScript --root $RepoRoot --output $archOut

# 2. DB schema audit
$dbOut = Join-Path $ReportsDir 'db_schema_latest.json'
Write-Host "[DriftAudit] DB schema audit..." -ForegroundColor Yellow
python $dbScript --schema-dir (Join-Path $RepoRoot 'data_info') `
  --db (Join-Path $RepoRoot 'data/settings.sqlite3') `
  --db (Join-Path $RepoRoot 'data/strategies.sqlite3') `
  --db (Join-Path $RepoRoot 'data/market_data.sqlite3') `
  --output $dbOut

# 3. Doc freshness audit
$docOut = Join-Path $ReportsDir 'doc_freshness_latest.json'
Write-Host "[DriftAudit] Doc freshness audit..." -ForegroundColor Yellow
python $docScript --root (Join-Path $RepoRoot 'docs') --output $docOut

# 4. Top-5 report
$top5Md = Join-Path $ReportsDir 'top5_drift_report.md'
$top5Json = Join-Path $ReportsDir 'top5_drift_report.json'
Write-Host "[DriftAudit] Top-5 drift report..." -ForegroundColor Yellow
if (Test-Path $weightsFile) {
  Write-Host "[DriftAudit] Using weights file: $weightsFile" -ForegroundColor Cyan
  python $top5Script `
    --arch $archOut `
    --db $dbOut `
    --docs $docOut `
    --weights $weightsFile `
    --output-md $top5Md `
    --output-json $top5Json
}
else {
  python $top5Script `
    --arch $archOut `
    --db $dbOut `
    --docs $docOut `
    --output-md $top5Md `
    --output-json $top5Json
}

Write-Host "[DriftAudit] Completed. Reports:" -ForegroundColor Green
Get-ChildItem $ReportsDir -Filter *.json | ForEach-Object { Write-Host " - $($_.FullName)" }
Get-ChildItem $ReportsDir -Filter top5_drift_report.md | ForEach-Object { Write-Host " - $($_.FullName)" }
