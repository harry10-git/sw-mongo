import emails.pr_emails as emails
from config import settings
from database.sheet_db import sheet_db
from database.db_types import EmpProjCol, EmpCol


def send_project_end_date_reminder_email_to_partners():
    """Send email to partners to remind them to update project end dates in the employee project database sheet"""
    partner_names = sheet_db.employees[sheet_db.employees[EmpCol.partner]
                                       == 'Yes'][EmpCol.emp_name]
    sheet_link = f"https://docs.google.com/spreadsheets/d/{settings.RECRUITMENT_AND_STAFFING_ID}/edit#gid=1233112386"
    for partner_name in partner_names:
        partner_emp_projects = sheet_db.emp_proj[(sheet_db.emp_proj[EmpProjCol.emp_name] == partner_name) &
                                                 (sheet_db.emp_proj[EmpProjCol.end_date] > settings.TODAYS_DATE)]
        emails.send_partner_reminder_email(
            partner_name=partner_name,
            partner_email=sheet_db.employees[sheet_db.employees[EmpCol.emp_name]
                                             == partner_name][EmpCol.email_fj].values[0],
            projects=partner_emp_projects,
            sheet_link=sheet_link,
        )
