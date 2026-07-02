"""
Place search routes.
"""
from typing import List

from fastapi import APIRouter, Query

from app.config import settings
from app.models.place import PlaceSearchResult
from app.services.place_search import PlaceSearchService


router = APIRouter(prefix="/api/places", tags=["place search"])

place_search_service = PlaceSearchService()


@router.get(
    "/search",
    response_model=List[PlaceSearchResult],
    summary="Search places",
    description="Search POIs/streets independently of Mapbox and return Mapbox-ready WGS84 coordinates.",
)
async def search_places(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    limit: int = Query(default=10, ge=1, le=20, description="Maximum result count"),
    city: str = Query(default="", description="Optional city hint for AMap"),
    provider: str = Query(default="auto", pattern="^(auto|amap|nominatim)$", description="auto, amap, or nominatim"),
) -> List[PlaceSearchResult]:
    selected_provider = provider.strip() or settings.PLACE_SEARCH_PROVIDER
    return await place_search_service.search(
        keyword=keyword,
        limit=limit,
        city=city or None,
        provider=selected_provider,
    )
