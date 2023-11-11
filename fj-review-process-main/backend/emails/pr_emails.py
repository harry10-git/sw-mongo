"""Collection of functions to send emails for project performance reviews"""
from datetime import date
import pandas as pd
from emails.style_email import FJStyledEmail
from config import settings
from database.db_types import EmpProj, EmpProjCol, EmpProjRole, EmpCol, ProjectCol
from database.sheet_db import sheet_db

FROM_HR = "FJHR"
REVIEW_DASHBOARD_LINK = f"{settings.APP_URL}/pr-reviews"
DIRECT_REVIEW_LINK = f"{settings.APP_URL}/pr-review"


def _send_pr_email(email: FJStyledEmail) -> None:
    if settings.DEPLOYED:
        email.send()
        print("------ Sent the following email ------")
    else:
        print("------ Would have sent the following email ------")
    print(f"From: {email.From}")
    print(f"To: {email.To}")
    print(f"Subject: {email.Subject}")
    print(f"Title: {email.Title}")
    print(f"HTML: {email.text}")
    print("--------------------------------------------------")


def send_new_reviews_email(reviewer_name:str, due_date:date, today_is_review_cycle_first_email_day:bool) -> None:
    """Send email to reviewer for new performance reviews due"""
    reviewer = sheet_db.get_employee(reviewer_name)
    if reviewer is None: return

    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer.email_fj,
        Subject="Performance Review Due",
        Title="Performance Review Due",
    )
    email.add_text(
        f"Hi {reviewer_name.split(' ')[0]},<br><br> This is to notify you that you have new performance review(s) due. Please complete the review(s) using the link below:")
    email.add_link_button("Review Dashboard",
                          f"{REVIEW_DASHBOARD_LINK}/{reviewer.id}")
    email.add_text(
        f"Please complete the review(s) by {due_date.strftime('%Y-%m-%d')}<br><br>")
    
    if today_is_review_cycle_first_email_day:
        email.add_text(
            f"If you have mentees, you should meet with them to discuss their past semester, review their self-appraisal, and take notes on any issues or concerns they may have by {due_date.strftime('%Y-%m-%d')}. You will be expected to represent their views at their respective review sessions.<br><br>")

    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, "", "Sent new reviews email")


def send_new_external_review_email(client_name:str, due_date:date) -> None:
    """Send email to reviewer for project performance review"""
    client = sheet_db.get_client_person(client_name)
    email = FJStyledEmail(
        From=FROM_HR,
        To=client.email,
        Subject="Project Performance Review Request",
        Title="Project Performance Review Request",
    )
    email.add_text(
        f"Hi {client.client_name.split(' ')[0]},<br><br> You have been requested to complete project performance review(s) for FischerJordan. Please complete the review(s) using the link below:")
    email.add_link_button("Review Dashboard",
                          f"{REVIEW_DASHBOARD_LINK}/{client.id}")
    email.add_text(
        f"Please complete the review by {due_date.strftime('%Y-%m-%d')}<br><br>")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(client.client_name, "", "Sent external review email")

def send_final_strict_reminder_email(
    reviewer_name: str,
    reviewer_email: str
) -> None:
    """Send final email to reviewer for review past due"""

    reviewer = sheet_db.get_employee(reviewer_name)
    if reviewer is None: return
    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer_email,
        Subject="Final Reminder for Performance Review",
        Title="Final Reminder for Performance Review",
    )
    email.add_text(f"Hi {reviewer_name},<br><br> This is the final reminder to fill all the pending reviews. The reviews will only be accessible till monday, ie 7th Aug '23. Failing to do so before the deadline will be reflected in the upcoming review meeting. ")
    email.add_link_button("Review Dashboard",
                          f"{DIRECT_REVIEW_LINK}/{reviewer.id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, '', "Sent final review reminder email", '')


def send_project_review_reminder_email(
    reviewer_name: str,
    reviewer_email: str,
    project_name: str,
    employee_name: str,
    needed_review_id: str,
) -> None:
    """Send email to reviewer for project performance review past due"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer_email,
        Subject="Project Performance Review Past Due",
        Title="Project Performance Review Past Due",
    )
    email.add_text(f"Hi {reviewer_name},<br><br> You have a project performance review past due for {employee_name} on {project_name}. Please complete the review using the link below as soon as possible:")
    email.add_link_button("Project Performance Review",
                          f"{DIRECT_REVIEW_LINK}/{needed_review_id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, employee_name, "Sent project review reminder email", project_name)


def send_self_appraisal_reminder_email(
    reviewer_name: str,
    reviewer_email: str,
    needed_review_id: str,
) -> None:
    """Send email for self appraisal past due"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer_email,
        Subject="Self Appraisal Past Due",
        Title="Self Appraisal Past Due",
    )
    email.add_text(
        f"Hi {reviewer_name},<br><br> You have a self appraisal past due. Please complete the review using the link below as soon as possible:")
    email.add_link_button("Self Appraisal",
                          f"{DIRECT_REVIEW_LINK}/{needed_review_id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, reviewer_name, "Sent self appraisal reminder email")


def send_external_review_reminder_email(
    client_person_name: str,
    client_person_email: str,
    project_name: str,
    employee_name: str,
    needed_review_id: str,
) -> None:
    """Send email to reviewer for project performance review"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=client_person_email,
        Subject="Project Performance Review Reminder",
        Title="Project Performance Review Reminder",
    )
    email.add_text(f"Hi {client_person_name},<br><br> You have a project performance review of {employee_name} on {project_name} that is past due. Please complete the review using the link below:")
    email.add_link_button("Project Performance Review",
                          f"{DIRECT_REVIEW_LINK}/{needed_review_id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(client_person_name, employee_name, "Sent external review reminder email", project_name)


def send_strict_self_appraisal_reminder_email(
    reviewer_name: str,
    reviewer_email: str,
    needed_review_id: str,
    period: str,
    last_day_to_complete: date,
) -> None:
    """Send strict email for self appraisal due"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer_email,
        Subject="SELF APPRAISAL - FINAL REMINDER",
        Title="SELF APPRAISAL - FINAL REMINDER",
        CC=settings.STRICT_EMAIL_CC,
    )
    email.add_text(f"""{reviewer_name},<br><br>
        Our records indicate that you have not filled out your self appraisal for {period}. 
        Please be informed that the last possible date for self appraisals is {last_day_to_complete.strftime('%Y-%m-%d')}.
        If the self appraisal has not been submitted by then, it will not be used in your review, 
        and your record will be flagged accordingly.  
        This will be the last reminder you receive for this.""")
    email.add_link_button("Self Appraisal Link",
                          f"{DIRECT_REVIEW_LINK}/{needed_review_id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, reviewer_name, "Sent strict self appraisal reminder email")


def send_strict_project_review_reminder_email(
    reviewer_name: str,
    reviewer_email: str,
    project_name: str,
    period: str,
    last_day_to_complete: date,
    employee_name: str,
    needed_review_id: str,
) -> None:
    """Send email to reviewer for project performance review"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=reviewer_email,
        Subject="PROJECT REVIEW - FINAL REMINDER",
        Title="PROJECT REVIEW - FINAL REMINDER",
        CC=settings.STRICT_EMAIL_CC,
    )
    email.add_text(f"""{reviewer_name},<br><br>
        Our records indicate that you have not filled out your project review of {employee_name} on {project_name} for {period}.
        Please be informed that the last possible date for project reviews is {last_day_to_complete.strftime('%Y-%m-%d')}. 
        This will be the last reminder you receive for this.""")
    email.add_link_button("Project Review Link",
                          f"{DIRECT_REVIEW_LINK}/{needed_review_id}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(reviewer_name, employee_name, "Sent strict project review reminder email", project_name)


def send_review_meeting_email(
    employee_name: str,
    employee_folder_link: str,
    all_review_meeting_emails: list[str],
    scheduler_name: str,
    period: str,
    read_access_off_date: date,
    all_review_meeting_names: list[str]
) -> None:
    """Send email to all managers and partners on projects in last 6 months for review meeting preparation"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=all_review_meeting_emails,
        Subject="Performance Review Meeting",
        Title="Performance Review Meeting",
    )

    # list of all managers and partners on projects in last 6 months to schedule review meeting in email body
    email.add_text(f"Hi {', '.join(all_review_meeting_names)},<br><br> Please find attached the Performance Review Resources for {employee_name} during {period}. {scheduler_name} will be scheduling the performance review sessions by {read_access_off_date.strftime('%Y-%m-%d')}.<br><br>")
    email.add_link_button(f"{employee_name} Performance Review Resources",
                          f"{employee_folder_link}")
    email.add_text(
        " <i> This is an automated email, please do not reply. </i>")
    _send_pr_email(email)


def send_schedule_review_meeting_email(
        scheduler_email: str,
        read_access_off_date: date,
        scheduler_name: str,
) -> None:
    """Send email to all managers and partners on projects in last 6 months to schedule review meeting"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=scheduler_email,
        Subject="Schedule Review Meeting",
        Title="Schedule Review Meeting",
    )

    # list of all managers and partners on projects in last 6 months to schedule review meeting in email body
    email.add_text(f"""Hi {scheduler_name},<br><br>
        Please schedule performance reviews of all FJ team members.
        You will see that a meeting templates have been created preset to yesterday for you to modify and schedule.
        Be sure to select "Send Emails" when you move the template event to the correct time for everyone on the meeting to be notified.<br><br>
        Please note that the review meeting should be scheduled before {read_access_off_date.strftime('%Y-%m-%d')}.<br><br>""")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)


def send_employee_result_email(
    employee_name: str,
    employee_email: str,
    AttachmentName: str,
    PathName: str,
    period: str,
) -> None:
    """Send email to reviewed employee with attached results of the recent review meeting"""

    Attachment = open(PathName, "rb")
    email = FJStyledEmail(
        From=FROM_HR,
        To=employee_email,
        Subject="Performance Review Result",
        Title="Performance Review Result",
        Attachment=Attachment,
        AttachmentName=AttachmentName
    )

    # list of all managers and partners on projects in last 6 months to schedule review meeting in email body
    # email.add_text(f"Hi {employee_name},<br><br>\
    #     Please find attached the Results of the {period} Review Meet.<br><br>")

    email.add_text(f"Dear {employee_name},<br><br> As part of our commitment to providing timely and detailed performance feedback, please find attached a summary of your staff, manager and partner review scores by category.<br> Please keep in mind that this is just one of several inputs that go into our evaluations, and that all results are final.<br><br> Please keep in mind that this information is confidential and intended for your use only. Please do not share it with anyone else.")
    # email.add_link_button(f"Review Result Sheet",
    #                       f"{result_sheet_link}")
    email.add_text(
        " <i><br> This is an automated email, please do not reply. Kindly ignore the previous email. Apologies for the inconvenience caused. </i>")
    _send_pr_email(email)


def send_partner_end_date_approval_email(
    cons_proj: EmpProj,
) -> None:
    """Send email to ask for partner confirmation reg an employee project end date"""

    partner_name: str = sheet_db.emp_proj[(sheet_db.emp_proj[EmpProjCol.project] == cons_proj.project) & (
        sheet_db.emp_proj[EmpProjCol.role] == EmpProjRole.PARTNER)][EmpProjCol.emp_name].values[0]
    employee_id: str = sheet_db.employees[sheet_db.employees[EmpCol.emp_name]
                                          == cons_proj.emp_name][EmpCol.id].values[0]
    partner_email: str = sheet_db.employees[sheet_db.employees[EmpCol.emp_name]
                                            == partner_name][EmpCol.email_fj].values[0]
    project_id: str = sheet_db.projects[sheet_db.projects[ProjectCol.project_name]
                                        == cons_proj.project][ProjectCol.id].values[0]

    END_DATE_LINK = f"{settings.APP_URL}post_end_date/{employee_id}/{project_id}"
    CONFIRM_DATE_LINK = f"{settings.APP_URL}confirm_end_date/{employee_id}/{project_id}"

    email = FJStyledEmail(
        From=FROM_HR,
        To=partner_email,
        Subject="Employee Project End Date Confirmation",
        Title="Employee Project End Date Confirmation",
    )
    email.add_text(
        f"Hi {partner_name},<br><br> This email is for the confirmation of {cons_proj.emp_name.split(' ')[0]}'s end date of {date.strftime(cons_proj.end_date, '%Y-%m-%d')} for the project: {cons_proj.project}")
    email.add_link_button("Edit End Date", f"{END_DATE_LINK}")
    email.add_link_button("Confirm End Date", f"{CONFIRM_DATE_LINK}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")

    _send_pr_email(email)
    sheet_db.log_event("Partner", cons_proj.emp_name, "Partner Approval Email Sent", cons_proj.project, cons_proj.end_date)


def send_partner_reminder_email(
    partner_name: str,
    partner_email: str,
    projects: pd.DataFrame,
    sheet_link: str,
) -> None:
    """Send email to partners for consultant sheet update"""

    email = FJStyledEmail(
        From=FROM_HR,
        To=partner_email,
        Subject="Reminder to update Consultant Project sheet",
        Title="Project End Date Verification",
    )
    email.add_text(f"Hi {partner_name},<br><br> This is the list of live projects and their projected end dates based on information from the Recruitment and Staffing sheet. Please review these to ensure the end date is accurate and the project list is complete.<br>")

    for project in range(len(projects)):
        if project == 0:
            email.add_text(
                f"<br>{projects['Project'].loc[project]}: {projects['End Date'].loc[project]}")
        else:
            email.add_text(
                f"{projects['Project'].loc[project]}: {projects['End Date'].loc[project]}")
    email.add_link_button("Recruitment & Staffing Sheet",
                          f"{sheet_link}")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)
    sheet_db.log_event(partner_name, partner_name, "Partner Reminder Email Sent")


def send_code_starting_email() -> None:
    email = FJStyledEmail(
        From=FROM_HR,
        To=settings.CODE_ADMIN_EMAILS,
        Subject="Code Starting",
        Title="Code Starting",
    )

    email.add_text(f"""
Hi code admin for FJReview,<br><br>
Code Starting.
""")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)


def send_code_complete_email() -> None:
    email = FJStyledEmail(
        From=FROM_HR,
        To=settings.CODE_ADMIN_EMAILS,
        Subject="Daily Runner Success",
        Title="Daily Runner Success",
    )

    email.add_text(f"""
Hi code admin for FJReview,<br><br>
Daily Runner Ran Successfully.
""")
    email.add_text("<i>This is an automated email, please do not reply.</i>")
    _send_pr_email(email)


def send_code_failure_email(message: str, e: Exception) -> None:
    email = FJStyledEmail(
        From=FROM_HR,
        To=settings.CODE_ADMIN_EMAILS,
        Subject="Code Failure",
        Title="Code Failure",
    )

    email.add_text(f"""
Hi code admin for FJReview,<br><br>
{message}<br><br>
Code failed with error {e}.
""")
    email.add_text("<i>This is an automated email, please do not reply.</i>")

    _send_pr_email(email)
