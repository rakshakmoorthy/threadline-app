# Threadline

> Threadline turns consumer frustration into product briefs before a brand runs a focus group.

---

## What is Threadline?

Threadline is a web application that helps product managers at adaptive fashion brands discover what to build next — grounded in real consumer signals from Reddit and Amazon.

A brand PM opens Threadline, selects a condition (post-mastectomy, ostomy, rheumatoid arthritis, or post-surgical recovery), and immediately sees:

- The **top ranked product opportunities** for that condition — surfaced from real consumer posts and reviews
- A **full product brief** for any opportunity — confirmed pain points, recommended materials, closures, sizing, and what to build first
- **Cross-condition overlap** — when the same unmet need appears across multiple conditions, Threadline flags it automatically

No focus groups. No guessing. No pre-formed idea required.

---

## Who is it for?

- **Product managers** at adaptive fashion brands (Tommy Hilfiger Adaptive, Silverts, Reboundwear, and others) who need to know what to build next before committing to a development cycle
- **Founders and startups** entering adaptive fashion for the first time who need to validate a market opportunity before investing in it
- **Design researchers and strategists** working with brands in this space

---

## Conditions covered at launch

| Condition | Data sources |
|---|---|
| Post-mastectomy / breast cancer recovery | r/breastcancer, r/mastectomy, r/BRCA + Amazon reviews |
| Ostomy | r/ostomy, r/CrohnsDisease, r/UlcerativeColitis + Amazon reviews |
| Rheumatoid arthritis / mobility limitations | r/rheumatoid, r/ChronicPain, r/arthritis + Amazon reviews |
| Post-surgical recovery (general) | r/PostOpRecovery, r/plasticsurgery + Amazon reviews |

---

## How it works

```
Reddit + Amazon
      ↓
Python scraper (runs weekly via GitHub Actions)
      ↓
Supabase — PostgreSQL + pgvector
      ↓
FastAPI backend (hybrid search + Claude API)
      ↓
React frontend (ranked opportunities → full product brief)
```

1. A weekly scraper pulls posts and reviews from Reddit and Amazon
2. Claude extracts pain points and product features from each record
3. OpenAI embeddings convert each record into a vector for semantic search
4. When a user selects a condition, the backend retrieves the most signal-rich opportunities
5. Claude synthesizes the signals into ranked product ideas and detailed briefs
6. The frontend displays everything — ranked list first, full brief on click

---

## Tech stack

| Layer | Tool |
|---|---|
| Database | Supabase (PostgreSQL + pgvector) |
| Backend | FastAPI (Python) |
| Frontend | React + Vite |
| Scraping | PRAW (Reddit), httpx + BeautifulSoup (Amazon) |
| AI — intelligence | Claude API (`claude-sonnet-4-6`) |
| AI — embeddings | OpenAI `text-embedding-3-small` |
| Hosting | Render (backend + static frontend) |
| Automation | GitHub Actions (weekly scraper + Supabase keepalive) |

---

## Repository structure

```
threadline-app/
├── README.md
├── .gitignore
├── docs/
│   ├── product/
│   │   ├── product_vision.md
│   │   ├── user_flow.md
│   │   └── feature_spec.md
│   ├── architecture/
│   │   ├── architecture_spec.md
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
├── backend/
├── frontend/
└── .github/
    └── workflows/
        ├── scraper.yml
        └── keepalive.yml
```

---

## Getting started

See [`docs/build/local_setup.md`](docs/build/local_setup.md) for full local setup instructions.

Quick version:

```bash
git clone https://github.com/rakshakmoorthy/threadline-app.git
cd threadline-app

# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd ../frontend
npm install
npm run dev
```

You will need the following environment variables — see `docs/build/local_setup.md` for details:

```
SUPABASE_URL=
SUPABASE_KEY=
CLAUDE_API_KEY=
OPENAI_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
```

---

## Documentation

| Document | What it covers |
|---|---|
| [`product_vision.md`](docs/product/product_vision.md) | What Threadline is, who it's for, and why it exists |
| [`user_flow.md`](docs/product/user_flow.md) | Full user experience from landing to output |
| [`feature_spec.md`](docs/product/feature_spec.md) | Every feature defined precisely |
| [`architecture_spec.md`](docs/architecture/architecture_spec.md) | System architecture and all technical decisions |
| [`data_schema.md`](docs/architecture/data_schema.md) | Full database schema |
| [`api_reference.md`](docs/architecture/api_reference.md) | Every API endpoint |
| [`prompt_library.md`](docs/data/prompt_library.md) | Every Claude prompt used in the system |
| [`data_sources.md`](docs/data/data_sources.md) | Every data source and why it was chosen |
| [`data_pipeline.md`](docs/data/data_pipeline.md) | How the scraper and pipeline work end to end |
| [`local_setup.md`](docs/build/local_setup.md) | How to run Threadline locally |
| [`deployment.md`](docs/build/deployment.md) | How to deploy to Render |
| [`github_actions.md`](docs/build/github_actions.md) | Scraper and keepalive workflow configuration |
| [`decisions_log.md`](docs/decisions_log.md) | Every major decision and its rationale |

---

## Status

Currently in active development. Data pipeline → backend → frontend, in that order.

---

## Author

Raksha Krishna Moorthy  
MS Information Systems, Northeastern University  
[github.com/rakshakmoorthy](https://github.com/rakshakmoorthy)
