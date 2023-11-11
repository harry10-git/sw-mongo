from datetime import datetime, timedelta
from typing import Annotated
from fastapi import APIRouter
from schemas.responses import ProcessStat, ProcessStatsResponse
from deps import get_mongo_db
from fastapi import Depends
from pymongo.database import Database

router = APIRouter()


@router.get("/process_stats")
async def get_process_stats(
        db: Annotated[Database, Depends(get_mongo_db)]) -> ProcessStatsResponse:
    """Get the number of completed and incomplete reviews for each process type"""
    needed_reviews = db.get_collection("needed_reviews")
    six_months_ago = (datetime.now() - timedelta(days=180)
                      ).strftime("%Y-%m-%d")

    process_stats = ProcessStatsResponse(
        partner=ProcessStat(incomplete=needed_reviews.count_documents({"type": "partner", "status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                            complete=needed_reviews.count_documents({"type": "partner", "status": "complete", "created_at": {"$gte": six_months_ago}})),
        staff=ProcessStat(incomplete=needed_reviews.count_documents({"type": "staff", "status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                          complete=needed_reviews.count_documents({"type": "staff", "status": "complete", "created_at": {"$gte": six_months_ago}})),
        self=ProcessStat(incomplete=needed_reviews.count_documents({"type": "self", "status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                         complete=needed_reviews.count_documents({"type": "self", "status": "complete", "created_at": {"$gte": six_months_ago}})),
        manager=ProcessStat(incomplete=needed_reviews.count_documents({"type": "manager", "status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                            complete=needed_reviews.count_documents({"type": "manager", "status": "complete", "created_at": {"$gte": six_months_ago}})),
        external=ProcessStat(incomplete=needed_reviews.count_documents({"type": "external", "status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                             complete=needed_reviews.count_documents({"type": "external", "status": "complete", "created_at": {"$gte": six_months_ago}})),
        total=ProcessStat(incomplete=needed_reviews.count_documents({"status": "incomplete", "created_at": {"$gte": six_months_ago}}),
                          complete=needed_reviews.count_documents({"status": "complete", "created_at": {"$gte": six_months_ago}}))
    )
    return process_stats
