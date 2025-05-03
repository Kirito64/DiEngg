from fastapi import APIRouter, HTTPException, UploadFile, File
from app.database.milvus import MilvusClient
from app.core.embeddings import EmbeddingGenerator
from typing import Dict, Any, List
import json
import uuid

router = APIRouter()
milvus_client = MilvusClient()
embedding_generator = EmbeddingGenerator()

@router.post("/kb/upload")
async def upload_knowledge(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Upload new knowledge base documents
    """
    try:
        content = await file.read()
        data = json.loads(content)
        
        # Process tickets
        if "tickets" in data:
            for ticket in data["tickets"]:
                ticket_id = str(uuid.uuid4())
                embedding = embedding_generator.generate_embedding(ticket["issueDescription"])
                ticket["id"] = ticket_id
                milvus_client.insert_ticket(ticket, embedding)
        
        # Process team knowledge
        if "team_members" in data:
            for member in data["team_members"]:
                member_id = str(uuid.uuid4())
                # Create a text representation for embedding
                text_repr = f"{member['name']} - {member['role']}\nSkills: {', '.join(member['skills'])}\nCertifications: {', '.join(member['certifications'])}\nResolved Issues: {', '.join(member['resolved_issues'])}"
                embedding = embedding_generator.generate_embedding(text_repr)
                member_data = {
                    "id": member_id,
                    **member
                }
                milvus_client.insert_team_member(member_data, embedding)
        
        return {"message": "Knowledge base updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kb/search")
async def search_knowledge(query: str) -> Dict[str, Any]:
    """
    Search the knowledge base
    """
    try:
        embedding = embedding_generator.generate_embedding(query)
        results = milvus_client.search_similar_tickets(embedding)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/kb/search/team")
async def search_team_knowledge(query: str) -> Dict[str, Any]:
    """
    Search the team knowledge base
    """
    try:
        embedding = embedding_generator.generate_embedding(query)
        results = milvus_client.search_similar_team_members(embedding)
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 