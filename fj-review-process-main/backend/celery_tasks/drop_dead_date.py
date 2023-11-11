from datetime import date, datetime, timedelta, timezone
import numpy as np
import pandas as pd

from gcalendar import cal
import emails.pr_emails as emails
import drive
import events
import kms
from config import settings, DropDeadDateFlavor
import gspread_dataframe
import gspread_formatting
from database.sheet_db import sheet_db
from database.mongo_db import mongo_db
from database.db_types import EmpProjCol, EmpCol, EmpProjRole, Employee, EmploymentType


def execute_drop_dead_date(flavor: DropDeadDateFlavor = settings.DROP_DEAD_DATE_FLAVOR):
    """
    If drop dead date, then for each employee send email to all managers and partners on projects with them in the last 6 months
    these emails are to setup the review letter meeting with the employee
    """

    kms_api = kms.KMS_API()
    read_access_off_date = np.busday_offset(settings.TODAYS_DATE,
                                            events.WORKDAYS_BEFORE_READ_WRITE_OFF_DATE -
                                            events.WORKDAYS_BEFORE_DROP_DEAD_DATE,
                                            roll='backward').astype(date)

    emp_names_on_projects_in_last_6_months = sheet_db.emp_proj[
        (sheet_db.emp_proj[EmpProjCol.start_date] < settings.TODAYS_DATE)
    ][EmpProjCol.emp_name].unique().tolist()

    emp_names_that_get_review_folder = sheet_db.employees[
        (sheet_db.employees[EmpCol.intern_or_fte_two_months_ago] != EmploymentType.INTERN) &
        # only apply condition if doj is a date
        (
            (sheet_db.employees[EmpCol.doj].isna()) |
            (sheet_db.employees[EmpCol.doj] <
             settings.TODAYS_DATE - timedelta(days=2*30))
        ) &
        (sheet_db.employees[EmpCol.emp_name].isin(emp_names_on_projects_in_last_6_months)) &
        (~sheet_db.employees[EmpCol.emp_name].isin(
            settings.NO_REVIEW_MEETING_EMPLOYEE_NAMES))
    ][EmpCol.emp_name].unique().tolist()

    for emp_name in emp_names_that_get_review_folder:
        employee = sheet_db.get_employee(emp_name)
        if not employee: continue
        
        # try to get employee folder id from mongodb otherwise create it and add to mongodb
        if mongo_db.employees.find_one({"employee_id": employee.id}):
            employee_folder_id = mongo_db.employees.find_one(
                {"employee_id": employee.id})['folder_id']  # type: ignore
        else:
            employee_folder_id = drive.create_file(
                employee.emp_name, settings.ALL_EMPLOYEES_DRIVE_FOLDER_ID, drive.FileType.FOLDER)
            mongo_db.employees.insert_one(
                {"name": employee.emp_name, "folder_id": employee_folder_id, "employee_id": employee.id})

        period_folder_name = f"{employee.emp_name} {settings.PREVIOUS_PERIOD_STRING}"
        period_folder_id = drive.create_file(
            period_folder_name, employee_folder_id, drive.FileType.FOLDER)

        # create template review letter if today in first 6 months
        if flavor == DropDeadDateFlavor.FORMAL:
            review_letter_template_name = f"{employee.emp_name} {settings.PREVIOUS_PERIOD_STRING} - Review Letter Template"
            drive.create_file(
                file_name=review_letter_template_name,
                file_path="resources/blank_review_letter.docx",
                file_type=drive.FileType.DOCX,
                parent_folder_id=period_folder_id
            )

        # create sheet for employee for the period review meeting
        review_sheet_name = f"{employee.emp_name} {settings.PREVIOUS_PERIOD_STRING} - Reviews"
        review_sheet_id = drive.create_file(
            review_sheet_name,
            period_folder_id,
            drive.FileType.GOOGLE_SHEET
        )

        if flavor == DropDeadDateFlavor.FORMAL:
            fill_review_sheet_with_data(employee, review_sheet_id, kms_api)
        else:
            fill_review_sheet_with_informal_data(employee, review_sheet_id)

        meeting_attendees_except_employee = get_meeting_attendees_except_employee(
            employee, flavor)

        if employee.partner == "Yes" or employee.emp_name in settings.NO_REVIEW_MEETING_EMPLOYEE_NAMES:
            continue

        # set permissions on employee folder to read only
        for meeting_attendee in meeting_attendees_except_employee:
            drive.set_permission(
                file_id=employee_folder_id,
                email=meeting_attendee.email_fj,
                role=drive.PermissionRole.READER
            )

        all_review_meeting_emails = [
            meeting_attendee.email_fj for meeting_attendee in meeting_attendees_except_employee] + [employee.email_fj]
        all_review_meeting_names = [
            meeting_attendee.emp_name for meeting_attendee in meeting_attendees_except_employee] + [employee.emp_name]

        employee_folder_link = f"https://drive.google.com/drive/folders/{employee_folder_id}"

        emails.send_review_meeting_email(
            employee_name=employee.emp_name,
            employee_folder_link=employee_folder_link,
            all_review_meeting_emails=all_review_meeting_emails,
            scheduler_name=settings.SCHEDULER_NAME,
            period=settings.PREVIOUS_PERIOD_STRING,
            read_access_off_date=read_access_off_date,
            all_review_meeting_names=all_review_meeting_names
        )

        # create calendar event for the meeting
        try:
            cal.create_review_meeting_event(
                summary=f"Review Meeting of {employee.emp_name}",
                description=f"Review Meeting of {employee.emp_name} {all_review_meeting_names}\n\n{employee_folder_link}",
                # 4 am IST (UTC+5:30) yesterday
                start_datetime=datetime.now(timezone.utc).replace(
                    hour=22, minute=0, second=0, microsecond=0) - timedelta(days=2),
                # 30 min hours later
                end_datetime=datetime.now(timezone.utc).replace(
                    hour=22, minute=0, second=0, microsecond=0) - timedelta(days=2) + timedelta(minutes=30),
                attendees=all_review_meeting_emails,
                meeting_key=f"review-meeting-{employee.emp_name}"
            )
        except Exception as e:
            emails.send_code_failure_email(f"failed to create review meeting event for {employee.emp_name} with error", e)

        print(
            f"Sent schedule review meeting email for {employee.emp_name} to {all_review_meeting_emails}")

    # all needed reviews that have status other than complete are now expired
    mongo_db.needed_reviews.update_many(
        {"status": {"$ne": "completed"}},
        {"$set": {"status": "expired"}}
    )

    drive.set_permission(
        file_id=settings.ALL_EMPLOYEES_DRIVE_FOLDER_ID,
        email=settings.WRITE_ACCESS_EMAIL,
        role=drive.PermissionRole.WRITER
    )

    # send email to always review meeting emails to remind them to move the meeting to the right time
    emails.send_schedule_review_meeting_email(
        scheduler_email=settings.SCHEDULER_EMAIL,
        scheduler_name=settings.SCHEDULER_NAME,
        read_access_off_date=read_access_off_date
    )


def get_meeting_attendees_except_employee(employee: Employee, flavor: DropDeadDateFlavor) -> list[Employee]:
    match flavor:
        case DropDeadDateFlavor.FORMAL:
            projects_worked_on_last_6mo: list[str] = sheet_db.emp_proj[
                (sheet_db.emp_proj[EmpProjCol.start_date] > settings.TODAYS_DATE - timedelta(days=30*6)) &
                (sheet_db.emp_proj[EmpProjCol.start_date] < settings.TODAYS_DATE) &
                (sheet_db.emp_proj[EmpProjCol.emp_name] == employee.emp_name)
            ][EmpProjCol.project].unique().tolist()
            managers_and_partners_names_on_projects_worked_on_last_6mo = sheet_db.emp_proj[
                (sheet_db.emp_proj[EmpProjCol.start_date] > settings.TODAYS_DATE - timedelta(days=30*6)) &
                (sheet_db.emp_proj[EmpProjCol.start_date] < settings.TODAYS_DATE) &
                (sheet_db.emp_proj[EmpProjCol.emp_name] != employee.emp_name) &
                (sheet_db.emp_proj[EmpProjCol.project].isin(projects_worked_on_last_6mo)) &
                (sheet_db.emp_proj[EmpProjCol.role].isin(
                    [EmpProjRole.MANAGER, EmpProjRole.PARTNER]))
            ][EmpProjCol.emp_name].unique().tolist()
            meeting_attendees_names_except_emp = [
                manager_and_partner_name for manager_and_partner_name in managers_and_partners_names_on_projects_worked_on_last_6mo
                + settings.ALWAYS_REVIEW_MEETING_NAMES
                + [employee.primary_manager]
                + [employee.mentor]
            ]
        case DropDeadDateFlavor.INFORMAL:
            meeting_attendees_names_except_emp = [
                manager_and_partner_name for manager_and_partner_name in settings.ALWAYS_REVIEW_MEETING_NAMES
                + [employee.primary_manager]
                + [employee.mentor]
            ]
        case _:
            meeting_attendees_names_except_emp = []
    try: meeting_attendees_names_except_emp.remove(employee.emp_name)
    except Exception as e: pass
    meeting_attendees_names_except_emp = list(set(
        meeting_attendees_names_except_emp))
    meeting_attendees_except_emp = [sheet_db.get_employee(
        emp_name) for emp_name in meeting_attendees_names_except_emp]
    return [
        emp for emp in meeting_attendees_except_emp if emp is not None]


def fill_review_sheet_with_data(employee: Employee, review_sheet_id: str, kms_api: kms.KMS_API):
    # create internal project reviews dataframe from mongodb reviews where type is staff, manager, or partner
    review_sheet = sheet_db.service_account.open_by_key(review_sheet_id)
    six_mo_ago_str: str = (settings.TODAYS_DATE -
                           timedelta(days=30*6)).strftime("%Y-%m-%d")
    try:
        internal_project_reviews,  = []
        for review in mongo_db.reviews.find({"employee_id": employee.id, "type": {"$in": ["staff", "manager", "partner"]}, "submit_date": {"$gte": six_mo_ago_str}}):
            internal_project_reviews.append(review)

        # flatten internal project reviews to get rid of nested objects
        for i, internal_project_review in enumerate(internal_project_reviews):
            internal_project_reviews[i] = flatten_review(
                internal_project_review)

            # remove employee name if it is type partner to make it anonymous
            if internal_project_review['type'] == "partner":
                internal_project_reviews[i]['reviewer_name'] = "Anonymous"
                internal_project_reviews[i]['reviewer_email'] = "Anonymous"
                internal_project_reviews[i]['reviewer_role'] = "Anonymous"
                internal_project_reviews[i]['reviewer_id'] = "Anonymous"
                internal_project_reviews[i]['reviewer_project_role'] = "Anonymous"

        if len(internal_project_reviews) > 0:
            projects_wks = review_sheet.add_worksheet(
                "Projects", rows=1000, cols=200)
            internal_project_reviews_df = pd.DataFrame(
                internal_project_reviews)

            gspread_dataframe.set_with_dataframe(
                projects_wks, internal_project_reviews_df.loc[
                    :, ~internal_project_reviews_df.columns.str.startswith('Comment: ')])

            gspread_formatting.set_row_height(
                projects_wks, 1, 250)
            projects_wks.format(
                'A1:ZZ1', {'wrapStrategy': 'WRAP'})

            proj_summary_wks = review_sheet.add_worksheet(
                "Projects Summary", rows=1000, cols=200)
            pivot = create_summary_pivot_table(
                internal_project_reviews_df.replace(np.nan, '', regex=True))
            gspread_dataframe.set_with_dataframe(
                proj_summary_wks, pivot)
            gspread_formatting.set_column_width(
                proj_summary_wks, 1, 350)
    except:
        print("Error creating projects tabs")

    # create external reviews dataframe from mongodb reviews where type is external
    # that was submitted by the employee in the last 6 months
    try:
        external_reviews,  = []
        for review in mongo_db.reviews.find({"employee_id": employee.id, "type": "external", "submit_date": {"$gte": six_mo_ago_str}}):
            external_reviews.append(flatten_review(review))
        if len(external_reviews) > 0:
            external_wks = review_sheet.add_worksheet(
                "External", rows=1000, cols=200)
            external_reviews_df = pd.DataFrame(external_reviews)
            gspread_dataframe.set_with_dataframe(
                external_wks, external_reviews_df)
            gspread_formatting.set_row_height(
                external_wks, 1, 250)
    except:
        print("Error adding external review tab")

    # create self appraisal dataframe from mongodb reviews where type is self
    try:
        self_appraisals,  = []
        for review in mongo_db.reviews.find({"employee_id": employee.id, "type": "self", "submit_date": {"$gte": six_mo_ago_str}}):
            self_appraisals.append(review)

        # flatten self appraisal to get rid of nested objects
        for i, self_appraisal in enumerate(self_appraisals):
            self_appraisals[i] = flatten_review(
                self_appraisal)

        if len(self_appraisals) > 0:
            # add a tab for self appraisals
            review_sheet.add_worksheet("Self Appraisal", rows=1000, cols=200)
            self_appraisals_df = pd.DataFrame(
                self_appraisals).set_index('submit_date')
            try:
                self_appraisals_df = self_appraisals_df.drop(
                    columns=['type', 'reviewer_name', 'employee_name', 'project_name', 'reviewer_project_role'])
            except:
                pass
            # add self appraisals to sheet
            review_sheet.add_worksheet("Self Appraisal", rows=1000, cols=200)
            gspread_dataframe.set_with_dataframe(
                review_sheet.worksheet("Self Appraisal"), self_appraisals_df)
    except:
        print("Error adding self appraisal tab")

    # create a tabs showing all needed_reviews related to the employee for the period and if they have been completed or not
    try:
        all_needed_reviews_by_employee = pd.DataFrame()
        all_needed_reviews_of_employee = pd.DataFrame()

        # find all needed where employee_id is the employee's id and the due date is in the last 6 months
        for i, needed_review in mongo_db.needed_reviews.find(
                {"employee_id": employee.id, "due_date": {"$gte": six_mo_ago_str}}):

            # concat to all needed reviews of employee
            all_needed_reviews_of_employee = pd.concat(
                [all_needed_reviews_of_employee, pd.DataFrame(needed_review, index=[0])])

        for i, needed_review in mongo_db.needed_reviews.find(
                {"reviewer_id": employee.id, "due_date": {"$gte": six_mo_ago_str}}):

            # concat to all needed reviews by employee
            all_needed_reviews_by_employee = pd.concat(
                [all_needed_reviews_by_employee, pd.DataFrame(needed_review, index=[0])])

        # remove unnecessary columns _id reviewer_id employee_id project_id reviewer_email employee_email description
        all_needed_reviews_of_employee = all_needed_reviews_of_employee.drop(
            columns=['_id', 'reviewer_id', 'employee_id', 'project_id', 'reviewer_email', 'employee_email', 'description', 'due_date', 'created_at'])
        all_needed_reviews_by_employee = all_needed_reviews_by_employee.drop(
            columns=['_id', 'reviewer_id', 'employee_id', 'project_id', 'reviewer_email', 'employee_email', 'description', 'due_date', 'created_at'])

        if employee.partner == "Yes":
            all_needed_reviews_of_employee = all_needed_reviews_of_employee.drop(
                columns=['reviewer_name', 'reviewer_project_role', 'project_name'])
            all_needed_reviews_by_employee = all_needed_reviews_by_employee.drop(
                columns=['reviewer_name', 'reviewer_project_role', 'project_name'])

        reviews_by_emp_wks = review_sheet.add_worksheet(
            "Reviews by Employee", rows=1000, cols=200)
        reviews_of_emp_wks = review_sheet.add_worksheet(
            "Reviews of Employee", rows=1000, cols=200)
        gspread_dataframe.set_with_dataframe(
            reviews_by_emp_wks, all_needed_reviews_by_employee)
        gspread_dataframe.set_with_dataframe(
            reviews_of_emp_wks, all_needed_reviews_of_employee)
    except:
        print("Error adding needed review tabs to the sheet")

    # training courses tab
    try:
        courses_df = sheet_db.online_courses
        employee_courses_df = courses_df[courses_df['Name']
                                         == employee.emp_name]
        if len(employee_courses_df) > 0:
            employee_courses_df = employee_courses_df["Name", "Course",
                                                      "Start Date", "End Date", "Is a Reschedule", "Complete"]
            online_training_wks = review_sheet.add_worksheet(
                "Training Courses", rows=1000, cols=200)
            gspread_dataframe.set_with_dataframe(
                online_training_wks, employee_courses_df)
    except:
        print("Could not find training courses for employee")

    # offline training courses tab
    try:
        offline_courses_df = sheet_db.offline_courses
        employee_offline_courses_df = offline_courses_df[offline_courses_df['Email']
                                                         == employee.email_fj]
        if len(employee_offline_courses_df) > 0:
            employee_offline_courses_df = employee_offline_courses_df["Name",
                                                                      "Course", "Start Date", "End Date", "Is a Reschedule", "Complete"]
            offline_training_wks = review_sheet.add_worksheet(
                review_sheet_id, "Offline Training Courses", 1000, 200)
            gspread_dataframe.set_with_dataframe(
                offline_training_wks, employee_offline_courses_df)
    except:
        print("Could not find offline training courses for employee")

    # kms projects tab
    try:
        kms_projects = kms_api.get_projects_for_employee(
            employee.email_fj)
        if kms_projects.shape[0] > 0:

            kms_projects['Created in last 6 months'] = kms_projects[kms.KMSProjectCol.created_on].apply(
                lambda x: "Yes" if x >= settings.TODAYS_DATE-timedelta(6*30) else "No")

            kms_projects['Total Count'] = ''
            kms_projects['Created in last 6 months Count'] = ''
            kms_projects['Total Count'][0] = len(kms_projects)
            kms_projects['Created in last 6 months Count'][0] = len(kms_projects[
                kms_projects['Created in last 6 months'] == 'Yes'])

            kms_projects_wks = review_sheet.add_worksheet(
                "KMS Projects", rows=1000, cols=200)
            gspread_dataframe.set_with_dataframe(
                kms_projects_wks, kms_projects)
    except:
        print("Error adding kms projects to sheet")

    # remove "Sheet1" tab from sheet if it exists and there are more than 1 tabs since "Sheet1" is created by default
    try:
        worksheets = review_sheet.worksheets()
        if "Sheet1" in worksheets and len(worksheets) > 1:
            review_sheet.del_worksheet(review_sheet.worksheet("Sheet1"))
    except:
        print("Error Trying to remove Sheet1")


def fill_review_sheet_with_informal_data(employee: Employee, review_sheet_id: str):
    review_sheet = sheet_db.service_account.open_by_key(review_sheet_id)
    six_mo_ago_str: str = (settings.TODAYS_DATE -
                           timedelta(days=30*6)).strftime("%Y-%m-%d")

    try:
        flattened_review_results = []
        for review in mongo_db.reviews.find({"employee_id": employee.id, "type": {"$in": ["staff", "manager", "partner"]}, "submit_date": {"$gte": six_mo_ago_str}}):
            flattened_review_results.append(flatten_review(review))
        reviews = pd.DataFrame(flattened_review_results)
        # remove all columns that start with "Comment"
        try:
            reviews = reviews.loc[:, ~reviews.columns.str.startswith('Comment')]
        except:
            pass

        # transpose the dataframe
        reviews = reviews.transpose()
        reviews['Question'] = reviews.index
        
        first_column = reviews.pop('Question')
        reviews.insert(0, 'Question', first_column)
        
        reviews = reviews.iloc[6:]
        reviews = reviews.replace('H', 3)
        reviews = reviews.replace('M', 2)
        reviews = reviews.replace('L', 1)
        reviews = reviews.replace('Don\'t Know', np.nan)
        
        # pivot so each row is a question and the value is the average score
        # row is index since we transposed the dataframe
        # reviews = reviews.pivot_table(
        #     index=reviews.index, aggfunc='mean', dropna=False)  # type: ignore
        
        reviews_avg = reviews.iloc[:,0].to_frame()
        reviews_avg['Average Score'] = round(reviews.iloc[:,1:].mean(axis=1),2)
        total_avg = round(reviews_avg['Average Score'].mean(),2)
        
        reviews = reviews_avg
        # sort by average score
        try: reviews = reviews.sort_values(
            by='Average Score', ascending=False)  # type: ignore
        except: pass
        reviews = pd.concat([reviews, pd.DataFrame([["TOTAL SCORE", total_avg]], columns = ["Question", "Average Score"])],  ignore_index=True)
        # update the review sheet
        reviews_wks = review_sheet.add_worksheet(
            "Results", rows=1000, cols=200)
        gspread_dataframe.set_with_dataframe(
            reviews_wks, reviews)
        gspread_formatting.set_column_width(
                reviews_wks, "A", 350)
        
        
        result_sheet_name = f"demo - Results"
        
        pathName = "/tmp/" + result_sheet_name + ".xlsx"
        fileName = result_sheet_name + ".xlsx"
        
        reviews.to_excel(pathName, 'Results', index=False)  
        emails.send_employee_result_email(
            employee_name=employee.emp_name, 
            employee_email = employee.email_fj,
            AttachmentName = fileName,
            PathName = pathName,
            period=settings.PREVIOUS_PERIOD_STRING
        )

    except Exception as e:
        print(f"Error getting review results for employee {employee.id} {employee.emp_name}")
        print(e)
        
    try:
        external_reviews,  = []
        for review in mongo_db.reviews.find({"employee_id": employee.id, "type": "external", "submit_date": {"$gte": six_mo_ago_str}}):
            external_reviews.append(flatten_review(review))
        if len(external_reviews) > 0:
            external_wks = review_sheet.add_worksheet(
                "External", rows=1000, cols=200)
            external_reviews_df = pd.DataFrame(external_reviews)
            gspread_dataframe.set_with_dataframe(
                external_wks, external_reviews_df)
            gspread_formatting.set_row_height(
                external_wks, 1, 250)
    except:
        print("Error adding external review tab")
    
    # remove "Sheet1" tab from sheet if it exists and there are more than 1 tabs since "Sheet1" is created by default
    try:
        worksheets = review_sheet.worksheets()
        if "Sheet1" in worksheets and len(worksheets) > 1:
            review_sheet.del_worksheet(review_sheet.worksheet("Sheet1"))
    except:
        print("Error Trying to remove Sheet1")


def flatten_review(review: dict):
    # RuntimeError: dictionary changed size during iteration because of nested dicts
    # so we need to make a copy of the dict and iterate over that
    flattened_review = {}

    for key in review.keys():
        if "_id" in key:
            continue
        if "_email" in key:
            continue
        if key == "form":
            continue
        flattened_review[key] = review[key]

    for key, value in review["form"].items():
        flattened_review[key] = value

    return flattened_review


def create_summary_pivot_table(df: pd.DataFrame) -> pd.DataFrame:

    def get_hml_value(hml):
        match hml:
            case 'H': return 3
            case 'M': return 2
            case 'L': return 1
            case _: return np.nan

    questions = [col.split(":")[1].strip()
                 for col in df.columns if col.startswith("HML")]

    # convert into the dataframe we want to return with the columns we want to return
    df_new = pd.DataFrame(
        columns=["Question", "Partner Average", "Partner Count" "Manager Average", "Manager Count", "Staff Average", "Staff Count" "All Average", "All Count" "Comments"])

    for question in questions:
        entry = {}
        entry["Question"] = question

        # get the average for each reviewer_project_role where you only use the HML for the current question and only if it is a number after converting it
        entry["Partner Average"] = df[df["reviewer_project_role"] ==
                                      "Partner"][f"HML: {question}"].apply(get_hml_value).mean()
        # don't count "Don't Know" as a response
        entry["Partner Count"] = df[df["reviewer_project_role"] ==
                                    "Partner"][f"HML: {question}"].apply(get_hml_value).count()
        entry["Manager Average"] = df[df["reviewer_project_role"] ==
                                      "Manager"][f"HML: {question}"].apply(get_hml_value).mean()
        entry["Manager Count"] = df[df["reviewer_project_role"] ==
                                    "Manager"][f"HML: {question}"].apply(get_hml_value).count()
        entry["Staff Average"] = df[df["reviewer_project_role"] ==
                                    "Staff"][f"HML: {question}"].apply(get_hml_value).mean()
        entry["Staff Count"] = df[df["reviewer_project_role"] ==
                                  "Staff"][f"HML: {question}"].apply(get_hml_value).count()
        entry["All Average"] = df[f"HML: {question}"].apply(
            get_hml_value).mean()
        entry["All Count"] = df[f"HML: {question}"].apply(
            get_hml_value).count()

        # create a list of comments for the current question

        comments = []
        for i in range(len(df)):
            # look for the comment column for the current question
            comment_col = f"Comment: {question}"
            # if the column exists and the comment is not empty
            if comment_col in df.columns and df[comment_col][i] != "":
                # add the reviewer_name and the comment to the list of comments for the current question
                comments.append(
                    f"{df['reviewer_name'][i]}: {df[comment_col][i]}")

        entry["Comments"] = ", ".join(comments)

        df_new = pd.concat([df_new, pd.DataFrame(entry, index=[0])])

    # fix the column order
    df_new = df_new[["Question", "Partner Average", "Partner Count", "Manager Average",
                     "Manager Count", "Staff Average", "Staff Count", "All Average", "All Count", "Comments"]]

    return df_new
