from dataclasses import dataclass
from datetime import date
from enum import StrEnum

# Project	Project Code	Person	Role	Client Person	Start Date	End Date	FTE/Intern Today	Skill 1	Skill 2	Skill 3	Skill 4	Skill 5	Send External Review Request	Review Request Sent	Partner Approved End Date	Partner Approval Requested	Billing/Nonbilling

class EmpProjCol(StrEnum):
    worksheet_name = "Consultant - Project"
    project = "Project"
    project_code = "Project Code"
    emp_name = "Person"
    role = "Role"
    client_person_name = "Client Person"
    start_date = "Start Date"
    end_date = "End Date"
    fte_or_intern_today = "FTE/Intern Today"
    send_external_review_request = "Send External Review Request"
    roll_off_review_request_sent = "Review Request Sent"
    partner_approved_end_date = "Partner Approved End Date"
    partner_approval_requested = "Partner Approval Requested"
    billing_or_nonbilling = "Billing/Nonbilling"


class EmpProjRole(StrEnum):
    PARTNER = "Partner"
    MANAGER = "Manager"
    STAFF = "Staff"


@dataclass()
class EmpProj:
    """ConProj object"""
    project: str
    project_code: str
    emp_name: str
    role: EmpProjRole
    client_person_name: str
    start_date: date
    end_date: date
    fte_or_intern_today: str
    send_external_review_request: bool
    roll_off_review_request_sent: bool
    partner_approved_end_date: bool
    partner_approval_requested: bool
    billing_or_nonbilling: str

# projects
# ID	Project Name	Status	Start Date	End Date	Client Company	Needs	Notes	Code


class ProjectCol(StrEnum):
    worksheet_name = "Projects"
    id = "ID"
    project_name = "Project Name"
    status = "Status"
    start_date = "Start Date"
    end_date = "End Date"
    client_company = "Client Company"
    needs = "Needs"
    notes = "Notes"
    code = "Code"


@dataclass()
class Project:
    """Project object"""
    id: str
    project_name: str
    status: str
    start_date: date
    end_date: date
    client_company: str
    needs: str
    notes: str
    code: str


# employees
# Name	Original Role (Intern/FTE)	Conversion Date Intern->FTE	PPO/Direct Hire	College	Tech/Non Tech	DOJ2	DOJ	Status	DOD	Comments	Email - Personal	Email - FJ	Phone	Intern/FTE Today	Partner	Mentor	Link to Interview Sheet	Primary Manager

class EmpCol(StrEnum):
    worksheet_name = "Employees"
    id = "ID"
    emp_name = "Name"
    original_role = "Original Role (Intern/FTE)"
    conversion_date_intern_to_fte = "Conversion Date Intern->FTE"
    ppo_or_direct_hire = "PPO/Direct Hire"
    college = "College"
    tech_or_non_tech = "Tech/Non Tech"
    doj2 = "DOJ2"
    doj = "DOJ"
    status = "Status"
    dod = "DOD"
    comments = "Comments"
    email_personal = "Email - Personal"
    email_fj = "Email - FJ"
    phone = "Phone"
    intern_or_fte_today = "Intern/FTE Today"
    partner = "Partner"
    mentor = "Mentor"
    link_to_interview_sheet = "Link to Interview Sheet"
    primary_manager = "Primary Manager"
    intern_or_fte_two_months_ago = "Intern/FTE Two Months Ago"


class EmploymentType(StrEnum):
    INTERN = "Intern"
    FTE = "FTE"


@dataclass()
class Employee:
    """Employee object"""
    id: str
    emp_name: str
    original_role: str
    conversion_date_intern_to_fte: date
    ppo_or_direct_hire: str
    college: str
    tech_or_non_tech: str
    doj2: date
    doj: date
    status: str
    dod: date
    comments: str
    email_personal: str
    email_fj: str
    phone: str
    intern_or_fte_today: EmploymentType
    partner: str
    mentor: str
    link_to_interview_sheet: str
    primary_manager: str
    intern_or_fte_two_months_ago: EmploymentType

# Clients
# ID	Name	Company	Email


class FJClientCol(StrEnum):
    worksheet_name = "Client Persons"
    id = "ID"
    client_name = "Name"
    company = "Company"
    email = "Email"


@dataclass()
class FJClient:
    """FJClient object"""
    id: str
    client_name: str
    company: str
    email: str


# OnlineEmpCourseAttempt

class OnlineEmpCourseAttemptCol(StrEnum):
    worksheet_name = "Tracker"


class OfflineEmpBatchCol(StrEnum):
    worksheet_name = "Trainee_Batch"
