"""
Independent place search service.

Map rendering still uses Mapbox, but text search is resolved through providers
that can return precise POIs and coordinates.
"""
import math
import logging
from typing import Any, Dict, Iterable, List, Optional, Tuple

import httpx

from app.config import settings
from app.models.place import PlaceSearchResult


AMAP_TEXT_SEARCH_URL = "https://restapi.amap.com/v3/place/text"
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
logger = logging.getLogger(__name__)

X_PI = math.pi * 3000.0 / 180.0
PI = math.pi
A = 6378245.0
EE = 0.00669342162296594323


def _transform_lat(lng: float, lat: float) -> float:
    ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat
    ret += 0.2 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * PI) + 40.0 * math.sin(lat / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * PI) + 320 * math.sin(lat * PI / 30.0)) * 2.0 / 3.0
    return ret


def _transform_lng(lng: float, lat: float) -> float:
    ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat
    ret += 0.1 * math.sqrt(abs(lng))
    ret += (20.0 * math.sin(6.0 * lng * PI) + 20.0 * math.sin(2.0 * lng * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * PI) + 40.0 * math.sin(lng / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * PI) + 300.0 * math.sin(lng / 30.0 * PI)) * 2.0 / 3.0
    return ret


def _out_of_china(lng: float, lat: float) -> bool:
    return lng < 72.004 or lng > 137.8347 or lat < 0.8293 or lat > 55.8271


def gcj02_to_wgs84(lng: float, lat: float) -> Tuple[float, float]:
    """Convert GCJ-02 coordinates to WGS84 for Mapbox navigation."""
    if _out_of_china(lng, lat):
        return lng, lat
    dlat = _transform_lat(lng - 105.0, lat - 35.0)
    dlng = _transform_lng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrt_magic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrt_magic) * PI)
    dlng = (dlng * 180.0) / (A / sqrt_magic * math.cos(radlat) * PI)
    mg_lat = lat + dlat
    mg_lng = lng + dlng
    return lng * 2 - mg_lng, lat * 2 - mg_lat


def _coerce_float_pair(value: str) -> Optional[Tuple[float, float]]:
    try:
        lng_s, lat_s = value.split(",", 1)
        lng = float(lng_s.strip())
        lat = float(lat_s.strip())
    except (AttributeError, TypeError, ValueError):
        return None
    if not (-180 <= lng <= 180 and -90 <= lat <= 90):
        return None
    return lng, lat


def _join_nonempty(parts: Iterable[Any], sep: str = " ") -> str:
    return sep.join(str(p).strip() for p in parts if str(p or "").strip())


class PlaceSearchService:
    """Search places with AMap first, then Nominatim fallback."""

    def __init__(self) -> None:
        self.timeout = float(settings.PLACE_SEARCH_TIMEOUT)
        self.user_agent = (
            f"{settings.USER_AGENT} PlaceSenseMap/1.0 "
            "(contact: local-development)"
        )

    async def search(
        self,
        keyword: str,
        limit: int = 10,
        city: Optional[str] = None,
        provider: str = "auto",
    ) -> List[PlaceSearchResult]:
        keyword = keyword.strip()
        provider = (provider or "auto").lower()
        limit = max(1, min(int(limit), 20))

        if not keyword:
            return []
        if provider not in {"auto", "amap", "nominatim"}:
            logger.warning("Unsupported place search provider %r; using auto", provider)
            provider = "auto"

        results: List[PlaceSearchResult] = []
        if provider in ("auto", "amap"):
            results = await self._search_amap(keyword, limit, city)
            if provider == "amap":
                return self._dedupe(results, limit)
            if results:
                return self._dedupe(results, limit)

        if provider in ("auto", "nominatim"):
            results = await self._search_nominatim(keyword, limit)
            return self._dedupe(results, limit)

        return []

    async def _search_amap(
        self,
        keyword: str,
        limit: int,
        city: Optional[str],
    ) -> List[PlaceSearchResult]:
        key = settings.AMAP_WEB_SERVICE_KEY.strip()
        if not key:
            return []

        params: Dict[str, Any] = {
            "key": key,
            "keywords": keyword,
            "offset": str(limit),
            "page": "1",
            "extensions": "base",
            "output": "json",
            "citylimit": "false",
        }
        if city and city.strip():
            params["city"] = city.strip()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(AMAP_TEXT_SEARCH_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            logger.warning("AMap place search failed: %s", exc)
            return []

        if str(payload.get("status")) != "1":
            logger.warning("AMap place search error: %s", payload.get("info") or payload.get("infocode"))
            return []

        items = payload.get("pois") or []
        results: List[PlaceSearchResult] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            parsed = _coerce_float_pair(str(item.get("location") or ""))
            if not parsed:
                continue
            raw_lng, raw_lat = parsed
            lng, lat = gcj02_to_wgs84(raw_lng, raw_lat)
            name = str(item.get("name") or keyword).strip()
            address = item.get("address")
            if isinstance(address, list):
                address = ""
            address_text = _join_nonempty(
                [
                    item.get("pname"),
                    item.get("cityname"),
                    item.get("adname"),
                    address,
                ],
                "",
            )
            place_name = _join_nonempty([name, address_text], " - ") or name
            results.append(
                PlaceSearchResult(
                    id=f"amap:{item.get('id') or len(results)}",
                    name=name,
                    address=address_text or None,
                    place_name=place_name,
                    center=(lng, lat),
                    provider="amap",
                    raw_center=(raw_lng, raw_lat),
                    coordinate_system="GCJ02",
                    type=str(item.get("type") or item.get("typecode") or "") or None,
                    confidence=0.95,
                    properties={
                        "city": item.get("cityname"),
                        "district": item.get("adname"),
                        "typecode": item.get("typecode"),
                    },
                )
            )
        return results

    async def _search_nominatim(self, keyword: str, limit: int) -> List[PlaceSearchResult]:
        params = {
            "format": "jsonv2",
            "q": keyword,
            "limit": str(limit),
            "addressdetails": "1",
        }
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout, headers=headers) as client:
                resp = await client.get(NOMINATIM_SEARCH_URL, params=params)
                resp.raise_for_status()
                payload = resp.json()
        except Exception as exc:
            logger.warning("Nominatim place search failed: %s", exc)
            return []

        results: List[PlaceSearchResult] = []
        for item in payload if isinstance(payload, list) else []:
            if not isinstance(item, dict):
                continue
            try:
                lat = float(item.get("lat"))
                lng = float(item.get("lon"))
            except (TypeError, ValueError):
                continue
            if not (-180 <= lng <= 180 and -90 <= lat <= 90):
                continue
            name = str(item.get("name") or item.get("display_name") or keyword).strip()
            display = str(item.get("display_name") or name).strip()
            importance = item.get("importance")
            try:
                confidence = max(0.0, min(float(importance), 1.0))
            except (TypeError, ValueError):
                confidence = None
            results.append(
                PlaceSearchResult(
                    id=f"nominatim:{item.get('osm_type', 'place')}:{item.get('osm_id') or len(results)}",
                    name=name,
                    address=display if display != name else None,
                    place_name=display or name,
                    center=(lng, lat),
                    provider="nominatim",
                    raw_center=(lng, lat),
                    coordinate_system="WGS84",
                    type=str(item.get("type") or item.get("class") or "") or None,
                    confidence=confidence,
                    properties={
                        "category": item.get("category") or item.get("class"),
                        "osm_type": item.get("osm_type"),
                    },
                )
            )
        return results

    def _dedupe(self, results: List[PlaceSearchResult], limit: int) -> List[PlaceSearchResult]:
        seen = set()
        deduped: List[PlaceSearchResult] = []
        for result in results:
            key = (
                result.provider,
                result.name.strip().lower(),
                round(result.center[0], 5),
                round(result.center[1], 5),
            )
            if key in seen:
                continue
            seen.add(key)
            deduped.append(result)
            if len(deduped) >= limit:
                break
        return deduped
