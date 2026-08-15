from fastapi import APIRouter
from app.api.routes.activities import router as activities_router
from app.api.routes.integrations import router as integrations_router

api_router = APIRouter()
api_router.include_router(integrations_router, prefix="/integrations", tags=["integrations"])
api_router.include_router(activities_router, prefix="/activities", tags=["activities"])
