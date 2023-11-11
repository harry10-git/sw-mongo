from datetime import date, datetime
from typing import Annotated
from bson import ObjectId
from fastapi import APIRouter, HTTPException
from schemas.responses import NeededReviewResponse
from deps import EmpProjSheetsDB, get_mongo_db, get_sheet_db
from fastapi import Depends
from pymongo.database import Database

router = APIRouter()


@router.get("/{reviewer_id}")
async def get_needed_reviews(reviewer_id: str,
                             db: Annotated[Database, Depends(get_mongo_db)]) -> list[NeededReviewResponse]:
    """Get all needed reviews for a specific reviewer"""
    needed_reviews_list: list[NeededReviewResponse] = []
    for needed_review in db.get_collection("needed_reviews").find({"reviewer_id": reviewer_id, "status": {"$nin": ["completed", "expired"]}}):

        needed_review["id"] = str(needed_review["_id"])
        needed_review.pop("_id")
        needed_review["title"] = get_title(needed_review["type"])

        needed_reviews_list.append(needed_review)

    return needed_reviews_list


@router.get("/review/{_id}")
async def get_needed_review(_id: str,
                            db: Annotated[Database, Depends(get_mongo_db)]) -> NeededReviewResponse | dict[str, str]:
    """Get a specific needed review"""
    needed_reviews = db.get_collection("needed_reviews")
    needed_review = needed_reviews.find_one({"_id": ObjectId(_id)})

    if not needed_review:
        return {"success": "false", "message": "Review does not exist"}

    # if review has a status field
    # and the status is not "completed" or "expired"
    # return the needed review
    if "status" in needed_review and needed_review["status"] in ["completed", "expired"]:
        return {"success": "false", "message": "Review has already been completed or has expired"}

    # convert ObjectId to string for json serialization
    needed_review["id"] = _id
    needed_review.pop("_id")
    needed_review["title"] = get_title(needed_review["type"])

    return needed_review

@router.get("/completed/{reviewer_id}")
async def get_completed_reviews(reviewer_id: str,
                                db: Annotated[Database, Depends(get_mongo_db)],
                                min_date: date | None = None,
                                max_date: date | None = None,
                                ) -> list[NeededReviewResponse]:
    """Get all completed reviews for a specific reviewer"""
    completed_reviews_list: list[NeededReviewResponse] = []
    if min_date and max_date:
        query = {"reviewer_id": reviewer_id, "status": "completed", "created_at": {"$gte": datetime.combine(
            min_date, datetime.min.time()), "$lte": datetime.combine(max_date, datetime.max.time())}}
    elif min_date:
        query = {"reviewer_id": reviewer_id, "status": "completed", "created_at": {
            "$gte": datetime.combine(min_date, datetime.min.time())}}
    elif max_date:
        query = {"reviewer_id": reviewer_id, "status": "completed", "created_at": {
            "$lte": datetime.combine(max_date, datetime.max.time())}}
    else:
        query = {"reviewer_id": reviewer_id, "status": "completed"}

    for needed_review in db.get_collection("needed_reviews").find(query):
        needed_review["id"] = str(needed_review["_id"])
        needed_review.pop("_id")
        needed_review["title"] = get_title(needed_review["type"])
        completed_reviews_list.append(needed_review)

    return completed_reviews_list


@router.get("/fields/{_id}")
async def get_needed_review_fields(_id: str,
                                   db: Annotated[Database, Depends(get_mongo_db)],
                                   sheet_db: Annotated[EmpProjSheetsDB, Depends(get_sheet_db)]):
    """Get the fields for a specific review
    based on the review type
    from a google sheet
    """
    # get needed review
    needed_review = db.get_collection(
        "needed_reviews").find_one({"_id": ObjectId(_id)})
    if not needed_review:
        raise HTTPException(status_code=404, detail="Review not found")

    match needed_review['type']:
        case "staff": worksheet_name = "Staff"
        case "manager": worksheet_name = "Manager"
        case "partner": worksheet_name = "Partner"
        case "external": worksheet_name = "External"
        case "self": worksheet_name = "Self"
        case _: worksheet_name = ""

    fields = sheet_db.service_account.open("Performance Review Settings").worksheet(
        worksheet_name).get_all_records()

    # return fields as json
    return fields


def get_title(needed_review_type: str) -> str:
    """Get the title of the review based on the db type"""
    match needed_review_type:
        case "internal": return "Internal Review"
        case "external": return "External Review"
        case "self": return "Self Appraisal"
        case "staff": return "Staff Review"
        case "manager": return "Manager Review"
        case "partner": return "Partner Review"
        case _: return "Unknown Review"
