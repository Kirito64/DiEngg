from fastapi import APIRouter, HTTPException
from app.database.models import Feedback
from typing import Dict, Any

router = APIRouter()

@router.post("/feedback")
async def submit_feedback(feedback: Feedback) -> Dict[str, Any]:
    """
    Submit feedback on AI suggestions
    """
    try:
        # TODO: Store feedback in a database for future analysis
        return {
            "message": "Feedback received successfully",
            "ticket_id": feedback.ticket_id,
            "feedback_score": feedback.feedback_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 