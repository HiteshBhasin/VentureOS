# Quick setup: Docker PostgreSQL + Migrations + Sanity Check
# Usage: powershell -ExecutionPolicy Bypass -File setup_and_check.ps1

$ErrorActionPreference = "Continue"

$AGENT_ENGINE_DIR = "venture-os/agent-engine"
$DB_CONTAINER = "ventureos-postgres"
$DB_URL = "postgresql://postgres:postgres@localhost:5432/ventureos"

Write-Host ""
Write-Host "==================================" -ForegroundColor Cyan
Write-Host "  VentureOS Foundation Sanity Check" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Start PostgreSQL if not running
Write-Host "[1/4] Checking PostgreSQL..." -ForegroundColor Yellow
$container = docker ps 2>$null | Select-String $DB_CONTAINER
if (-not $container) {
    Write-Host "  Starting PostgreSQL container..." -ForegroundColor Gray
    docker run --name $DB_CONTAINER `
      -e POSTGRES_DB=ventureos `
      -e POSTGRES_PASSWORD=postgres `
      -p 5432:5432 `
      -d postgres:16 | Out-Null
    
    Write-Host "  Waiting for PostgreSQL to start..." -ForegroundColor Gray
    Start-Sleep -Seconds 5
}
Write-Host "  ✓ PostgreSQL running" -ForegroundColor Green
Write-Host ""

# Step 2: Create .env if missing
Write-Host "[2/4] Configuring environment..." -ForegroundColor Yellow
$envFile = Join-Path $AGENT_ENGINE_DIR ".env"
if (-not (Test-Path $envFile)) {
    $envContent = @"
DATABASE_URL=$DB_URL
OPENAI_API_KEY=sk-test
DEBUG=true
"@
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-Host "  ✓ Created .env file" -ForegroundColor Green
} else {
    Write-Host "  ✓ .env already exists" -ForegroundColor Green
}
Write-Host ""

# Step 3: Run migrations
Write-Host "[3/4] Creating database schema..." -ForegroundColor Yellow
Push-Location $AGENT_ENGINE_DIR
python scripts/migrate_db.py 2>&1 | Out-Null
Write-Host "  ✓ Schema ready" -ForegroundColor Green
Pop-Location
Write-Host ""

# Step 4: Run sanity check
Write-Host "[4/4] Running sanity check..." -ForegroundColor Yellow
Write-Host ""
Push-Location $AGENT_ENGINE_DIR
python scripts/sanity_check.py
Pop-Location
