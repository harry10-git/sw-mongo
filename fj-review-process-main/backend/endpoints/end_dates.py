from datetime import datetime
from typing import Annotated
from fastapi import APIRouter
import pandas as pd
from schemas.responses import PostEndDateResponse
from config import settings
from schemas.requests import EndDateRequest
from deps import EmpProjSheetsDB, get_mongo_db, get_sheet_db
from fastapi import Depends
from pymongo.database import Database
import gspread_dataframe
router = APIRouter()


@router.post("/posting_end_date")
async def posting_end_date(end_date_request: EndDateRequest,
                           db: Annotated[Database, Depends(get_mongo_db)],
                           sheet_db: Annotated[EmpProjSheetsDB, Depends(get_sheet_db)]) -> PostEndDateResponse | dict:
    """post the end date"""
    end_date = end_date_request.end_date
    _id = end_date_request.employee_id
    project_id = end_date_request.project_id

    person_projects = db.get_collection("person_projects")

    employee_name = sheet_db.employees_worksheet.cell(
        sheet_db.employees_worksheet.find(_id).row, # type: ignore
        sheet_db.employees_worksheet.find("Name").col # type: ignore
    ).value

    project_name = sheet_db.projects_worksheet.cell(
        sheet_db.projects_worksheet.find(project_id).row, # type: ignore
        sheet_db.projects_worksheet.find("Project Name").col, # type: ignore
    ).value

    partner_approved_end_date_col_num = sheet_db.person_projects_worksheet.find(
        "Partner Approved End Date").col # type: ignore
    partner_approval_requested_col_num = sheet_db.person_projects_worksheet.find(
        "Partner Approval Requested").col # type: ignore
    end_date_col_num = sheet_db.person_projects_worksheet.find("End Date").col # type: ignore

    prev_end_date = None
    partner_name = None
    row_num = 1
    for person_project in person_projects:
        row_num += 1
        if person_project["Role"] == 'Partner' and person_project["Project"] == project_name:
            partner_name = person_project["Person"]

        if person_project["Person"] == employee_name and person_project["Project"] == project_name:
            prev_end_date = person_project["End Date"]

    if not prev_end_date:
        return {"success": "false", "message": "employee not found"}
    try:
        if datetime.strptime(end_date, "%Y-%m-%d").date() < settings.TODAYS_DATE:
            return {"success": "false", "message": "New End date must be sometime in the future"}
    except:
        return {"success": "false", "message": "Date format is not correct"}

    if end_date != prev_end_date:
        sheet_db.person_projects_worksheet.update_cell(
            row_num, end_date_col_num, end_date)
        sheet_db.person_projects_worksheet.update_cell(
            row_num, partner_approval_requested_col_num, '0')
    else:
        sheet_db.person_projects_worksheet.update_cell(
            row_num, partner_approved_end_date_col_num, '1')
        
    event_logs_df = pd.DataFrame(sheet_db.event_logs_worksheet.get_all_records())
    
    new_row = {"Date": settings.TODAYS_DATE,
               "Person Acting": partner_name,
               "Project": project_name,
               "Consultant": employee_name,
               "End date as per R&S Sheet": prev_end_date,
               "Action": "End Date Changed"}
    event_logs_df = event_logs_df.concat([event_logs_df, pd.DataFrame(new_row, index=[0])], ignore_index=True) # type: ignore

    sheet_db.event_logs_worksheet.clear()
    gspread_dataframe.set_with_dataframe(worksheet=sheet_db.event_logs_worksheet,
                                         dataframe=event_logs_df,
                                         include_index=False,
                                         include_column_header=True)

    return {"success": "true"}


@router.get("/get_end_date/{_id}/{project_id}")
async def get_end_date(_id: str, project_id: str,
                       db: Annotated[Database, Depends(get_mongo_db)],
                       sheet_db: Annotated[EmpProjSheetsDB, Depends(get_sheet_db)]):
    """Get an end date"""
    
    person_projects = db.get_collection("person_projects")

    employee_name = sheet_db.employees_worksheet.cell(
        sheet_db.employees_worksheet.find(_id).row, # type: ignore
        sheet_db.employees_worksheet.find("Name").col # type: ignore
    ).value

    project_name = sheet_db.projects_worksheet.cell(
        sheet_db.projects_worksheet.find(project_id).row, # type: ignore
        sheet_db.projects_worksheet.find("Project Name").col,   # type: ignore
    ).value

    end_date = None
    for person_project in person_projects:
        if person_project["Person"] == employee_name and person_project["Project"] == project_name:
            end_date = person_project["End Date"]

    if not end_date: 
        return {"success": "false", "message": "employee not found"}

    return {"employee_name": employee_name, "project_name": project_name, "end_date": end_date, "todays_date": settings.TODAYS_DATE}


@router.get("/confirm_end_date/{_id}/{project_id}")
async def confirm_end_date(_id: str, project_id: str,
                           db: Annotated[Database, Depends(get_mongo_db)],
                           sheet_db: Annotated[EmpProjSheetsDB, Depends(get_sheet_db)]):
    """Get an end date"""
    person_projects = db.get_collection("person_projects")

    employee_name = sheet_db.employees_worksheet.cell(
        sheet_db.employees_worksheet.find(_id).row, # type: ignore
        sheet_db.employees_worksheet.find("Name").col # type: ignore
    ).value

    project_name = sheet_db.projects_worksheet.cell(
        sheet_db.projects_worksheet.find(project_id).row, # type: ignore
        sheet_db.projects_worksheet.find("Project Name").col, # type: ignore
    ).value

    partner_approved_end_date_col_num = sheet_db.person_projects_worksheet.find(
        "Partner Approved End Date").col # type: ignore

    check = False
    partner_name = None
    employee_end_date = None
    row_num = 1
    for person_project in person_projects:
        row_num += 1
        if person_project["Role"] == 'Partner' and person_project["Project"] == project_name:
            partner_name = person_project["Person"]

        if person_project["Person"] == employee_name and person_project["Project"] == project_name:
            employee_end_date = person_project["End Date"]
            sheet_db.person_projects_worksheet.update_cell(
                row_num, partner_approved_end_date_col_num, '1')
            check = True

    if not check:
        return {"success": "false", "message": "employee not found"}

    event_logs_df = gspread_dataframe.get_as_dataframe(sheet_db.event_logs_worksheet)

    event_logs_df = event_logs_df.append({'Date': settings.TODAYS_DATE,
                                          'Person Acting': partner_name,
                                          'Project': project_name,
                                          'Consultant': employee_name,
                                          'End date as per R&S Sheet': employee_end_date,
                                          'Action': 'End Date Confirmed'},
                                         ignore_index=True)

    sheet_db.event_logs_worksheet.clear()
    gspread_dataframe.set_with_dataframe(worksheet=sheet_db.event_logs_worksheet,
                                         dataframe=event_logs_df,
                                         include_index=False,
                                         include_column_header=True)

    return {"success": "true"}


