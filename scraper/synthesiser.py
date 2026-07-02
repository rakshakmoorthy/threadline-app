import anthropic
import json
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

You have been given a collection of real consumer posts and reviews from people living with {condition_label}. Each record contains extracted pain points and product features that consumers mentioned.

Your task is to synthesize these signals into the top 10 ranked product opportunities for adaptive fashion brands.

For each opportunity, provide:
1. A specific, actionable product idea title (e.g. "Front-closure adaptive bra with drain pocket")
2. A signal strength score (0-100) based on how many records support this opportunity and how strongly
3. A confidence level: "high" (60+ supporting signals), "medium" (20-59), or "low" (under 20)
4. A one-line pain point summary
5. A full product brief with:
   - confirmed_pain_points: list of specific pain points this addresses
   - recommended_features: list of specific features consumers want
   - priority_features: top 3 features to build first
   - gaps: what the data doesn't tell us yet
6. Sample evidence: 3 short excerpts from real consumer posts that support this opportunity

Return ONLY a valid JSON array with exactly this structure, no other text:
[
  {{
    "title": "Product idea title",
    "score": 85,
    "confidence": "high",
    "pain_point_summary": "One line summary of main pain point",
    "brief": {{
      "confirmed_pain_points": ["pain point 1", "pain point 2"],
      "recommended_features": ["feature 1", "feature 2"],
      "priority_features": ["priority 1", "priority 2", "priority 3"],
      "gaps": ["gap 1"]
    }},
    "evidence": [
      {{"source": "reddit", "excerpt": "short quote from consumer post"}},
      {{"source": "amazon", "excerpt": "short quote from review"}}
    ]
  }}
]

Consumer signals for {condition_label}:
{signals}
"""


def fetch_signals(condition: str, limit: int = 200) -> list:
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
    """Format signals for the prompt."""
    formatted = []
    for i, s in enumerate(signals[:150]):
        pain = s.get("pain_points") or []
        features = s.get("mentioned_features") or []
        text = s.get("raw_text", "")[:300]
        formatted.append(
            f"Record {i+1} ({s.get('source', '')}, upvotes: {s.get('upvotes', 0)}):\n"
            f"Text: {text}\n"
            f"Pain points: {', '.join(pain) if pain else 'none'}\n"
            f"Features mentioned: {', '.join(features) if features else 'none'}\n"
        )
    return "\n---\n".join(formatted)


def synthesise_condition(condition: str) -> list:
    """Run Claude Opus 4.8 synthesis for a condition."""
    print(f"  Fetching signals for {condition}...")
    signals = fetch_signals(condition)
    print(f"  Found {len(signals)} signals")

    if len(signals) < 10:
        print(f"  Not enough signals for {condition} — skipping")
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
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text.strip()

        # Clean JSON if wrapped in markdown
        if "```" in response_text:
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
                response_text = response_text[4:]

        opportunities = json.loads(response_text)
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
                "brief": opp.get("brief", {}),
                "signal_ids": [],
                "overlap": False,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Add evidence to brief
            record["brief"]["evidence"] = opp.get("evidence", [])

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

    # Find similar titles across conditions
    from collections import defaultdict
    title_map = defaultdict(list)

    for opp in all_opps:
        # Normalize title for comparison
        key_words = set(opp["title"].lower().split())
        for existing_key, existing_opps in title_map.items():
            existing_words = set(existing_key.split())
            overlap = len(key_words & existing_words) / max(len(key_words), len(existing_words))
            if overlap > 0.5:
                existing_opps.append(opp)
                break
        else:
            title_map[" ".join(sorted(key_words))].append(opp)

    # Flag overlapping opportunities
    flagged = 0
    for key, opps in title_map.items():
        if len(opps) > 1:
            conditions = list(set(o["condition"] for o in opps))
            if len(conditions) > 1:
                for opp in opps:
                    supabase.table("opportunities")\
                        .update({"overlap": True, "conditions": conditions})\
                        .eq("id", opp["id"])\
                        .execute()
                    flagged += 1

    print(f"  Flagged {flagged} opportunities as cross-condition overlap")


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