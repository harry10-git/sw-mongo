from datetime import date, timedelta
import numpy as np
import emails.pr_emails as emails
from config import settings
import events

from database.sheet_db import sheet_db
from database.mongo_db import mongo_db
from database.db_types import EmpProj, EmpProjCol, EmpCol, EmpProjRole, Employee, EmploymentType


def create_and_send_new_needed_reviews():
    today_is_review_cycle_first_email_day = settings.TODAYS_DATE == np.busday_offset(
        settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_FIRST_EMAIL, roll='backward').astype(date)
    if today_is_review_cycle_first_email_day:
        due_date = np.busday_offset(settings.MOST_RECENT_6MO_DATE,
                                    events.WORKDAYS_BEFORE_DUE_DATE, roll='backward').astype(date)
    else:
        due_date = np.busday_offset(
            settings.TODAYS_DATE, events.WORKDAYS_BEFORE_DUE_DATE_PROJECT_END, roll='backward').astype(date)

    reviewer_names_need_emails: set[str] = set()
    client_names_need_emails: set[str] = set()

    # create any needed reviews for employees on projects
    for idx, emp_proj in enumerate(sheet_db.get_consultant_projects()):
        try:
            create_reviews_for_emp_proj_if_needed(
                emp_proj, idx + 2, reviewer_names_need_emails, client_names_need_emails, due_date)
        except Exception as e:
            emails.send_code_failure_email(
                f"Error processing consultant project {emp_proj} in row {idx+2}", e)

    if settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_FIRST_EMAIL, roll='backward').astype(date):
        # create any needed self appraisals
        for employee in sheet_db.get_employees():
            try:
                create_self_appraisal_if_needed(
                    employee, reviewer_names_need_emails, due_date)
            except Exception as e:
                emails.send_code_failure_email(
                    f"Error processing employee {employee}", e)

    # send new review emails
    for reviewer_name in reviewer_names_need_emails:
        try:
            emails.send_new_reviews_email(
                reviewer_name, due_date, today_is_review_cycle_first_email_day)
        except Exception as e:
            emails.send_code_failure_email(
                f"Error sending new review email to {reviewer_name}", e)
    for client_name in client_names_need_emails:
        try:
            emails.send_new_external_review_email(client_name, due_date)
        except Exception as e:
            emails.send_code_failure_email(
                f"Error sending new external review email to {client_name}", e)


def create_reviews_for_emp_proj_if_needed(emp_proj: EmpProj,
                                          sheet_row: int,
                                          reviewer_names_need_emails: set[str],
                                          client_names_need_emails: set[str],
                                          due_date: date,
                                          ) -> None:
    """Creates a review for the given employee-project if needed, and adds the reviewer name to the given set if so."""

    employee = sheet_db.get_employee(emp_proj.emp_name)
    if not employee: return
    if type(employee.dod) == date and employee.dod < settings.TODAYS_DATE:
        return

    if type(employee.doj) == date and employee.doj > settings.TODAYS_DATE-timedelta(60) and employee.intern_or_fte_today == EmploymentType.FTE:
        return

    if (settings.TODAYS_DATE < emp_proj.start_date
        or emp_proj.end_date + timedelta(7 * 30) < settings.TODAYS_DATE
            or emp_proj.roll_off_review_request_sent):
        return

    # send email to partner if project is ending in 7 days or ended in the last day and partner hasn't approved end date
    if (not emp_proj.partner_approved_end_date == True
        and (settings.TODAYS_DATE == emp_proj.end_date + timedelta(-7)
             or settings.TODAYS_DATE == emp_proj.end_date + timedelta(-1))):
        emails.send_partner_end_date_approval_email(emp_proj)
        sheet_db.emp_proj.at[sheet_row,
                             EmpProjCol.partner_approval_requested] = True

    if not (settings.TODAYS_DATE == np.busday_offset(emp_proj.end_date, events.WORKDAYS_BEFORE_FIRST_EMAIL_PROJECT_END, roll='backward').astype(date)
            or settings.TODAYS_DATE == np.busday_offset(settings.MOST_RECENT_6MO_DATE, events.WORKDAYS_BEFORE_FIRST_EMAIL, roll='backward').astype(date)):
        return

    # combine list of everyone else on the project with the person during the review period
    # first merge employee info to check if they were fte
    con_proj_merged_emp = sheet_db.emp_proj.merge(
        sheet_db.employees, left_on=EmpProjCol.emp_name, right_on=EmpCol.emp_name, how="left")

    internal_reviewers = con_proj_merged_emp[
        # check if same project
        (con_proj_merged_emp[EmpProjCol.project] == emp_proj.project) &
        # check if not person being reviewed
        (con_proj_merged_emp[EmpProjCol.emp_name] != emp_proj.emp_name) &
        # check if end date was less than 7 months ago
        (con_proj_merged_emp[EmpProjCol.end_date] >= settings.TODAYS_DATE - timedelta(7 * 30)) &
        # check if overlap was at least enough days to be considered teammates
        (((con_proj_merged_emp[EmpProjCol.start_date] <= emp_proj.start_date) &
            (con_proj_merged_emp[EmpProjCol.end_date] >= emp_proj.start_date + timedelta(settings.MINIMUM_TEAMMATES_OVERLAP_TIME_DAYS))) |
         ((con_proj_merged_emp[EmpProjCol.start_date] >= emp_proj.start_date) &
         (con_proj_merged_emp[EmpProjCol.start_date] <= emp_proj.end_date - timedelta(settings.MINIMUM_TEAMMATES_OVERLAP_TIME_DAYS)))) &
        (con_proj_merged_emp[EmpCol.intern_or_fte_two_months_ago]
         == EmploymentType.FTE)  # check if they were fte
    ]

    for reviewer_name in internal_reviewers[EmpProjCol.emp_name]:
        reviewer = sheet_db.get_employee(reviewer_name)
        if not reviewer: continue
        if type(reviewer.dod) == date and reviewer.dod < settings.TODAYS_DATE:
            continue
        if type(reviewer.doj) == date and reviewer.doj > settings.TODAYS_DATE-timedelta(60) and reviewer.intern_or_fte_today == EmploymentType.FTE:
            continue

        reviewee = sheet_db.get_employee(emp_proj.emp_name)
        if not reviewee: continue
        mongo_db.create_internal_needed_review(
            emp_proj=emp_proj,
            reviewee=reviewee,
            reviewer_cons_proj=sheet_db.get_consultant_project(
                reviewer_name, emp_proj.project),
            reviewer=reviewer,
            project=sheet_db.get_project(emp_proj.project),
            due_date=due_date,
        )
        reviewer_names_need_emails.add(reviewer_name)
        print(
            f"Created internal review for {emp_proj.emp_name} from {reviewer_name}")

    if (emp_proj.client_person_name == ""
            or emp_proj.send_external_review_request != 1
            or emp_proj.role == EmpProjRole.PARTNER):
        return

    reviewee = sheet_db.get_employee(emp_proj.emp_name)
    if not reviewee: return
    mongo_db.create_external_needed_review(
        emp_proj=emp_proj,
        reviewee=reviewee,
        client_person=sheet_db.get_client_person(emp_proj.client_person_name),
        project=sheet_db.get_project(emp_proj.project),
        due_date=due_date,
    )
    client_names_need_emails.add(emp_proj.client_person_name)
    print(
        f"Created external review for {emp_proj.emp_name} from {emp_proj.client_person_name}")


def create_self_appraisal_if_needed(employee: Employee,
                                    reviewer_names_need_emails: set[str],
                                    due_date: date,
                                    ) -> None:
    involved_projects_in_last_6_months = sheet_db.emp_proj[
        (sheet_db.emp_proj[EmpProjCol.emp_name] == employee.emp_name) &
        (sheet_db.emp_proj[EmpProjCol.end_date] >= settings.TODAYS_DATE - timedelta(6 * 30)) &
        (sheet_db.emp_proj[EmpProjCol.start_date] <= settings.TODAYS_DATE)
    ]

    if (employee.intern_or_fte_two_months_ago == EmploymentType.INTERN
            or involved_projects_in_last_6_months.empty
            or employee.partner == "Yes"):
        return
    # if it is a datetime
    if type(employee.doj) == date:
        if settings.TODAYS_DATE - timedelta(2*30) < employee.doj:
            return
    if type(employee.dod) == date:
        if settings.TODAYS_DATE > employee.dod:
            return

    mongo_db.create_needed_self_appraisal(employee, due_date)
    reviewer_names_need_emails.add(employee.emp_name)
    print(f"Created self appraisal for {employee.emp_name}")
    return
