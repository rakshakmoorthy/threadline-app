import urllib.request
import gzip
import json
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Keywords mapped to conditions
CONDITION_KEYWORDS = {
    "post_mastectomy": [
        "mastectomy", "post surgery bra", "post-surgery bra",
        "drain pocket", "surgical bra", "breast surgery",
        "breast reconstruction", "breast augmentation recovery",
        "lumpectomy", "front closure bra", "post op bra"
    ],
    "ostomy": [
        "ostomy", "colostomy", "ileostomy", "urostomy",
        "stoma", "ostomy bag", "colostomy bag"
    ],
    "rheumatoid": [
        "rheumatoid", "arthritis", "joint pain", "mobility",
        "adaptive clothing", "adaptive fashion", "easy to put on",
        "magnetic closure", "velcro closure", "easy closure"
    ],
    "post_surgical": [
        "post surgery", "post-surgery", "after surgery",
        "recovery clothing", "surgical recovery", "post op",
        "drain tube", "wound care clothing"
    ]
}

# Dataset URLs to process
DATASETS = [
    {
        "url": "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Clothing_Shoes_and_Jewelry.jsonl.gz",
        "name": "Clothing_Shoes_and_Jewelry"
    },
    {
        "url": "https://mcauleylab.ucsd.edu/public_datasets/data/amazon_2023/raw/review_categories/Health_and_Household.jsonl.gz",
        "name": "Health_and_Household"
    }
]

# Maximum records to check per dataset
MAX_RECORDS_PER_DATASET = 500000

# Minimum word count for quality gate
MIN_WORDS = 20


def detect_condition(text: str) -> str | None:
    """Detect which condition a review relates to."""
    text_lower = text.lower()
    for condition, keywords in CONDITION_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return condition
    return None


def passes_quality_gate(text: str, rating: float) -> bool:
    """Check if a review meets minimum quality standards."""
    if len(text.split()) < MIN_WORDS:
        return False
    if not rating:
        return False
    return True


def save_to_supabase(records: list):
    """Save records to Supabase, skipping duplicates."""
    saved = 0
    skipped = 0
    for record in records:
        try:
            supabase.table("consumer_signals").upsert(
                record,
                on_conflict="source_id"
            ).execute()
            saved += 1
        except Exception as e:
            skipped += 1
    return saved, skipped


def process_dataset(url: str, name: str):
    """Stream and filter a dataset, saving matches to Supabase."""
    print(f"\nProcessing: {name}")
    print(f"URL: {url}")

    checked = 0
    matched = 0
    saved_total = 0
    batch = []
    batch_size = 50

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            with gzip.GzipFile(fileobj=response) as f:
                for line in f:
                    try:
                        record = json.loads(line.decode("utf-8"))
                        checked += 1

                        text = record.get("text") or ""
                        rating = record.get("rating")
                        asin = record.get("asin") or ""
                        review_id = record.get("review_id") or record.get("reviewerID") or str(checked)

                        # Quality gate
                        if not passes_quality_gate(text, rating):
                            continue

                        # Condition detection
                        condition = detect_condition(text)
                        if not condition:
                            continue

                        matched += 1

                        # Build record for Supabase
                        supabase_record = {
                            "source": "amazon",
                            "source_url": f"https://www.amazon.com/dp/{asin}",
                            "source_id": f"{asin}_{review_id}",
                            "condition": condition,
                            "raw_text": text,
                            "pain_points": None,
                            "mentioned_features": None,
                            "sentiment": None,
                            "upvotes": int(record.get("helpful_vote") or 0),
                            "embedding": None,
                            "scraped_at": datetime.utcnow().isoformat(),
                        }

                        batch.append(supabase_record)

                        # Save in batches
                        if len(batch) >= batch_size:
                            saved, skipped = save_to_supabase(batch)
                            saved_total += saved
                            print(f"  Checked: {checked} | Matched: {matched} | Saved: {saved_total}")
                            batch = []

                        if checked >= MAX_RECORDS_PER_DATASET:
                            break

                    except Exception as e:
                        continue

        # Save remaining batch
        if batch:
            saved, skipped = save_to_supabase(batch)
            saved_total += saved

    except Exception as e:
        print(f"  Error processing dataset: {e}")

    print(f"\n  Done — Checked: {checked} | Matched: {matched} | Saved to Supabase: {saved_total}")
    return saved_total


def run():
    """Run the full Hugging Face loader pipeline."""
    print("Starting Hugging Face data loader...")
    print(f"Target: {MAX_RECORDS_PER_DATASET:,} records per dataset")
    total = 0

    for dataset in DATASETS:
        saved = process_dataset(dataset["url"], dataset["name"])
        total += saved

    print(f"\nComplete. Total records saved to Supabase: {total}")


if __name__ == "__main__":
    run()