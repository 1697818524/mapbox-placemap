"""
图片入库服务（上传与URL采集）
"""
from __future__ import annotations

import hashlib
import asyncio
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings
from app.models.image import CollectedImage
from app.utils.ssl_context import get_ssl_context

_executor = ThreadPoolExecutor(max_workers=6)
_SSL_CTX = get_ssl_context()


class ImageIngestService:
    def __init__(self, base_dir: str = "data/ingest") -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _location_dir(self, location: str) -> Path:
        safe_location = location.strip().replace(" ", "_")
        path = self.base_dir / safe_location
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def _file_ext_from_content_type(content_type: Optional[str]) -> str:
        if not content_type:
            return ".jpg"
        mapping = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/tiff": ".tiff",
        }
        return mapping.get(content_type.lower(), ".jpg")

    @staticmethod
    def _is_image_content_type(content_type: Optional[str]) -> bool:
        return bool(content_type and content_type.lower().startswith("image/"))

    @staticmethod
    def _build_image_id(raw: bytes) -> str:
        digest = hashlib.md5(raw).hexdigest()[:12]  # nosec B324 - 非安全用途ID
        return f"img_{digest}"

    async def ingest_uploads(self, location: str, files: List[UploadFile]) -> List[CollectedImage]:
        output_dir = self._location_dir(location)
        results: List[CollectedImage] = []

        for file in files:
            if not self._is_image_content_type(file.content_type):
                continue
            raw = await file.read()
            if not raw:
                continue

            image_id = self._build_image_id(raw)
            ext = Path(file.filename or "").suffix or self._file_ext_from_content_type(file.content_type)
            filename = f"{image_id}{ext.lower()}"
            path = output_dir / filename
            path.write_bytes(raw)

            results.append(
                CollectedImage(
                    image_id=image_id,
                    filename=filename,
                    path=str(path),
                    source="upload",
                )
            )
        return results

    async def ingest_urls(self, location: str, urls: List[str]) -> List[CollectedImage]:
        output_dir = self._location_dir(location)
        semaphore = asyncio.Semaphore(6)

        def _fetch_sync(url: str) -> Optional[CollectedImage]:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": settings.USER_AGENT})
                kwargs = {"timeout": settings.REQUEST_TIMEOUT}
                if url.startswith("https"):
                    kwargs["context"] = _SSL_CTX
                with urllib.request.urlopen(req, **kwargs) as resp:
                    content_type = resp.headers.get("Content-Type")
                    if not self._is_image_content_type(content_type):
                        return None
                    raw = resp.read()
                    if not raw:
                        return None
                    image_id = self._build_image_id(raw)
                    ext = self._file_ext_from_content_type(content_type)
                    filename = f"{image_id}{ext}"
                    path = output_dir / filename
                    path.write_bytes(raw)
                    return CollectedImage(
                        image_id=image_id,
                        filename=filename,
                        path=str(path),
                        source="search",
                        original_url=url,
                    )
            except Exception:
                return None

        async def fetch_one(url: str) -> Optional[CollectedImage]:
            async with semaphore:
                loop = asyncio.get_running_loop()
                return await loop.run_in_executor(_executor, _fetch_sync, url)

        items = await asyncio.gather(*(fetch_one(url) for url in urls))

        seen: set[str] = set()
        results: List[CollectedImage] = []
        for item in items:
            if not item or item.image_id in seen:
                continue
            seen.add(item.image_id)
            results.append(item)

        return results
