from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class TicketBase(BaseModel):
    ticket_id: str
    machine_model: str
    serial_number: str
    issue_description: str
    affected_components: List[str]
    customer: str
    reported_date: datetime
    priority: str
    status: str

class TicketCreate(TicketBase):
    pass

class TicketResponse(TicketBase):
    resolution_solution: Optional[str]
    root_cause: Optional[str]
    resolution_date: Optional[datetime]
    technician: Optional[str]

class TeamMemberBase(BaseModel):
    employee_id: str
    name: str
    role: str
    skills: List[str]
    certifications: List[str]
    resolved_issues: List[str]
    experience_years: int
    region: str

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberResponse(TeamMemberBase):
    pass

class IssueDescription(BaseModel):
    ticket_text: str

class Feedback(BaseModel):
    ticket_id: str
    feedback_score: int
    feedback_text: Optional[str]
    suggested_improvements: Optional[str] 