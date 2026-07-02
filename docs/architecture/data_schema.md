# Threadline — Data Schema

**Version:** 2.0  
**Status:** Approved for build  
**Last updated:** July 2, 2026  

---

## Overview

This document defines the database schema for Threadline. The database is hosted on Supabase (PostgreSQL) with the pgvector extension enabled for semantic search.

---

## Database: Supabase (PostgreSQL + pgvector)

**Extension required:** `vector` (pgvector) — must be enabled before running migrations

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## Tables

---

### Table: `consumer_signals`

The core data table. Every Reddit post and Amazon review that passes the quality gate is stored here. This is the raw intelligence layer — everything Threadline knows about consumer needs lives here.

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
  clean_text TEXT,
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
| `source_id` | TEXT | Yes | Unique ID for deduplication |
| `condition` | TEXT | Yes | One of the four launch conditions |
| `raw_text` | TEXT | Yes | Original unmodified text |
| `clean_text` | TEXT | No | Cleaned text — HTML removed, salutations removed. Null until cleaning pipeline runs |
| `pain_points` | JSONB | No | Extracted pain points array — null until Haiku extraction runs |
| `mentioned_features` | JSONB | No | Product features mentioned — null until extraction runs |
| `sentiment` | TEXT | No | Overall sentiment — null until extraction runs |
| `upvotes` | INTEGER | No | Reddit upvotes or Amazon helpfulness votes |
| `embedding` | VECTOR(1536) | No | Semantic embedding — null until embedding pipeline runs |
| `scraped_at` | TIMESTAMP | Yes | When this record was fetched |
| `created_at` | TIMESTAMP | Yes | DB insert time — auto-set |

**Indexes:**
```sql
-- Fast lookup by condition (used in hybrid search)
CREATE INDEX idx_consumer_signals_condition ON consumer_signals(condition);

-- Fast deduplication check
CREATE INDEX idx_consumer_signals_source_id ON consumer_signals(source_id);

-- Vector similarity search (HNSW — recommended for pgvector)
CREATE INDEX idx_consumer_signals_embedding ON consumer_signals
USING hnsw (embedding vector_cosine_ops);
```

**Important caveat on HNSW + condition filtering:**
When combining HNSW vector search with a WHERE clause on `condition`, pgvector may return fewer rows than requested. Mitigation: enable `hnsw.iterative_scan` in the query session. This was introduced in pgvector 0.8.0.

**Pipeline order for each record:**
```
1. Scrape → raw_text saved, clean_text/pain_points/embedding all NULL
2. Clean  → clean_text populated
3. Extract (Haiku) → pain_points, mentioned_features, sentiment populated
4. Embed  → embedding populated
```

---

### Table: `opportunities`

Pre-generated weekly by Claude Opus 4.8 via the Batch API. This is what the frontend reads — users never wait for LLM generation, they read from this table instantly.

**SQL:**
```sql
CREATE TABLE opportunities (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  condition TEXT NOT NULL CHECK (condition IN (
    'post_mastectomy',
    'ostomy',
    'rheumatoid',
    'post_surgical'
  )),
  conditions TEXT[],
  title TEXT NOT NULL,
  score INTEGER NOT NULL CHECK (score >= 0 AND score <= 100),
  confidence TEXT NOT NULL CHECK (confidence IN ('high', 'medium', 'low')),
  pain_point_summary TEXT NOT NULL,
  brief JSONB NOT NULL,
  signal_ids UUID[],
  overlap BOOLEAN DEFAULT FALSE,
  generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Column definitions:**

| Column | Type | Required | Description |
|---|---|---|---|
| `id` | UUID | Yes | Unique opportunity ID |
| `condition` | TEXT | Yes | Primary condition this opportunity is for |
| `conditions` | TEXT[] | No | All conditions this applies to — used for overlap detection |
| `title` | TEXT | Yes | Product idea title (e.g. "Front-closure adaptive bra") |
| `score` | INTEGER | Yes | Signal strength 0–100 |
| `confidence` | TEXT | Yes | `high`, `medium`, or `low` |
| `pain_point_summary` | TEXT | Yes | One-line summary of top pain point |
| `brief` | JSONB | Yes | Full product brief — see structure below |
| `signal_ids` | UUID[] | No | IDs of consumer_signals that drove this opportunity |
| `overlap` | BOOLEAN | No | True if this opportunity appears across multiple conditions |
| `generated_at` | TIMESTAMP | Yes | When Opus generated this — auto-set |

**`brief` JSONB structure:**
```json
{
  "pain_points": [
    "Cannot fasten back closures with limited arm mobility",
    "Standard bras cause discomfort against surgical sites"
  ],
  "recommended_features": [
    "Front closure mechanism",
    "Soft fabric with no seams near surgical sites"
  ],
  "priority_features": [
    "Front closure",
    "Drain pocket compatibility"
  ],
  "gaps": [
    "Limited data on sizing preferences for asymmetric recovery"
  ],
  "evidence": [
    {
      "source": "reddit",
      "url": "https://www.reddit.com/r/breastcancer/...",
      "excerpt": "I struggled so much with back closures after my surgery..."
    },
    {
      "source": "amazon",
      "url": "https://www.amazon.com/dp/B078HMR63H",
      "excerpt": "This front closure bra was a lifesaver post-mastectomy..."
    }
  ]
}
```

**Indexes:**
```sql
-- Fast lookup by condition
CREATE INDEX idx_opportunities_condition ON opportunities(condition);

-- Fast lookup by score for ranking
CREATE INDEX idx_opportunities_score ON opportunities(score DESC);

-- Fast overlap queries
CREATE INDEX idx_opportunities_overlap ON opportunities(overlap);
```

**Important:** Old opportunities are replaced on each weekly run. Before inserting new opportunities, delete the previous week's records for that condition:
```sql
DELETE FROM opportunities WHERE condition = 'post_mastectomy';
```

---

### Table: `keepalive`

Prevents Supabase free tier from pausing after 7 days of inactivity. A GitHub Actions workflow inserts a row every 5 days.

**SQL:**
```sql
CREATE TABLE keepalive (
  id SERIAL PRIMARY KEY,
  pinged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Notes:**
- Never delete this table
- Rows older than 7 days are deleted on each ping run
- Table stays at ~5 rows maximum

---

### Table: `validations` *(future — not built at launch)*

Reserved for when user accounts are added.

```sql
-- DO NOT RUN YET
CREATE TABLE validations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  opportunity_id UUID NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Migration Order

Run in this exact order:

```
1. Enable pgvector extension
2. Create consumer_signals table
3. Create consumer_signals indexes
4. Create opportunities table
5. Create opportunities indexes
6. Create keepalive table
```

Do not create `validations` until auth is implemented.

---

## Schema Change from v1.0

| Change | Reason |
|---|---|
| Added `clean_text` to `consumer_signals` | Cleaning pipeline runs before extraction — store clean version separately from raw |
| Added `opportunities` table | Pre-generation approach confirmed — Opus generates weekly, users read instantly |
| Added indexes on `opportunities` | Fast lookup by condition, score, and overlap |

---

## Open Questions

| # | Question | Decision needed by |
|---|---|---|
| 1 | Embedding vector dimension — listed as 1536 (OpenAI text-embedding-3-small default) but model not yet confirmed | Step 2.5 |
| 2 | How many opportunities to pre-generate per condition? Top 10 is working assumption | Step 2.6 |
| 3 | Should old opportunities be deleted before inserting new ones, or versioned? | Step 2.6 |
