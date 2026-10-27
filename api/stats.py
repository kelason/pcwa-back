from fastapi import APIRouter, Depends

from api.deps import get_stats_service
from schemas.stats import StatsResponse
from services.stats_service import StatsService

router = APIRouter(tags=["Stats"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(service: StatsService = Depends(get_stats_service)):
    return service.get_stats()
