from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv
import os
import time

load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

EMBEDDING_MODEL = "text-embedding-3-small"
BATCH_SIZE = 100


def generate_embedding(text: str) -> list | None:
    """Generate embedding for a single text."""
    try:
        response = openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text[:8000]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"  Embedding error: {e}")
        return None


def run():
    """Generate embeddings for all records with clean_text but no embedding."""
    print("Starting embedding pipeline (text-embedding-3-small)...")

    # Fetch records that have clean_text but no embedding
    result = supabase.table("consumer_signals")\
        .select("id, clean_text")\
        .not_.is_("clean_text", "null")\
        .is_("embedding", "null")\
        .execute()

    records = result.data
    print(f"Found {len(records)} records to embed")

    embedded = 0
    failed = 0

    for i, record in enumerate(records):
        clean_text = record.get("clean_text", "")

        if not clean_text:
            failed += 1
            continue

        embedding = generate_embedding(clean_text)

        if embedding:
            try:
                supabase.table("consumer_signals")\
                    .update({"embedding": embedding})\
                    .eq("id", record["id"])\
                    .execute()
                embedded += 1

                if embedded % 100 == 0:
                    print(f"  Embedded: {embedded} | Failed: {failed}")

                # Small delay to avoid rate limits
                if embedded % 500 == 0:
                    time.sleep(1)

            except Exception as e:
                print(f"  Save error: {e}")
                failed += 1
        else:
            failed += 1

    print(f"\nDone. Embedded: {embedded} | Failed: {failed}")


if __name__ == "__main__":
    run()