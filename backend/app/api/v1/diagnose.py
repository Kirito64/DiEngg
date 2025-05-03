from fastapi import APIRouter, HTTPException
from app.database.models import IssueDescription
from app.core.rag import RAGEngine
from typing import Dict, Any

router = APIRouter()
rag_engine = RAGEngine()

@router.post("/diagnose")
async def diagnose_issue(issue: IssueDescription) -> Dict[str, Any]:
    """
    Endpoint to diagnose a new issue
    """
    try:
        response = rag_engine.process_issue(issue.ticket_text)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 