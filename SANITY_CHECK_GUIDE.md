# 🚀 Foundation Sanity Check - Quick Start

Your task: **Verify the foundation is sound in 30 seconds**

- ✅ Cluster exists (PostgreSQL)
- ✅ Tables exist (tasks table with bucket column)
- ✅ Buckets spread evenly (16 buckets, ~equal distribution)
- ✅ Ready to build workers

## TL;DR - Windows (30 seconds)

### Prerequisites Check

```powershell
# 1. Check Docker is running
docker ps

# 2. If not running, start it (Docker Desktop app, or:)
docker run hello-world
```

### One Command Setup

```powershell
# From VentureOS root directory:
powershell -ExecutionPolicy Bypass -File setup_and_check.ps1
```

Done! This will:

1. Start PostgreSQL in Docker
2. Wait for it to be ready
3. Create `.env` file
4. Run migrations
5. Run sanity check (500 fake tasks → bucket distribution)

## TL;DR - macOS/Linux (30 seconds)

### Prerequisites Check

```bash
docker ps
```

### One Command Setup

```bash
# From VentureOS root directory:
bash setup_and_check.sh
```

## Manual Setup (if you prefer)

### Step 1: Start PostgreSQL

**Option A: Docker** (recommended)

```bash
docker run --name ventureos-postgres \
  -e POSTGRES_DB=ventureos \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:16
```

Wait for it:

```bash
docker logs ventureos-postgres | grep "database system is ready"
```

**Option B: Already installed locally**

```bash
# macOS with Homebrew
brew services start postgresql

# Windows with PostgreSQL installed
# (Start the service via Services app or pgAdmin)

# Linux
sudo systemctl start postgresql
```

**Option C: Existing cloud database**
Just get the connection URL (e.g., from AWS RDS, Azure, etc.)

---

### Step 2: Create `.env`

```bash
cd venture-os/agent-engine
cp .env.example .env
```

Edit `.env` and set `DATABASE_URL`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ventureos
```

Or if using a cloud database:

```ini
DATABASE_URL=postgresql://user:password@your-host:5432/ventureos
```

---

### Step 3: Run Migrations

This creates all tables (idempotent — safe to run multiple times):

```bash
python scripts/migrate_db.py
```

Expected output:

```
✓ Connected to database
✓ Schema created successfully
✓ All tables ready
```

---

### Step 4: Run Sanity Check

```bash
python scripts/sanity_check.py
```

### Expected Output (Success)

```
======================================================================
  SANITY CHECK: Task Distribution Across 16 Buckets
======================================================================

✓ Connected to database

✓ Tables and bucket column exist

Inserting 500 fake tasks...
✓ Inserted 500 tasks in 1.23s

Counting tasks per bucket...

Bucket Distribution (target: ~31-32 per bucket)
--------------------------------------------------
  ✓ Bucket  0:  31 tasks ( 6.2%) ████████
  ✓ Bucket  1:  32 tasks ( 6.4%) ████████
  ✓ Bucket  2:  30 tasks ( 6.0%) ████████
  ✓ Bucket  3:  33 tasks ( 6.6%) ████████
  ✓ Bucket  4:  31 tasks ( 6.2%) ████████
  ✓ Bucket  5:  30 tasks ( 6.0%) ████████
  ✓ Bucket  6:  32 tasks ( 6.4%) ████████
  ✓ Bucket  7:  31 tasks ( 6.2%) ████████
  ✓ Bucket  8:  30 tasks ( 6.0%) ████████
  ✓ Bucket  9:  32 tasks ( 6.4%) ████████
  ✓ Bucket 10:  31 tasks ( 6.2%) ████████
  ✓ Bucket 11:  33 tasks ( 6.6%) ████████
  ✓ Bucket 12:  30 tasks ( 6.0%) ████████
  ✓ Bucket 13:  31 tasks ( 6.2%) ████████
  ✓ Bucket 14:  32 tasks ( 6.4%) ████████
  ✓ Bucket 15:  31 tasks ( 6.2%) ████████
--------------------------------------------------
Total: 500 tasks

Max deviation:  8.3%
Avg deviation:  4.1%

✓ PASS: Hash distribution is sound!
  → Cluster exists
  → Tables exist
  → Buckets spread evenly
  → Ready to build workers on this foundation
```

## What Each Check Does

| Check             | What                           | Why                                                   |
| ----------------- | ------------------------------ | ----------------------------------------------------- |
| **Connect**       | Database accepts connection    | If it fails, your DB URL is wrong or DB isn't running |
| **Table exists**  | `tasks` table found            | Schema wasn't created (run migrations)                |
| **Bucket column** | Hash distribution column found | Schema is old or migrations failed                    |
| **Distribution**  | 500 tasks across 16 buckets    | Hash function is working correctly                    |
| **Evenness**      | Max deviation < 15%            | If one bucket is fat, hashing is broken               |

## Troubleshooting

### "connection refused" or "could not connect to server"

```bash
# PostgreSQL isn't running
docker logs ventureos-postgres
# or check your local PostgreSQL service
```

### "database ventureos does not exist"

```bash
# Connect and create it
psql -h localhost -U postgres -c "CREATE DATABASE ventureos;"
```

### "relation \"public.tasks\" does not exist"

```bash
# Run migrations
python scripts/migrate_db.py
```

### "password authentication failed"

```bash
# Update your DATABASE_URL in .env to match your PostgreSQL password
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/ventureos
```

### "could not translate host name \"localhost\" to address"

```bash
# Use 127.0.0.1 instead of localhost
DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:5432/ventureos
```

## After the Check Passes ✅

Once you see the green **PASS** message, your foundation is solid:

1. **Cluster is online** — PostgreSQL is running and responding
2. **Schema is correct** — Tables and columns exist as expected
3. **Distribution is even** — The hash function spreads tasks evenly
4. **Ready for workers** — Build the worker process confidently

**Next:** Implement the worker to claim and execute tasks from the queue.

---

## Stop/Clean Up

### Stop PostgreSQL Container

```bash
docker stop ventureos-postgres
```

### Remove PostgreSQL Container (reset database)

```bash
docker rm ventureos-postgres
```

### Restart PostgreSQL Container

```bash
docker start ventureos-postgres
```

---

**Questions?** See `venture-os/agent-engine/IMPLEMENTATION_GUIDE.md` for full architecture details.
