from fastapi import APIRouter
from services.supabase_client import supabase

router = APIRouter()

CONDITIONS = {
    "post_mastectomy": "Post-mastectomy / breast cancer recovery",
    "ostomy": "Ostomy",
    "rheumatoid": "Rheumatoid arthritis / mobility limitations",
    "post_surgical": "Post-surgical recovery (general)",
}

@router.get("/conditions")
def get_conditions():
    """Return supported conditions with record counts."""
    conditions = []

    for condition_id, label in CONDITIONS.items():
        result = supabase.table("consumer_signals")\
            .select("count")\
            .eq("condition", condition_id)\
            .execute()

        count = result.data[0]["count"] if result.data else 0

        conditions.append({
            "id": condition_id,
            "label": label,
            "signal_count": count
        })

    return {"conditions": conditions}