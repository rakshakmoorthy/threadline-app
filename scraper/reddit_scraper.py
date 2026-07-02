import httpx
import time
import random
import re
import xml.etree.ElementTree as ET
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

SUBREDDITS = {
    "post_mastectomy": ["breastcancer", "mastectomy", "BRCA"],
    "ostomy": ["ostomy", "CrohnsDisease", "UlcerativeColitis"],
    "rheumatoid": ["rheumatoid", "ChronicPain", "arthritis"],
    "post_surgical": ["PostOpRecovery", "plasticsurgery"],
}

KEYWORDS = [
    "clothes", "clothing", "wear", "wearing", "dress", "dressing",
    "bra", "shirt", "pants", "underwear", "garment", "outfit",
    "button", "zipper", "closure", "magnetic", "velcro",
    "fabric", "material", "comfortable", "uncomfortable",
    "adaptive", "accessible", "easy to put on", "hard to wear",
    "post surgery", "post-surgery", "recovery", "drain", "tube",
    "mastectomy bra", "front closure", "ostomy", "stoma",
    "arthritis", "mobility", "joint", "pain"
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
}


def is_relevant(text):
    text_lower = text.lower()
    return any(kw in text_lower for kw in KEYWORDS)


def strip_html(text):
    clean = re.sub(r"<[^>]+>", " ", text)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def fetch_subreddit_rss(subreddit, sort="new"):
    url = f"https://www.reddit.com/r/{subreddit}/{sort}/.rss"
    try:
        response = httpx.get(url, headers=HEADERS, timeout=15, follow_redirects=True)
        if response.status_code == 200:
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            root = ET.fromstring(response.text)
            entries = root.findall("atom:entry", ns)
            posts = []
            for entry in entries:
                title_el = entry.find("atom:title", ns)
                content_el = entry.find("atom:content", ns)
                link_el = entry.find("atom:link", ns)
                title_text = title_el.text if title_el is not None else ""
                content_text = strip_html(content_el.text if content_el is not None else "")
                link_url = link_el.get("href") if link_el is not None else ""
                post_id = ""
                if "/comments/" in link_url:
                    post_id = link_url.split("/comments/")[1].split("/")[0]
                posts.append({
                    "title": title_text,
                    "text": content_text,
                    "url": link_url,
                    "id": post_id or link_url,
                })
            return posts
        elif response.status_code == 429:
            print(f"  Rate limited — waiting 30s...")
            time.sleep(30)
            return []
        else:
            print(f"  Failed r/{subreddit} ({sort}): HTTP {response.status_code}")
            return []
    except Exception as e:
        print(f"  Error r/{subreddit}: {e}")
        return []


def process_posts(posts, condition, subreddit):
    records = []
    for post in posts:
        full_text = f"{post['title']}. {post['text']}".strip()
        if len(full_text.split()) < 20:
            continue
        if not is_relevant(full_text):
            continue
        records.append({
            "source": "reddit",
            "source_url": post["url"],
            "source_id": f"reddit_{post['id']}",
            "condition": condition,
            "raw_text": full_text,
            "pain_points": None,
            "mentioned_features": None,
            "sentiment": None,
            "upvotes": 0,
            "embedding": None,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })
    return records


def save_to_supabase(records):
    saved = 0
    skipped = 0
    for record in records:
        try:
            supabase.table("consumer_signals").upsert(
                record, on_conflict="source_id"
            ).execute()
            saved += 1
        except Exception:
            skipped += 1
    return saved, skipped


def run():
    print("Starting Reddit scraper (RSS)...")
    total_saved = 0

    for condition, subreddits in SUBREDDITS.items():
        print(f"\nCondition: {condition}")
        for subreddit in subreddits:
            print(f"  Scraping r/{subreddit}...")
            all_posts = []
            for sort in ["new", "hot", "top"]:
                posts = fetch_subreddit_rss(subreddit, sort)
                all_posts.extend(posts)
                time.sleep(random.uniform(2, 4))
            records = process_posts(all_posts, condition, subreddit)
            print(f"  Found {len(records)} relevant posts")
            if records:
                saved, skipped = save_to_supabase(records)
                total_saved += saved
                print(f"  Saved: {saved} | Skipped: {skipped}")
            time.sleep(random.uniform(3, 6))

    print(f"\nDone. Total Reddit records saved: {total_saved}")


if __name__ == "__main__":
    run()
