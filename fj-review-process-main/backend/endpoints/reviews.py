import time
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, BackgroundTasks
import pandas as pd
from config import settings
from schemas.requests import PerformanceReviewRequest
from deps import EmpProjSheetsDB, get_mongo_db, get_google_drive
from fastapi import Depends
from pymongo.database import Database
from pydrive2.drive import GoogleDrive
import gspread_dataframe
import json

router = APIRouter()


def upload_review_backup(review: PerformanceReviewRequest, drive: GoogleDrive):
    """upload a backup of the review to google drive"""
    try:
        file = drive.CreateFile({'title': f"review_{review.employee_id}_{review.reviewer_id}_{review.needed_review_id}.json",
                                'mimeType': 'application/json', 'parents': [{'id': settings.BACKUP_FOLDER_ID}]})
        print(f"parent id: {settings.BACKUP_FOLDER_ID}")
        print(f"str contents: {json.dumps(review.dict())}")
        file.SetContentString(json.dumps(review.dict()))
        file.Upload()
        for permission in file.GetPermissions():
            if permission['role'] != 'owner' and permission['emailAddress'] != settings.DRIVE_OWNER_EMAIL:
                file.DeletePermission(permission['id'])
    except Exception as e:
        print(f"Error uploading review backup: {e}")
    
def update_event_logs(needed_review_in_db: dict, sheet_db: EmpProjSheetsDB):
    
    event_logs_df = pd.DataFrame(sheet_db.event_logs_worksheet.get_all_records())
    
    new_row = {'Date': settings.TODAYS_DATE,
                'Person Acting': needed_review_in_db['reviewer_name'],
                'Consultant': needed_review_in_db['employee_name'],
                'Action': 'Review Submitted'}
    if needed_review_in_db.get('project_name'):
        new_row['Project'] = needed_review_in_db['project_name']
    
    # concat instead of append because append is not inplace
    event_logs_df = pd.concat([event_logs_df, pd.DataFrame([new_row])] , ignore_index=True)
    sheet_db.event_logs_worksheet.clear()
    gspread_dataframe.set_with_dataframe(
        worksheet=sheet_db.event_logs_worksheet,
        dataframe=event_logs_df,
        include_index=False,
        include_column_header=True,
    )

@router.post("")
async def create_review(review: PerformanceReviewRequest,
                        db: Annotated[Database, Depends(get_mongo_db)],
                        drive: Annotated[GoogleDrive, Depends(get_google_drive)],
                        sheet_db: Annotated[EmpProjSheetsDB, Depends(EmpProjSheetsDB)],
                        background_tasks: BackgroundTasks):
    """post a new review to the database review collection and remove it from the needed reviews collection"""
    background_tasks.add_task(upload_review_backup, review, drive)

    reviews = db.get_collection("reviews")
    needed_reviews = db.get_collection("needed_reviews")

    # if review already exists in database
    review_in_db = reviews.find_one(
        {
            "needed_review_id": review.needed_review_id,
        }
    )
    # if it is not a needed review
    needed_review_in_db = needed_reviews.find_one(
        {
            "_id": ObjectId(review.needed_review_id),
        }
    )
    if review_in_db or not needed_review_in_db:
        # error already exists in database
        return {"success": "false", "error": "already exists"}

    reviews.insert_one(review.dict())
    # set the status of the needed review to completed
    needed_reviews.update_one(
        {"_id": ObjectId(review.needed_review_id)},
        {"$set": {"status": "completed"}},
    )
    background_tasks.add_task(update_event_logs, needed_review_in_db, sheet_db)
