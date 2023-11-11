

from pydantic import BaseModel


class PerformanceReviewRequest(BaseModel):
    form: dict
    type: str
    reviewer_name: str
    reviewer_id: str
    reviewer_email: str
    employee_name: str
    employee_id: str
    employee_email: str
    project_name: str | None = None
    reviewer_project_role: str | None = None
    project_id: str | None = None
    submit_date: str
    needed_review_id: str
    
class EndDateRequest(BaseModel):
    employee_id: str
    project_id: str
    end_date: str