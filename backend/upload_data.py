import json
from datetime import datetime
from typing import List, Dict, Any
from app.core.embeddings import EmbeddingGenerator
from app.database.milvus import MilvusClient
from app.config import get_settings
import os

settings = get_settings()

def load_tickets_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and format tickets data from JSON file
    """
    with open(file_path, 'r') as f:
        data = json.load(f)
        tickets = data.get('tickets', [])
        
        # Format tickets to match the required schema
        formatted_tickets = []
        for ticket in tickets:
            formatted_ticket = {
                "id": ticket["ticketID"],
                "ticket_id": ticket["ticketID"],
                "machine_model": ticket["machineModel"],
                "serial_number": ticket["serialNumber"],
                "issue_description": ticket["issueDescription"],
                "affected_components": ticket["affectedComponents"],
                "customer": ticket["customer"],
                "reported_date": datetime.strptime(ticket["reportedDate"], "%Y-%m-%d %H:%M"),
                "priority": ticket["priority"],
                "status": ticket["status"],
                "resolution_solution": ticket.get("resolutionSolution", ""),
                "root_cause": ticket.get("rootCause", ""),
                "resolution_date": datetime.strptime(ticket["resolutionDate"], "%Y-%m-%d %H:%M") if ticket.get("resolutionDate") else None,
                "technician": ticket.get("technician", "")
            }
            formatted_tickets.append(formatted_ticket)
        
        return formatted_tickets

def load_team_data(file_path: str) -> List[Dict[str, Any]]:
    """
    Load and format team member data from JSON file
    """
    with open(file_path, 'r') as f:
        team_members = json.load(f)
        
        # Format team members to match the required schema
        formatted_members = []
        for member in team_members:
            formatted_member = {
                "id": member["employee_id"],
                "employee_id": member["employee_id"],
                "name": member["name"],
                "role": member["role"],
                "skills": member["skills"],
                "certifications": member["certifications"],
                "resolved_issues": member["resolved_issues"],
                "experience_years": member["experience_years"],
                "region": member["region"]
            }
            formatted_members.append(formatted_member)
        
        return formatted_members

def upload_tickets(tickets_data: List[Dict[str, Any]]):
    """
    Upload tickets to the RAG system
    """
    embedding_generator = EmbeddingGenerator()
    milvus_client = MilvusClient()
    
    for ticket in tickets_data:
        # Generate embedding for the issue description
        embedding = embedding_generator.generate_embedding(ticket["issue_description"])
        
        # Insert ticket into Milvus
        milvus_client.insert_ticket(ticket, embedding)
    
    print(f"Successfully uploaded {len(tickets_data)} tickets")

def upload_team_members(team_members_data: List[Dict[str, Any]]):
    """
    Upload team members to the RAG system
    """
    embedding_generator = EmbeddingGenerator()
    milvus_client = MilvusClient()
    
    for member in team_members_data:
        # Generate embedding for the member's skills and experience
        member_text = f"{member['name']} {member['role']} {' '.join(member['skills'])} {' '.join(member['certifications'])}"
        embedding = embedding_generator.generate_embedding(member_text)
        
        # Insert team member into Milvus
        milvus_client.insert_team_member(member, embedding)
    
    print(f"Successfully uploaded {len(team_members_data)} team members")

def main():
    # Get the absolute path to the kb_samples directory
    kb_samples_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kb_samples')
    
    # Load and upload tickets
    tickets_file = os.path.join(kb_samples_dir, 'combined_data.json')
    tickets_data = load_tickets_data(tickets_file)
    upload_tickets(tickets_data)
    
    # Load and upload team members
    team_file = os.path.join(kb_samples_dir, 'TeamData', 'teamdata.json')
    team_members_data = load_team_data(team_file)
    upload_team_members(team_members_data)

if __name__ == "__main__":
    main() 