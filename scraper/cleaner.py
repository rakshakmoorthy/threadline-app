import re
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# Salutations and noise phrases to remove
NOISE_PHRASES = [
    "hi everyone", "hi all", "hello everyone", "hello all",
    "hey everyone", "hey all", "hi there", "hello there",
    "thanks for reading", "thank you for reading",
    "thanks in advance", "thank you in advance",
    "sorry for the long post", "sorry if this is long",
    "long post sorry", "tl;dr", "tldr",
    "edit:", "update:", "edited to add",
    "first time posting", "first post here",
    "not sure if this is the right place",
    "hope this helps", "hope that helps",
]


def clean_text(text: str) -> str:
    """Clean raw text for LLM extraction."""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove URLs
    text = re.sub(r"http\S+|www\.\S+", "", text)

    # Remove Reddit formatting
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)        # italic
    text = re.sub(r"~~(.+?)~~", r"\1", text)         # strikethrough
    text = re.sub(r"#{1,6}\s", "", text)             # headers
    text = re.sub(r">\s?.+", "", text)               # blockquotes
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)  # links

    # Remove noise phrases (case insensitive)
    for phrase in NOISE_PHRASES:
        text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)

    # Remove excessive whitespace and newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s{2,}", " ", text)
    text = text.strip()

    return text


def run():
    """Clean all records in consumer_signals that don't have clean_text yet."""
    print("Starting cleaning pipeline...")

    # Fetch records without clean_text
    result = supabase.table("consumer_signals")\
        .select("id, raw_text")\
        .is_("clean_text", "null")\
        .execute()

    records = result.data
    print(f"Found {len(records)} records to clean")

    cleaned = 0
    skipped = 0

    for record in records:
        raw = record.get("raw_text", "")
        cleaned_text = clean_text(raw)

        # Skip if cleaned text is too short
        if len(cleaned_text.split()) < 15:
            skipped += 1
            continue

        try:
            supabase.table("consumer_signals")\
                .update({"clean_text": cleaned_text})\
                .eq("id", record["id"])\
                .execute()
            cleaned += 1

            if cleaned % 100 == 0:
                print(f"  Cleaned: {cleaned} | Skipped: {skipped}")

        except Exception as e:
            print(f"  Error on {record['id']}: {e}")
            skipped += 1

    print(f"\nDone. Cleaned: {cleaned} | Skipped: {skipped}")


if __name__ == "__main__":
    run()