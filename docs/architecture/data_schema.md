# Threadline — Data Schema

**Version:** 1.0  
**Status:** Approved for build  
**Last updated:** July 1, 2026  

---

## Overview

This document defines the database schema for Threadline. The database is hosted on Supabase (PostgreSQL) with the pgvector extension enabled for semantic search.

Only confirmed tables are documented here. Additional tables will be added as architectural decisions are made during the build.

---

## Database: Supabase (PostgreSQL + pgvector)

**Project:** threadline-app  
**Extension required:** `vector` (pgvector) — must be enabled before running migrations  

To enable pgvector in Supabase:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Tables

---

### Table: `consumer_signals`

The core data table. Every Reddit post and Amazon review that passes the quality gate is stored here as a single record. This is the foundation of everything Threadline does.

**SQL:**
```sql
CREATE TABLE consumer_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  source TEXT NOT NULL CHECK (source IN ('reddit', 'amazon')),
  source_url TEXT NOT NULL,
  source_id TEXT NOT NULL UNIQUE,
  condition TEXT NOT NULL CHECK (condition IN (
    'post_mastectomy',
    'ostomy',
    'rheumatoid',
    'post_surgical'
  )),
  raw_text TEXT NOT NULL,
  pain_points JSONB,
  mentioned_features JSONB,
  sentiment TEXT CHECK (sentiment IN ('positive', 'negative', 'mixed')),
  upvotes INTEGER DEFAULT 0,
  embedding VECTOR(1536),
  scraped_at TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Column definitions:**

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | UUID | Yes | Unique record ID, auto-generated |
| `source` | TEXT | Yes | `reddit` or `amazon` only |
| `source_url` | TEXT | Yes | Full URL to original post or review |
| `source_id` | TEXT | Yes | Reddit post ID or Amazon ASIN + review ID — used to prevent duplicate ingestion |
| `condition` | TEXT | Yes | One of the four launch conditions |
| `raw_text` | TEXT | Yes | Original unmodified text of the post or review |
| `pain_points` | JSONB | No | Array of pain points extracted by Claude — null if extraction failed |
| `mentioned_features` | JSONB | No | Array of product features mentioned — null if none found |
| `sentiment` | TEXT | No | Overall sentiment of the record |
| `upvotes` | INTEGER | No | Reddit upvotes or Amazon helpfulness votes — defaults to 0 |
| `embedding` | VECTOR(1536) | No | Semantic embedding — null until embedding pipeline runs |
| `scraped_at` | TIMESTAMP | Yes | When this record was fetched from the source |
| `created_at` | TIMESTAMP | Yes | When this record was inserted into the database — auto-set |

**Indexes:**
```sql
-- Fast lookup by condition (used in hybrid search)
CREATE INDEX idx_consumer_signals_condition ON consumer_signals(condition);

-- Fast deduplication check by source_id
CREATE INDEX idx_consumer_signals_source_id ON consumer_signals(source_id);

-- Vector similarity search index (HNSW — recommended for pgvector in 2026)
CREATE INDEX idx_consumer_signals_embedding ON consumer_signals
USING hnsw (embedding vector_cosine_ops);
```

**Notes:**
- `source_id` has a UNIQUE constraint — the pipeline uses this to skip records already in the database (upsert pattern)
- `embedding` is nullable — records are inserted first, then embeddings are added in a second pass. This allows the pipeline to recover if the embedding step fails
- `pain_points` and `mentioned_features` are JSONB — flexible structure that can evolve as we learn what Claude extracts
- The HNSW index on `embedding` enables fast approximate nearest neighbour search — required for semantic search to be fast at scale
- **Important caveat:** When combining HNSW vector search with a WHERE clause filter (e.g. filtering by `condition`), pgvector may return fewer rows than requested. This is a known behaviour. Mitigation: enable `hnsw.iterative_scan` in the query session, which tells pgvector to keep scanning until enough filtered results are found. This was introduced in pgvector 0.8.0.

**Example `pain_points` value:**
```json
[
  "Cannot fasten back closures with limited arm mobility",
  "Standard bras cause discomfort against surgical drain sites"
]
```

**Example `mentioned_features` value:**
```json
[
  "front closure",
  "magnetic buttons",
  "soft cotton",
  "drain pocket"
]
```

---

### Table: `keepalive`

A small utility table used to prevent Supabase from pausing the free tier project. A GitHub Actions workflow inserts a row every 5 days, resetting the 7-day inactivity timer. Rows older than 7 days are deleted on each run.

**SQL:**
```sql
CREATE TABLE keepalive (
  id SERIAL PRIMARY KEY,
  pinged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Column definitions:**

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | SERIAL | Yes | Auto-incrementing integer |
| `pinged_at` | TIMESTAMP | Yes | When the ping ran — auto-set |

**Notes:**
- This table will never exceed ~5 rows
- No indexes needed — this table is never queried for application purposes
- Do not delete this table — it is required for Supabase free tier stability

---

### Table: `validations` *(future — not built at launch)*

Reserved for when user accounts are added. Will store which opportunities a user has saved or viewed.

**SQL (do not run yet):**
```sql
CREATE TABLE validations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Notes:**
- This table is documented now so the schema design accounts for it
- Do not create this table until auth is implemented
- Will require a `user_id` column once auth is added

---

## Migration Order

Run migrations in this exact order:

```
1. Enable pgvector extension
2. Create consumer_signals table
3. Create consumer_signals indexes
4. Create keepalive table
```

Do not create the `validations` table until auth is implemented.

---

## Open Questions

| # | Question | Decision needed by |
|---|---|---|
| 1 | Will an `opportunities` table be needed? Depends on whether opportunity generation is on-demand or pre-generated | Step 3.2 |
| 2 | What is the exact structure of `pain_points` and `mentioned_features` JSONB? Will be determined by what Claude actually extracts during pipeline testing | Step 2.3 |
| 3 | What is the embedding vector dimension? Listed as 1536 (OpenAI text-embedding-3-small default) but embedding model is not yet confirmed | Step 2.3 |
