from datetime import datetime
from typing_extensions import TypedDict
from pydantic import BaseModel

class BaseResponse(BaseModel):
    """Base request class"""
    pass

class NeededReviewResponse(BaseResponse):
    id: str
    type: str
    reviewer_id: str
    reviewer_name: str
    reviewer_email: str
    employee_id: str
    employee_name: str
    employee_email: str
    project_id: str|None = None
    reviewer_project_role: str|None = None
    project_name: str | None = None
    due_date: str
    description: str
    status: str
    created_at: datetime
    title: str

class ProcessStat(TypedDict):
    incomplete: int
    complete: int

class ProcessStatsResponse(BaseResponse):
    partner: ProcessStat
    staff: ProcessStat
    self: ProcessStat
    manager: ProcessStat
    external: ProcessStat
    total: ProcessStat
    
    
class PostEndDateResponse(BaseModel):
    success: bool