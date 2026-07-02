import httpx
import time
import random
from bs4 import BeautifulSoup
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime

# Load environment variables
load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ASINs to scrape — confirmed adaptive fashion products
ASINS = {
    "post_mastectomy": [
        "B078HMR63H",  # Front closure zip post-surgery bra (48k+ reviews)
        "B09P3JXYPG",  # Post surgical front closure bra
        "B09S3BQG16",  # Post-surgery zip front closure bra
    ],
    "post_surgical": [
        "B0F6N87HC4",  # Adaptive post-surgery underwear with side hooks
    ],
}

HEADERS_LIST = [
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    },
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xhtml;q=0.9,*/*;q=0.8",
    },
]


def get_reviews(asin: str, condition: str, pages: int = 5):
    """Scrape reviews for a given ASIN from Amazon."""
    reviews = []

    for page in range(1, pages + 1):
        url = f"https://www.amazon.com/product-reviews/{asin}/?pageNumber={page}&sortBy=recent"
        headers = random.choice(HEADERS_LIST)

        try:
            print(f"  Scraping ASIN {asin} page {page}...")
            response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)

            if response.status_code != 200:
                print(f"  Blocked on page {page} — status {response.status_code}")
                break

            soup = BeautifulSoup(response.text, "html.parser")
            review_divs = soup.find_all("div", {"data-hook": "review"})

            if not review_divs:
                print(f"  No reviews found on page {page} — may be blocked")
                break

            for div in review_divs:
                try:
                    # Extract review text
                    body = div.find("span", {"data-hook": "review-body"})
                    raw_text = body.get_text(strip=True) if body else ""

                    # Quality gate — minimum 20 words
                    if len(raw_text.split()) < 20:
                        continue

                    # Extract rating
                    rating_tag = div.find("i", {"data-hook": "review-star-rating"})
                    rating_text = rating_tag.get_text(strip=True) if rating_tag else ""
                    rating = float(rating_text.split()[0]) if rating_text else 0.0

                    # Extract date
                    date_tag = div.find("span", {"data-hook": "review-date"})
                    date_text = date_tag.get_text(strip=True) if date_tag else ""

                    # Extract review ID
                    review_id = div.get("id", "")
                    source_id = f"{asin}_{review_id}"

                    # Extract title
                    title_tag = div.find("a", {"data-hook": "review-title"})
                    title = title_tag.get_text(strip=True) if title_tag else ""

                    # Verified purchase check
                    verified_tag = div.find("span", {"data-hook": "avp-badge"})
                    is_verified = verified_tag is not None

                    reviews.append({
                        "source": "amazon",
                        "source_url": f"https://www.amazon.com/product-reviews/{asin}",
                        "source_id": source_id,
                        "condition": condition,
                        "raw_text": raw_text,
                        "pain_points": None,
                        "mentioned_features": None,
                        "sentiment": None,
                        "upvotes": 0,
                        "embedding": None,
                        "scraped_at": datetime.utcnow().isoformat(),
                    })

                except Exception as e:
                    print(f"  Error parsing review: {e}")
                    continue

            # Polite delay between pages — avoid getting blocked
            time.sleep(random.uniform(3, 6))

        except Exception as e:
            print(f"  Request failed on page {page}: {e}")
            break

    return reviews


def save_to_supabase(reviews: list):
    """Save reviews to Supabase, skipping duplicates."""
    saved = 0
    skipped = 0

    for review in reviews:
        try:
            # Upsert — skip if source_id already exists
            result = supabase.table("consumer_signals").upsert(
                review,
                on_conflict="source_id"
            ).execute()
            saved += 1
        except Exception as e:
            print(f"  Skipped duplicate or error: {e}")
            skipped += 1

    print(f"  Saved: {saved} | Skipped (duplicates): {skipped}")


def run():
    """Run the full Amazon scraping pipeline."""
    print("Starting Amazon scraper...")
    total = 0

    for condition, asins in ASINS.items():
        print(f"\nCondition: {condition}")
        for asin in asins:
            print(f" ASIN: {asin}")
            reviews = get_reviews(asin, condition, pages=5)
            print(f"  Found {len(reviews)} reviews")
            save_to_supabase(reviews)
            total += len(reviews)
            # Polite delay between products
            time.sleep(random.uniform(5, 10))

    print(f"\nDone. Total records processed: {total}")


if __name__ == "__main__":
    run()