# Threadline — Technical Architecture Specification

**Version:** 2.0 (full rewrite)  
**Status:** Approved for build  
**Last updated:** July 1, 2026  
**Author:** Raksha Krishna Moorthy  

---

## 1. Product Overview

Threadline is an AI-powered market intelligence web application for the adaptive fashion market.

A user selects one or more conditions and immediately sees ranked product opportunities grounded in real consumer signals from Reddit and Amazon. They click any opportunity to get a full product brief — confirmed pain points, recommended features, priority order, gaps, and source evidence.

No pre-formed idea required. No focus group. No waiting.

**Target conditions at launch:**
- Post-mastectomy / breast cancer recovery
- Ostomy
- Rheumatoid arthritis / mobility limitations
- Post-surgical recovery (general)

**Target user:** Product managers at adaptive fashion brands who need to know what to build next.

---

## 2. System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      DATA LAYER                         │
│                                                         │
│  Reddit API (PRAW)     Amazon (HTTP scraper)            │
│       ↓                        ↓                        │
│       └────────────────────────┘                        │
│                     ↓                                   │
│           Python scraper pipeline                       │
│           (extraction + embedding)                      │
│                     ↓                                   │
│        GitHub Actions (weekly cron)                     │
│                     ↓                                   │
│         Supabase — PostgreSQL + pgvector                │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                   BACKEND LAYER                         │
│                                                         │
│             FastAPI (Python) on Render                  │
│                                                         │
│  • Receives condition selection from frontend           │
│  • Queries Supabase for relevant consumer signals       │
│  • Calls Claude API to generate opportunities + briefs  │
│  • Returns ranked opportunities + full briefs           │
│  • Claude API key lives here and only here              │
└─────────────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND LAYER                         │
│                                                         │
│        React (Vite) — Render static site                │
│                                                         │
│  • Brief explanation + condition selector               │
│  • Multi-condition selection                            │
│  • Ranked opportunity cards                             │
│  • Cross-condition overlap flagging                     │
│  • Full product brief                                   │
│  • Navigation between brief and ranked list             │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Architecture Decisions (with justification)

### 3.1 Why a Backend (FastAPI)?

**Decision:** Build a FastAPI backend rather than calling Claude API directly from React.

**Reason:** Calling the Claude API from a React frontend exposes the API key to anyone who opens browser dev tools. For a product being shown to industry contacts and potential employers, this is a real security problem. FastAPI protects the key and gives a clean API contract between frontend and backend.

**Tradeoff:** More to build and host — worth it.

### 3.2 Search Strategy — Hybrid (Condition Filter + Semantic Search)

**Decision:** Filter by condition first, then run semantic/vector search within that subset.

**Reason:**
- Pure keyword search misses meaning — "difficulty dressing post-surgery" and "can't get clothes on after operation" describe the same need but share no keywords
- Pure semantic search across all records is slower and noisier without filtering
- Hybrid gives the best results: condition narrows the pool, vector search finds the most relevant signals within it

**Implementation:** pgvector is included in all Supabase plans including free, at no extra cost. Each consumer record gets an embedding at ingestion. At query time, the condition filters the records and vector similarity finds the most relevant ones within that subset.

### 3.3 Opportunity Generation — Open Question

**Decision:** Not yet decided whether ranked opportunities are generated on demand by Claude when a user selects a condition, or pre-generated during the scrape pipeline and stored in the database.

**Tradeoffs:**

| Approach | Pros | Cons |
|---|---|---|
| On demand (Claude at query time) | Always reflects latest data; no pre-generation needed | Slower response; higher Claude API cost per request |
| Pre-generated (Claude at scrape time) | Fast response for user; lower real-time cost | Stale until next scrape; more complex pipeline |

**Decision needed by:** Backend build — Step 3.2.

### 3.4 Data Freshness — Weekly Scrape

**Decision:** Weekly automated scrape via GitHub Actions cron job.

**Reason:**
- Adaptive fashion consumer conversations do not change daily — weekly is fresh enough
- Daily scraping risks Reddit rate limits and potential bans
- GitHub Actions is completely free for public repositories

**Critical constraint:** GitHub Actions automatically disables scheduled workflows after 60 days of repository inactivity. Mitigation: ensure at least one repo commit every 60 days, and always include `workflow_dispatch` so the pipeline can be triggered manually.

### 3.5 API Key Security

**Decision:** Claude API key lives in the FastAPI backend only, stored as an environment variable in Render's dashboard.

**Never in:**
- Frontend code
- GitHub repository
- `.env` files committed to git

`.gitignore` excludes `.env` from day one.

### 3.6 Supabase Inactivity Pause — Verified Mitigation

**Risk:** Free tier projects pause after exactly 7 days of zero database activity. The timer tracks actual database queries — not API calls, not dashboard visits.

**Correct mitigation:** A GitHub Actions workflow runs every 5 days and inserts a row into a dedicated `keepalive` table. This resets the inactivity timer. Rows older than 7 days are deleted on each run to keep the table small.

**Important:** Pinging a health endpoint does NOT reset the timer. Only actual database activity does.

### 3.7 Render Cold Start — Verified Behavior

**Risk:** FastAPI backend on Render free tier spins down after 15 minutes of inactivity. Cold start takes approximately 1 minute — unacceptable for a live demo.

**Mitigation:**
- During development: accept cold starts
- Before any demo: either upgrade to Render Starter ($7/mo) or add a keep-alive ping every 10 minutes via GitHub Actions or a free Uptime Robot monitor

**Frontend (static site) is not affected** — Render static sites have no spin-down and are free permanently.

### 3.8 Embedding Model — Open Question

**Decision:** Not yet decided. OpenAI `text-embedding-3-small` is the working assumption but has not been confirmed.

**Decision needed by:** Step 2.3 (embedding pipeline build).

### 3.9 One Repository

**Decision:** One repository (`threadline-app`) for everything — scraper, backend, frontend, docs, and GitHub Actions workflows.

**Reason:** Simpler to manage, easier to deploy, appropriate for this project size. Separate repos add complexity with no real benefit at this stage.

---

## 4. Database Schema

### Table: `consumer_signals`

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique record ID |
| `source` | TEXT | `reddit` or `amazon` |
| `source_url` | TEXT | Original post/review URL |
| `source_id` | TEXT | Reddit post ID or ASIN + review ID (used for deduplication) |
| `condition` | TEXT | `post_mastectomy`, `ostomy`, `rheumatoid`, `post_surgical` |
| `raw_text` | TEXT | Original post/review text |
| `pain_points` | JSONB | Extracted pain points array |
| `mentioned_features` | JSONB | Product features mentioned in the text |
| `sentiment` | TEXT | `positive`, `negative`, `mixed` |
| `upvotes` | INTEGER | Reddit upvotes or Amazon helpfulness votes |
| `embedding` | VECTOR(1536) | Semantic embedding for vector search |
| `scraped_at` | TIMESTAMP | When this record was collected |
| `created_at` | TIMESTAMP | DB insert time |

### Table: `keepalive`

| Column | Type | Description |
|---|---|---|
| `id` | SERIAL (PK) | Auto-increment |
| `pinged_at` | TIMESTAMP | When the ping ran |

Rows older than 7 days are deleted on each ping run. Table stays small (~5 rows max).

### Table: `opportunities` *(if pre-generation approach is chosen)*

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique opportunity ID |
| `condition` | TEXT | Primary condition |
| `conditions` | TEXT[] | All conditions this opportunity applies to |
| `title` | TEXT | Product idea title |
| `score` | INTEGER | Signal strength score 0–100 |
| `confidence` | TEXT | `high`, `medium`, `low` |
| `pain_point_summary` | TEXT | One-line top pain point summary |
| `brief` | JSONB | Full product brief |
| `signal_ids` | UUID[] | Which consumer_signals drove this opportunity |
| `generated_at` | TIMESTAMP | When this opportunity was generated |

*Note: This table is only needed if opportunities are pre-generated. If generated on demand, this table is not required.*

### Table: `validations` *(future — for when auth is added)*

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique validation ID |
| `opportunity_id` | UUID | Which opportunity was viewed |
| `created_at` | TIMESTAMP | When this was saved |

---

## 5. API Design (FastAPI)

### `POST /opportunities`

Called when a user selects one or more conditions and requests ranked opportunities.

**Request:**
```json
{
  "conditions": ["post_mastectomy", "ostomy"]
}
```

**Response:**
```json
{
  "opportunities": [
    {
      "id": "uuid",
      "title": "Front-closure adaptive top",
      "score": 87,
      "confidence": "high",
      "pain_point_summary": "Consumers cannot fasten standard closures post-surgery",
      "conditions": ["post_mastectomy", "post_surgical"],
      "overlap": true
    },
    {
      "id": "uuid",
      "title": "High-waist adaptive trousers",
      "score": 74,
      "confidence": "medium",
      "pain_point_summary": "Standard waistbands are incompatible with ostomy pouches",
      "conditions": ["ostomy"],
      "overlap": false
    }
  ],
  "total": 2,
  "generated_at": "2026-07-01T12:00:00Z"
}
```

### `GET /opportunities/{id}/brief`

Called when a user clicks an opportunity card to see the full brief.

**Response:**
```json
{
  "id": "uuid",
  "title": "Front-closure adaptive top",
  "score": 87,
  "confidence": "high",
  "conditions": ["post_mastectomy", "post_surgical"],
  "overlap": true,
  "pain_points": [
    "Cannot fasten back closures with limited arm mobility",
    "Standard bras cause discomfort against surgical sites"
  ],
  "recommended_features": [
    "Front closure",
    "Soft fabric with no seams near surgical sites"
  ],
  "priority_features": [
    "Front closure mechanism",
    "Drain pocket compatibility"
  ],
  "gaps": [
    "Limited data on sizing preferences for asymmetric recovery"
  ],
  "evidence": [
    {
      "source": "reddit",
      "url": "https://reddit.com/r/breastcancer/...",
      "excerpt": "...",
      "relevance_score": 0.91
    }
  ],
  "signal_count": 34
}
```

### `GET /health`
Returns API status. Used by keep-alive ping and for debugging.

### `GET /conditions`
Returns the list of supported conditions.

---

## 6. Data Pipeline Design

### Sources

| Source | Method | Library | Rate limit strategy |
|---|---|---|---|
| Reddit | PRAW (official API) | `praw` | Stay within 60 req/min; scrape one subreddit at a time with delays |
| Amazon | HTTP scraper | `httpx` + `BeautifulSoup` | Rotate user agents; add delays; use product ASINs. Amazon aggressively blocks scrapers — see Open Question #3 |

### Target Subreddits (launch)

| Condition | Subreddits |
|---|---|
| Post-mastectomy | r/breastcancer, r/mastectomy, r/BRCA |
| Ostomy | r/ostomy, r/CrohnsDisease, r/UlcerativeColitis |
| Rheumatoid | r/rheumatoid, r/ChronicPain, r/arthritis |
| Post-surgical | r/PostOpRecovery, r/plasticsurgery |

### Target Amazon Categories (launch)
- Post-surgery adaptive clothing
- Front closure garments
- Ostomy adaptive wear
- Adaptive clothing (general)

### Pipeline Steps

```
1. Fetch raw posts/reviews from Reddit + Amazon
2. Filter for relevance (clothing, dressing, adaptive keywords)
3. Extract pain points + features via Claude API
4. Generate embedding (model TBD — see Open Question #2)
5. Quality gate (minimum text length, relevance score threshold)
6. Upsert to Supabase — skip duplicates using source_id
```

### Schedule

| Workflow | Trigger | Purpose |
|---|---|---|
| `scraper.yml` | Weekly cron — Sunday 2am UTC + `workflow_dispatch` | Full scrape of all sources |
| `keepalive.yml` | Every 5 days + `workflow_dispatch` | Insert row into Supabase keepalive table |

**Keep repo public** — GitHub Actions is completely free and unlimited for public repositories.

---

## 7. Claude Prompt Design

Claude is used in two places:

**1. During the scrape pipeline (extraction)**
Claude reads each raw post/review and extracts structured pain points and product features. This runs once per record at ingestion time.

**2. During opportunity generation (synthesis)**
Claude reads a set of relevant consumer signals and synthesises them into ranked product opportunities and full briefs. This runs either at scrape time (pre-generation) or at query time (on demand) — see Open Question #1.

**Brief structure Claude returns:**
- Confirmed pain points
- Recommended product features (categories determined by what the data surfaces)
- Priority features (what to build first)
- Gaps (what the data does not yet tell us)

**Scoring logic:**

| Score | Signal strength |
|---|---|
| 0–30 | Weak — few mentions, contradictory or thin data |
| 31–60 | Moderate — some pain points confirmed |
| 61–80 | Strong — clear pain points, consistent feature signals |
| 81–100 | Very strong — high volume, consistent, specific |

---

## 8. Hosting Stack (verified pricing)

| Layer | Service | Plan | Verified cost |
|---|---|---|---|
| Database | Supabase | Free | $0 |
| Vector search | Supabase pgvector | Included in all plans | $0 |
| Backend | Render web service | Free (cold starts) → Starter before demos | $0 → $7/mo |
| Frontend | Render static site | Free, no spin-down, permanent | $0 |
| Scraper + keepalive | GitHub Actions | Free for public repos | $0 |
| AI — synthesis | Claude API (`claude-sonnet-4-6`) | Pay per token | ~$1–5/mo |
| AI — embeddings | TBD | Pay per token | ~$0.50/mo |
| **Total (development)** | | | **~$1.50–5.50/mo** |
| **Total (demo-ready)** | | | **~$8.50–12.50/mo** |

---

## 9. Build Order

```
Phase 1 — Foundation
  Step 1.1  Set up Supabase project + enable pgvector + run schema migrations
  Step 1.2  Set up GitHub repo (public) + folder structure
  Step 1.3  Set up environment variable management

Phase 2 — Data Pipeline
  Step 2.1  Build Reddit scraper (PRAW)
  Step 2.2  Build Amazon scraper (resolve approach — see Open Question #3)
  Step 2.3  Build extraction + embedding pipeline (Claude + embedding model TBD)
  Step 2.4  Load initial dataset — target 200+ verified records
  Step 2.5  Set up GitHub Actions: scraper.yml + keepalive.yml
  Step 2.6  Verify data and embeddings in Supabase dashboard

Phase 3 — Backend
  Step 3.1  Set up FastAPI project structure
  Step 3.2  Build /opportunities endpoint
  Step 3.3  Build /opportunities/{id}/brief endpoint
  Step 3.4  Build /health and /conditions endpoints
  Step 3.5  Test locally with curl or Postman
  Step 3.6  Deploy to Render

Phase 4 — Frontend
  Step 4.1  Set up React (Vite) project
  Step 4.2  Build landing page + condition selector
  Step 4.3  Build ranked opportunity cards
  Step 4.4  Build cross-condition overlap flagging
  Step 4.5  Build full product brief
  Step 4.6  Build navigation between brief and ranked list
  Step 4.7  Deploy to Render (static site)

Phase 5 — Polish + Documentation
  Step 5.1  Error states + loading states
  Step 5.2  Mobile responsiveness
  Step 5.3  Add backend keep-alive before demos
  Step 5.4  README + living code docs
  Step 5.5  Full demo run-through
```

---

## 10. Repository Structure

```
threadline-app/                         ← public GitHub repo
├── README.md
├── .gitignore
├── docs/
│   ├── product/
│   │   ├── product_vision.md
│   │   ├── user_flow.md
│   │   └── feature_spec.md
│   ├── architecture/
│   │   ├── architecture_spec.md        ← this document
│   │   ├── data_schema.md
│   │   └── api_reference.md
│   ├── data/
│   │   ├── data_sources.md
│   │   ├── data_pipeline.md
│   │   └── prompt_library.md
│   ├── build/
│   │   ├── local_setup.md
│   │   ├── deployment.md
│   │   └── github_actions.md
│   └── decisions_log.md
├── scraper/
│   ├── reddit_scraper.py
│   ├── amazon_scraper.py
│   ├── extractor.py
│   ├── embedder.py
│   ├── pipeline.py
│   └── requirements.txt
├── backend/
│   ├── main.py
│   ├── routes/
│   │   ├── opportunities.py
│   │   ├── health.py
│   │   └── conditions.py
│   ├── services/
│   │   ├── supabase_client.py
│   │   └── claude_client.py
│   ├── prompts/
│   │   ├── extraction_prompt.py
│   │   └── synthesis_prompt.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── ConditionSelector.jsx
│   │   │   ├── OpportunityCard.jsx
│   │   │   ├── OpportunityList.jsx
│   │   │   ├── ProductBrief.jsx
│   │   │   └── EvidencePanel.jsx
│   │   └── api/
│   │       └── threadline.js
│   ├── index.html
│   └── package.json
└── .github/
    └── workflows/
        ├── scraper.yml
        └── keepalive.yml
```

---

## 11. Open Questions

| # | Question | Decision needed by |
|---|---|---|
| 1 | Are opportunities generated on demand (Claude at query time) or pre-generated at scrape time? | Step 3.2 |
| 2 | Which embedding model? OpenAI text-embedding-3-small is the working assumption | Step 2.3 |
| 3 | Amazon scraping approach — direct HTTP or a paid scraping API? Amazon aggressively blocks scrapers | Step 2.2 |
| 4 | Minimum record count before app produces reliable opportunities? | Step 2.4 |
| 5 | Backend keep-alive strategy before demos — Uptime Robot or GitHub Actions ping? | Step 5.3 |
| 6 | Does the brief open as a new page or an expanded panel on the same page? | Step 4.5 |
| 7 | How many opportunity cards shown by default — all or top N with show more? | Step 4.3 |
| 8 | Do results load immediately on condition selection or after clicking a button? | Step 4.2 |
| 9 | What signal volume thresholds define High / Medium / Low confidence? | Step 3.2 |

---

## 12. Key Decisions Summary

Full rationale for every decision is in [`decisions_log.md`](../decisions_log.md). Summary:

| Decision | What was decided |
|---|---|
| Backend required | FastAPI protects Claude API key from frontend exposure |
| Hybrid search | Condition filter + vector search gives best signal quality |
| Weekly scrape | Free on public repos; sufficient freshness for this market |
| Render for hosting | Predictable cost; free static hosting; no usage surprises |
| No auth at launch | Reduce scope; DB schema is auth-ready for later |
| One repo | Simpler to manage at this project size |
| Supabase keepalive | Insert DB row every 5 days — health endpoint ping does not work |
| Render cold start | 15-min spin-down; upgrade to Starter ($7/mo) before demos |
| GitHub Actions inactivity | Scheduled workflows disable after 60 days of repo inactivity |
| Public repo | Unlimited free Actions minutes on public repos |
