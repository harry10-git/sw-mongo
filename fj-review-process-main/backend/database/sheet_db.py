from datetime import date
from typing import Any
import gspread
import gspread_dataframe
import pandas as pd
from database.db_types import EmpProj, EmpProjCol, EmpCol, Employee, FJClient, FJClientCol, OfflineEmpBatchCol, OnlineEmpCourseAttemptCol, Project, ProjectCol
from config import settings


class ReviewsDB():
    """Offline database class."""

    def __init__(self):
        self.service_account = gspread.service_account_from_dict(
            settings.GOOGLE_SERVICE_ACCOUNT)
        self.settings_sheet = self.service_account.open(
            settings.SETTINGS_SHEET_NAME)
        self.staffing_sheet = self.service_account.open(
            settings.EMPLOYEE_PROJECT_DATABASE)

        self._emp_proj = None
        self._employees = None
        self._projects = None
        self._reviews_log = None
        self._clients = None
        self._online_courses = None
        self._offline_courses = None
        self._event_log = None
        self._event_log_worksheet = None

        self._reviews_log_worksheet = self.staffing_sheet.worksheet(
            "Reviews Log")
        
        # process dates
        self.process_dates: list[dict[str, Any]] = self.settings_sheet.worksheet(
            "Process Dates").get_all_records()
        # convert all dates to date type
        self.emp_rolls_off_process_dates: list[dict[str, Any]] = self.settings_sheet.worksheet(
            "Employee Rolls Off Process Dates").get_all_records()
        print("Review Database initialized.")

    @property
    def projects(self) -> pd.DataFrame:
        """Get the projects dataframe."""
        if self._projects is not None:
            return self._projects
        self._projects_worksheet = self.staffing_sheet.worksheet(
            ProjectCol.worksheet_name)
        self._projects = pd.DataFrame(
            self._projects_worksheet.get_all_records())
        return self._projects

    # property so that on first call, the settings are fetched from the sheet

    @property
    def employees(self) -> pd.DataFrame:
        """Get the employees dataframe."""
        if self._employees is not None:
            return self._employees
        self._employees_worksheet = self.staffing_sheet.worksheet(
            EmpCol.worksheet_name)
        self._employees = pd.DataFrame(
            self._employees_worksheet.get_all_records())
        # convert EmpCol.doj to date type
        self._employees[EmpCol.doj] = pd.to_datetime(
            self._employees[EmpCol.doj]).dt.date
        self._employees[EmpCol.doj] = self._employees[EmpCol.doj].astype(object).where(
            self._employees[EmpCol.doj].notnull(), None)

        self._employees[EmpCol.dod] = pd.to_datetime(
            self._employees[EmpCol.dod]).dt.date
        self._employees[EmpCol.dod] = self._employees[EmpCol.dod].astype(object).where(
            self._employees[EmpCol.dod].notnull(), None)
        return self._employees

    @property
    def emp_proj(self) -> pd.DataFrame:
        """Get the employee projects dataframe."""
        if self._emp_proj is not None:
            return self._emp_proj
        self._emp_project_worksheet = self.staffing_sheet.worksheet(
            EmpProjCol.worksheet_name)
        self._emp_proj = pd.DataFrame(
            self._emp_project_worksheet.get_all_records())
        # convert EmpProjCol.start_date and EmpProjCol.end_date to date type
        self._emp_proj[EmpProjCol.start_date] = pd.to_datetime(
            self._emp_proj[EmpProjCol.start_date]).dt.date
        self._emp_proj[EmpProjCol.start_date] = self._emp_proj[EmpProjCol.start_date].astype(object).where(
            self._emp_proj[EmpProjCol.start_date].notnull(), None)

        self._emp_proj[EmpProjCol.end_date] = pd.to_datetime(
            self._emp_proj[EmpProjCol.end_date]).dt.date
        self._emp_proj[EmpProjCol.end_date] = self._emp_proj[EmpProjCol.end_date].astype(object).where(
            self._emp_proj[EmpProjCol.end_date].notnull(), None)
        return self._emp_proj

    @property
    def clients(self) -> pd.DataFrame:
        """Get the clients dataframe."""
        if self._clients is not None:
            return self._clients
        self._clients_worksheet = self.staffing_sheet.worksheet(
            FJClientCol.worksheet_name)
        self._clients = pd.DataFrame(
            self._clients_worksheet.get_all_records())
        return self._clients

    @property
    def event_log(self) -> pd.DataFrame:
        """Get the event log dataframe."""
        if self._event_log is not None:
            return self._event_log
        self._event_log_worksheet = self.staffing_sheet.worksheet(
            "ARS Event Log")
        self._event_log = pd.DataFrame(
            self._event_log_worksheet.get_all_records())
        return self._event_log

    # setter for event log
    @event_log.setter
    def event_log(self, event_log_df: pd.DataFrame):
        """Set the event log dataframe."""
        self._event_log = event_log_df

    @property
    def online_courses(self) -> pd.DataFrame:
        """Get the online courses dataframe."""
        if self._online_courses is not None:
            return self._online_courses
        self._online_courses_worksheet = self.staffing_sheet.worksheet(
            OnlineEmpCourseAttemptCol.worksheet_name)
        self._online_courses = pd.DataFrame(
            self._online_courses_worksheet.get_all_records())
        return self._online_courses

    @property
    def offline_courses(self) -> pd.DataFrame:
        """Get the offline courses dataframe."""
        if self._offline_courses is not None:
            return self._offline_courses
        self._offline_courses_worksheet = self.staffing_sheet.worksheet(
            OfflineEmpBatchCol.worksheet_name)
        self._offline_courses = pd.DataFrame(
            self._offline_courses_worksheet.get_all_records())
        return self._offline_courses

    def get_consultant_projects(self) -> list[EmpProj]:
        """Get a list of consultant projects from the consultant projects dataframe."""
        consultant_projects = self.emp_proj.to_dict("records")
        consultant_projects = [EmpProj(*[value for key, value in consultant_project.items(
        ) if key in EmpProjCol._value2member_map_.keys()]) for consultant_project in consultant_projects]
        return consultant_projects

    def get_employees(self) -> list[Employee]:
        """Get a list of employees from the employees dataframe."""
        employees = self.employees.to_dict("records")
        employees = [Employee(*[value for key, value in employee.items(
        ) if key in EmpCol._value2member_map_.keys()]) for employee in employees]
        return employees

    def get_employee(self, emp_name: str) -> Employee | None:
        """Get an employee from the employees"""
        try: employee_values = self.employees[self.employees[EmpCol.emp_name]
                                         == emp_name].to_dict("records")[0]
        except: return None
        employee_values = [value for key, value in employee_values.items(
        ) if key in EmpCol._value2member_map_.keys()]
        return Employee(*employee_values)

    def get_project(self, project: str) -> Project:
        """Get a project from the projects"""
        project_values = self.projects[self.projects[ProjectCol.project_name]
                                       == project].to_dict("records")[0]
        project_values = [value for key, value in project_values.items(
        ) if key in ProjectCol._value2member_map_.keys()]
        return Project(*project_values)

    def get_consultant_project(self, emp_name: str, project_name: str) -> EmpProj:
        """Get a consultant project from the consultant projects"""
        consultant_project_values = self.emp_proj[(self.emp_proj[EmpProjCol.emp_name]
                                                   == emp_name) & (self.emp_proj[EmpProjCol.project] == project_name)].to_dict("records")[0]
        consultant_project_values = [value for key, value in consultant_project_values.items(
        ) if key in EmpProjCol._value2member_map_.keys()]
        return EmpProj(*consultant_project_values)

    def get_client_person(self, client_name) -> FJClient:
        """Get a client from the clients"""
        client_values = self.clients[self.clients[FJClientCol.client_name]
                                     == client_name].to_dict("records")[0]
        client_values = [value for key, value in client_values.items(
        ) if key in FJClientCol._value2member_map_.keys()]
        return FJClient(*client_values)

    def log_event(self, person_acting: str, emp_name: str, action: str, project: str = "", end_date: date | None = None):
        insert_dict = {
            'Date': settings.TODAYS_DATE,
            'Person Acting': person_acting,
            'Consultant': emp_name,
            'Action': action
        }
        if project:
            insert_dict['Project'] = project
        if end_date:
            insert_dict['End date as per R&S Sheet'] = end_date.strftime(
                "%Y-%m-%d")
        new_row = pd.Series(insert_dict)
        # concat the new row to the event log
        self.event_log = pd.concat(
            [self.event_log, new_row], ignore_index=True)  # type: ignore

    # on delete of the db write all the dataframes to the sheets

    def __del__(self):
        """Write all the dataframes to the sheets."""
        if settings.DEPLOYED:
            gspread_dataframe.set_with_dataframe(
                self._event_log_worksheet, self.event_log)
        else:
            print("Not deployed, not writing to sheets.")

    @classmethod
    def refresh(cls):
        """Refresh the database."""
        return cls()


sheet_db = ReviewsDB()
