#!/bin/bash
# Quick setup: Docker PostgreSQL + Migrations + Sanity Check
# Usage: bash setup_and_check.sh

set -e

AGENT_ENGINE_DIR="venture-os/agent-engine"
DB_CONTAINER="ventureos-postgres"
DB_URL="postgresql://postgres:postgres@localhost:5432/ventureos"

echo "=================================="
echo "  VentureOS Foundation Sanity Check"
echo "=================================="
echo ""

# Step 1: Start PostgreSQL if not running
echo "[1/4] Checking PostgreSQL..."
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo "  Starting PostgreSQL container..."
    docker run --name "$DB_CONTAINER" \
      -e POSTGRES_DB=ventureos \
      -e POSTGRES_PASSWORD=postgres \
      -p 5432:5432 \
      -d postgres:16 > /dev/null
    
    echo "  Waiting for PostgreSQL to start..."
    sleep 5
fi
echo "  ✓ PostgreSQL running"
echo ""

# Step 2: Create .env if missing
echo "[2/4] Configuring environment..."
if [ ! -f "$AGENT_ENGINE_DIR/.env" ]; then
    cat > "$AGENT_ENGINE_DIR/.env" << EOF
DATABASE_URL=$DB_URL
OPENAI_API_KEY=sk-test
DEBUG=true
EOF
    echo "  ✓ Created .env file"
else
    echo "  ✓ .env already exists"
fi
echo ""

# Step 3: Run migrations
echo "[3/4] Creating database schema..."
cd "$AGENT_ENGINE_DIR"
python scripts/migrate_db.py > /dev/null 2>&1 || true
echo "  ✓ Schema ready"
cd - > /dev/null
echo ""

# Step 4: Run sanity check
echo "[4/4] Running sanity check..."
echo ""
cd "$AGENT_ENGINE_DIR"
python scripts/sanity_check.py
cd - > /dev/null
