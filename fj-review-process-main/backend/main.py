"""API for the performance review process"""
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import endpoints.needed_reviews
import endpoints.others
import endpoints.reviews
import endpoints.end_dates

app = FastAPI(
    title="Performance Review API",
    description="API for the performance review process",
    docs_url="/",
    version="0.1.0",
)

api_router = APIRouter()
api_router.include_router(
    endpoints.needed_reviews.router,
    prefix="/needed_reviews",
    tags=["Needed Reviews"],
)
api_router.include_router(
    endpoints.others.router,
    prefix="",
    tags=["Others"],
)
api_router.include_router(
    endpoints.reviews.router,
    prefix="/reviews",
    tags=["Reviews"],
)
api_router.include_router(
    endpoints.end_dates.router,
    prefix="",
    tags=["End Dates"],
)
app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
