import anthropic
import json
import re
from supabase import create_client
from dotenv import load_dotenv
import os
from datetime import datetime, timezone

load_dotenv("../.env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

CONDITIONS = ["post_mastectomy", "ostomy", "rheumatoid", "post_surgical"]

CONDITION_LABELS = {
    "post_mastectomy": "Post-mastectomy / breast cancer recovery",
    "ostomy": "Ostomy",
    "rheumatoid": "Rheumatoid arthritis / mobility limitations",
    "post_surgical": "Post-surgical recovery (general)",
}

SYNTHESIS_PROMPT = """You are a product intelligence analyst specializing in adaptive fashion.

You have been given consumer posts and reviews from people living with {condition_label}. Each record contains extracted pain points and product features.

Synthesize these into the top 5 ranked product opportunities for adaptive fashion brands.

Return ONLY a valid JSON array. Keep each field concise to fit within token limits.

[
  {{
    "title": "Specific product idea (max 10 words)",
    "score": 85,
    "confidence": "high",
    "pain_point_summary": "One line summary (max 20 words)",
    "brief": {{
      "confirmed_pain_points": ["pain point 1", "pain point 2", "pain point 3"],
      "recommended_features": ["feature 1", "feature 2", "feature 3"],
      "priority_features": ["priority 1", "priority 2", "priority 3"],
      "gaps": ["gap 1"]
    }},
    "evidence": [
      {{"source": "reddit", "excerpt": "Short quote (max 20 words)"}},
      {{"source": "amazon", "excerpt": "Short quote (max 20 words)"}}
    ]
  }}
]

Scoring: high=60+ signals, medium=20-59, low=under 20.

Consumer signals for {condition_label}:
{signals}
"""


def fetch_signals(condition: str, limit: int = 100) -> list:
    """Fetch extracted signals for a condition."""
    result = supabase.table("consumer_signals")\
        .select("id, source, raw_text, pain_points, mentioned_features, sentiment, upvotes")\
        .eq("condition", condition)\
        .not_.is_("pain_points", "null")\
        .order("upvotes", desc=True)\
        .limit(limit)\
        .execute()
    return result.data


def format_signals(signals: list) -> str:
    """Format signals for the prompt — keep concise."""
    formatted = []
    for i, s in enumerate(signals[:80]):
        pain = s.get("pain_points") or []
        features = s.get("mentioned_features") or []
        formatted.append(
            f"[{i+1}] {s.get('source','')} | "
            f"Pain: {'; '.join(pain[:2]) if pain else 'none'} | "
            f"Features: {'; '.join(features[:2]) if features else 'none'}"
        )
    return "\n".join(formatted)


def extract_json(text: str) -> list:
    """Extract JSON array from response text robustly."""
    # Try direct parse first
    try:
        return json.loads(text)
    except:
        pass

    # Try extracting from markdown code block
    try:
        match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except:
        pass

    # Try finding JSON array directly
    try:
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except:
        pass

    return []


def synthesise_condition(condition: str) -> list:
    """Run Claude Opus 4.8 synthesis for a condition."""
    print(f"  Fetching signals for {condition}...")
    signals = fetch_signals(condition)
    print(f"  Found {len(signals)} signals")

    if len(signals) < 5:
        print(f"  Not enough signals — skipping")
        return []

    formatted = format_signals(signals)
    condition_label = CONDITION_LABELS[condition]

    prompt = SYNTHESIS_PROMPT.format(
        condition_label=condition_label,
        signals=formatted
    )

    print(f"  Running Claude Opus 4.8 synthesis...")

    try:
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()
        opportunities = extract_json(response_text)

        if not opportunities:
            print(f"  Could not parse JSON response")
            print(f"  Response preview: {response_text[:200]}")
            return []

        print(f"  Generated {len(opportunities)} opportunities")
        return opportunities

    except Exception as e:
        print(f"  Synthesis error for {condition}: {e}")
        return []


def save_opportunities(opportunities: list, condition: str):
    """Save pre-generated opportunities to Supabase."""
    # Delete old opportunities for this condition first
    supabase.table("opportunities")\
        .delete()\
        .eq("condition", condition)\
        .execute()

    saved = 0
    for opp in opportunities:
        try:
            record = {
                "condition": condition,
                "conditions": [condition],
                "title": opp.get("title", ""),
                "score": opp.get("score", 0),
                "confidence": opp.get("confidence", "low"),
                "pain_point_summary": opp.get("pain_point_summary", ""),
                "brief": {
                    **opp.get("brief", {}),
                    "evidence": opp.get("evidence", [])
                },
                "signal_ids": [],
                "overlap": False,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            supabase.table("opportunities").insert(record).execute()
            saved += 1
        except Exception as e:
            print(f"  Save error: {e}")

    print(f"  Saved {saved} opportunities for {condition}")


def detect_overlap():
    """Flag opportunities that appear across multiple conditions."""
    print("\nDetecting cross-condition overlap...")

    result = supabase.table("opportunities")\
        .select("id, condition, title, score")\
        .execute()

    all_opps = result.data
    flagged = 0

    for i, opp1 in enumerate(all_opps):
        for opp2 in all_opps[i+1:]:
            if opp1["condition"] == opp2["condition"]:
                continue
            words1 = set(opp1["title"].lower().split())
            words2 = set(opp2["title"].lower().split())
            overlap = len(words1 & words2) / max(len(words1), len(words2))
            if overlap > 0.4:
                conditions = list(set([opp1["condition"], opp2["condition"]]))
                for opp_id in [opp1["id"], opp2["id"]]:
                    supabase.table("opportunities")\
                        .update({"overlap": True, "conditions": conditions})\
                        .eq("id", opp_id)\
                        .execute()
                flagged += 1

    print(f"  Flagged {flagged} opportunity pairs as cross-condition overlap")


def run():
    """Run the full synthesis pipeline for all conditions."""
    print("Starting synthesis pipeline (Claude Opus 4.8)...")
    print("This runs once a week — generating pre-built opportunities for instant load.\n")

    for condition in CONDITIONS:
        print(f"\nCondition: {CONDITION_LABELS[condition]}")
        opportunities = synthesise_condition(condition)
        if opportunities:
            save_opportunities(opportunities, condition)

    detect_overlap()
    print("\nSynthesis complete. Opportunities are ready for instant load.")


if __name__ == "__main__":
    run()
