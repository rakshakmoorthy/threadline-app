from fastapi import APIRouter, Query
from services.supabase_client import supabase
from typing import List

router = APIRouter()

@router.get("/opportunities")
def get_opportunities(conditions: str = Query(..., description="Comma-separated list of conditions")):
    """Return pre-generated ranked opportunities for selected conditions."""
    
    condition_list = [c.strip() for c in conditions.split(",")]
    
    all_opportunities = []
    
    for condition in condition_list:
        result = supabase.table("opportunities")\
            .select("*")\
            .eq("condition", condition)\
            .order("score", desc=True)\
            .execute()
        
        all_opportunities.extend(result.data)
    
    # Sort all opportunities by score descending
    all_opportunities.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    return {
        "opportunities": all_opportunities,
        "total": len(all_opportunities),
        "conditions_queried": condition_list
    }


@router.get("/opportunities/{opportunity_id}")
def get_opportunity_brief(opportunity_id: str):
    """Return full product brief for a specific opportunity."""
    
    result = supabase.table("opportunities")\
        .select("*")\
        .eq("id", opportunity_id)\
        .execute()
    
    if not result.data:
        return {"error": "Opportunity not found"}
    
    return result.data[0]