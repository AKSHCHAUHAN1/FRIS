from fastapi import APIRouter

from app.api.health import ready_router
from app.api.routes import faculty, jobs, reviews

api_router = APIRouter()
api_router.include_router(ready_router)
api_router.include_router(faculty.router, prefix="/faculty", tags=["faculty"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
