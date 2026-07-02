"""
Place search models.
"""
from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, Field


ProviderName = Literal["amap", "nominatim"]
CoordinateSystem = Literal["WGS84", "GCJ02"]


class PlaceSearchResult(BaseModel):
    """Normalized place result consumed by the frontend map search."""

    id: str = Field(..., description="Provider-scoped place id")
    name: str = Field(..., description="Short display name")
    address: Optional[str] = Field(None, description="Human-readable address")
    place_name: str = Field(..., description="Full display label")
    center: Tuple[float, float] = Field(..., description="[lng, lat] in WGS84 for Mapbox")
    provider: ProviderName
    raw_center: Tuple[float, float] = Field(..., description="Original provider [lng, lat]")
    coordinate_system: CoordinateSystem
    type: Optional[str] = Field(None, description="Provider place type/category")
    confidence: Optional[float] = Field(None, ge=0, le=1)
    properties: Dict[str, Any] = Field(default_factory=dict)


class PlaceSearchResponse(BaseModel):
    """Place search response wrapper."""

    keyword: str
    provider: str
    results: List[PlaceSearchResult]
