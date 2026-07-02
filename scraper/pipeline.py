"""
Threadline Weekly Pipeline
--------------------------
Runs every week via GitHub Actions.
Orchestrates the full data pipeline in correct order:

1. Scrape — Reddit RSS (hot posts)
2. Clean  — Remove HTML, noise, salutations
3. Extract — Claude Haiku extracts pain points + features
4. Embed  — OpenAI generates vectors
5. Synthesise — Claude Opus 4.8 generates ranked opportunities

Run manually: python3 pipeline.py
"""

import sys
from datetime import datetime

def log(msg):
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
    print('='*50)


def run_pipeline():
    print("\nThreadline Weekly Pipeline Starting...")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1 — Scrape Reddit
    log("Step 1/5 — Scraping Reddit (hot posts)")
    try:
        from reddit_scraper import run as scrape
        scrape()
    except Exception as e:
        print(f"Reddit scraper error: {e}")
        print("Continuing with existing data...")

    # Step 2 — Clean
    log("Step 2/5 — Cleaning records")
    try:
        from cleaner import run as clean
        clean()
    except Exception as e:
        print(f"Cleaner error: {e}")
        sys.exit(1)

    # Step 3 — Extract (Claude Haiku)
    log("Step 3/5 — Extracting pain points (Claude Haiku)")
    try:
        from extractor import run as extract
        extract()
    except Exception as e:
        print(f"Extractor error: {e}")
        sys.exit(1)

    # Step 4 — Embed
    log("Step 4/5 — Generating embeddings (OpenAI)")
    try:
        from embedder import run as embed
        embed()
    except Exception as e:
        print(f"Embedder error: {e}")
        sys.exit(1)

    # Step 5 — Synthesise (Claude Opus 4.8)
    log("Step 5/5 — Synthesising opportunities (Claude Opus 4.8)")
    try:
        from synthesiser import run as synthesise
        synthesise()
    except Exception as e:
        print(f"Synthesiser error: {e}")
        sys.exit(1)

    log("Pipeline Complete")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Opportunities are ready for instant load in Supabase.")


if __name__ == "__main__":
    run_pipeline()
