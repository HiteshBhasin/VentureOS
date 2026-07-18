# Sanity Check Setup Guide

## What This Does

The sanity check verifies the foundation of the task distribution system:

- ✓ Database connectivity works
- ✓ `tasks` table exists with `bucket` column
- ✓ Hash distribution is even across 16 buckets
- ✓ Ready to build workers on this foundation

**Time: ~30 seconds**

## Prerequisites

You need a running PostgreSQL instance. Choose one:

### Option 1: Docker (Recommended - 1 minute)

```bash
docker run --name ventureos-postgres \
  -e POSTGRES_DB=ventureos \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  -d postgres:16
```

Wait for it to start (~10 seconds):

```bash
docker logs ventureos-postgres
```

### Option 2: Local PostgreSQL

Install PostgreSQL 15+ on your system and create a database:

```sql
CREATE DATABASE ventureos;
```

### Option 3: Cloud PostgreSQL

Use AWS RDS, Azure Database, or similar. Note the connection URL.

## Setup Steps

### 1. Create `.env` file

```bash
cp venture-os/agent-engine/.env.example venture-os/agent-engine/.env
```

Then edit `.env` and set `DATABASE_URL`:

```ini
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ventureos
```

### 2. Run Migrations

This creates the tables:

```bash
cd venture-os/agent-engine
python scripts/migrate_db.py
```

Expected output:

```
✓ Schema created successfully
✓ Tables ready for use
```

### 3. Run Sanity Check

```bash
python scripts/sanity_check.py
```

## Expected Output

If everything is working:

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
  ...
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

## Troubleshooting

### "connection refused"

Database isn't running. Start PostgreSQL:

```bash
docker start ventureos-postgres
# or start your local PostgreSQL service
```

### "database does not exist"

Create the database:

```bash
psql -h localhost -U postgres -c "CREATE DATABASE ventureos;"
```

### "relation \"public.tasks\" does not exist"

Run migrations first:

```bash
python scripts/migrate_db.py
```

### "password authentication failed"

Check your DATABASE_URL matches your PostgreSQL credentials.

## Next Steps (After Passing)

Once the sanity check passes, you're ready to:

1. Build the worker (`worker.py`)
2. Set up task distribution logic
3. Implement agent execution

The foundation is sound. Build with confidence.
