import anthropic
import json
from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

EXTRACTION_PROMPT = """You are analyzing a consumer review or post about adaptive fashion and clothing needs.

Extract the following from the text:
1. pain_points: specific problems or frustrations mentioned about clothing or dressing
2. mentioned_features: specific product features mentioned or desired (closures, materials, sizing, etc.)
3. sentiment: overall sentiment toward the topic (positive, negative, or mixed)

Return ONLY a JSON object with this exact structure, no other text:
{
  "pain_points": ["pain point 1", "pain point 2"],
  "mentioned_features": ["feature 1", "feature 2"],
  "sentiment": "positive" | "negative" | "mixed"
}

If no pain points or features are found, return empty arrays.
Text to analyze:
"""


def extract_from_text(text: str) -> dict | None:
    """Extract pain points and features using Claude Haiku."""
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT + text[:2000]
                }
            ]
        )

        response_text = message.content[0].text.strip()

        # Clean JSON if wrapped in markdown
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        result = json.loads(response_text)

        # Validate structure
        if not isinstance(result.get("pain_points"), list):
            result["pain_points"] = []
        if not isinstance(result.get("mentioned_features"), list):
            result["mentioned_features"] = []
        if result.get("sentiment") not in ["positive", "negative", "mixed"]:
            result["sentiment"] = "mixed"

        return result

    except Exception as e:
        print(f"  Extraction error: {e}")
        return None


def run():
    """Run extraction on all records with clean_text but no pain_points."""
    print("Starting extraction pipeline (Claude Haiku)...")

    # Fetch records that have clean_text but no pain_points yet
    result = supabase.table("consumer_signals")\
        .select("id, clean_text, condition")\
        .not_.is_("clean_text", "null")\
        .is_("pain_points", "null")\
        .execute()

    records = result.data
    print(f"Found {len(records)} records to extract")

    extracted = 0
    failed = 0

    for i, record in enumerate(records):
        clean_text = record.get("clean_text", "")

        if not clean_text or len(clean_text.split()) < 15:
            failed += 1
            continue

        result_data = extract_from_text(clean_text)

        if result_data:
            try:
                supabase.table("consumer_signals")\
                    .update({
                        "pain_points": result_data["pain_points"],
                        "mentioned_features": result_data["mentioned_features"],
                        "sentiment": result_data["sentiment"]
                    })\
                    .eq("id", record["id"])\
                    .execute()
                extracted += 1

                if extracted % 50 == 0:
                    print(f"  Extracted: {extracted} | Failed: {failed}")

            except Exception as e:
                print(f"  Save error on {record['id']}: {e}")
                failed += 1
        else:
            failed += 1

    print(f"\nDone. Extracted: {extracted} | Failed: {failed}")


if __name__ == "__main__":
    run()