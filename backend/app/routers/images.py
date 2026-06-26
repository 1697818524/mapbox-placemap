"""
图片搜索路由
"""
import asyncio
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor
from typing import List
from urllib.parse import urlparse

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

from app.models.common import ErrorResponse
from app.models.image import (
    ImageCollectRequest,
    ImageCollectResponse,
    ImageResult,
)
from app.services.image_ingest import ImageIngestService
from app.services.image_search import ImageSearchService
from app.utils.ssl_context import get_ssl_context

router = APIRouter(prefix="/api/images", tags=["图片搜索"])

_executor = ThreadPoolExecutor(max_workers=4)
_SSL_CTX = get_ssl_context()

# 单次上传 / URL 采集与 pipeline 批次上限对齐（见 PipelineJobCreateRequest）
MAX_IMAGES_PER_BATCH = 20

# 经代理拉取的外链图最大体积（避免内存滥用）
_MAX_PROXY_IMAGE_BYTES = 8 * 1024 * 1024

# 仅允许搜索源常见图床（防 SSRF）；需扩展时在此追加后缀
_ALLOWED_IMAGE_PROXY_SUFFIXES = (
    "baidu.com",
    "bdstatic.com",
    "bdimg.com",
    "wikimedia.org",
)


def _proxy_host_allowed(hostname: str) -> bool:
    h = (hostname or "").lower().rstrip(".")
    for suf in _ALLOWED_IMAGE_PROXY_SUFFIXES:
        if h == suf or h.endswith("." + suf):
            return True
    return False


# 创建服务实例
image_search_service = ImageSearchService()
image_ingest_service = ImageIngestService()


@router.get(
    "/proxy",
    summary="外链图片代理",
    description="同源代理展示用图片，绕过部分图床 Referer 限制；采集入库仍请使用原始 URL",
    response_class=Response,
)
async def proxy_remote_image(
    url: str = Query(..., min_length=12, max_length=4096, description="原始图片 URL"),
) -> Response:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="仅允许 http(s) URL")
    host = parsed.hostname or ""
    if not _proxy_host_allowed(host):
        raise HTTPException(status_code=403, detail="该域名不允许经代理访问")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": f"{parsed.scheme}://{host}/",
    }
    try:
        loop = asyncio.get_running_loop()

        def _fetch():
            req = urllib.request.Request(url, headers=headers)
            kwargs = {"timeout": 25.0}
            if url.startswith("https"):
                kwargs["context"] = _SSL_CTX
            with urllib.request.urlopen(req, **kwargs) as resp:
                ct = resp.headers.get("Content-Type") or "image/jpeg"
                body = resp.read()
                return body, ct

        body, content_type = await loop.run_in_executor(_executor, _fetch)
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"拉取图片失败: {e!s}") from e
    except urllib.error.URLError as e:
        raise HTTPException(status_code=502, detail=f"拉取图片失败: {e!s}") from e

    if len(body) > _MAX_PROXY_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="图片过大")

    ct = (content_type or "image/jpeg").split(";")[0].strip()
    if ct and not (ct.startswith("image/") or ct == "application/octet-stream"):
        raise HTTPException(status_code=502, detail="响应不是图片类型")

    return Response(content=body, media_type=ct or "image/jpeg")


@router.get(
    "/search",
    response_model=List[ImageResult],
    summary="搜索图片",
    description="基于关键词搜索相关图片（百度图片搜索）",
    responses={
        200: {
            "description": "成功返回图片列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "url": "https://example.com/image.jpg",
                            "thumbnail": "https://example.com/thumb.jpg",
                            "title": "风景图片",
                            "width": 1920,
                            "height": 1080,
                        }
                    ]
                }
            },
        },
        500: {"description": "服务器错误"},
    },
)
async def search_images(
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    count: int = Query(default=9, ge=1, le=50, description="返回图片数量"),
) -> List[ImageResult]:
    """
    搜索图片接口

    Args:
        keyword: 搜索关键词
        count: 返回图片数量（1-50）

    Returns:
        图片搜索结果列表（直接返回数组，符合前端期望）
    """
    try:
        print(f"\n[API路由] 收到图片搜索请求")
        print(f"[API路由] 参数 - keyword: {keyword}, count: {count}")

        # 调用搜索服务
        images = await image_search_service.search(keyword, count)

        # 详细的API响应日志
        print(f"[API路由] 服务返回结果: {len(images)} 张图片")
        if images:
            print(f"[API路由] ✓ 准备返回给前端:")
            for idx, img in enumerate(images[:3], 1):  # 只显示前3张
                # HttpUrl 对象需要转换为字符串才能切片
                url_str = str(img.url)
                print(f"  [{idx}] {url_str[:80]}...")
        else:
            print(f"[API路由] ✗ 返回空列表，前端将显示无图片")

        print(f"[API路由] 响应状态: 200 OK\n")

        return images

    except Exception as e:
        import traceback
        print(f"\n[API路由] ✗ 搜索图片异常: {str(e)}")
        traceback.print_exc()
        print()
        raise HTTPException(
            status_code=500,
            detail=f"搜索图片失败: {str(e)}",
        )


@router.post(
    "/upload",
    response_model=ImageCollectResponse,
    summary="上传图片入库",
    description="上传本地图片并存储到后端数据目录，返回 image_ids",
)
async def upload_images(
    location: str = Query(..., min_length=1, description="地点名"),
    files: List[UploadFile] = File(..., description="图片文件列表"),
) -> ImageCollectResponse:
    if len(files) > MAX_IMAGES_PER_BATCH:
        err = ErrorResponse(
            success=False,
            message=f"单次最多上传 {MAX_IMAGES_PER_BATCH} 张图片",
            error_code="IMAGE_UPLOAD_TOO_MANY",
        )
        raise HTTPException(status_code=400, detail=err.model_dump())
    if not files:
        err = ErrorResponse(
            success=False,
            message="未上传任何文件",
            error_code="IMAGE_UPLOAD_EMPTY",
        )
        raise HTTPException(status_code=400, detail=err.model_dump())

    items = await image_ingest_service.ingest_uploads(location, files)
    if not items:
        err = ErrorResponse(
            success=False,
            message="未识别到有效图片文件",
            error_code="IMAGE_UPLOAD_INVALID",
        )
        raise HTTPException(status_code=400, detail=err.model_dump())

    return ImageCollectResponse(
        location=location,
        image_ids=[item.image_id for item in items],
        items=items,
    )


@router.post(
    "/collect",
    response_model=ImageCollectResponse,
    summary="采集搜索图片入库",
    description="接收图片URL列表并下载到后端数据目录，返回 image_ids",
)
async def collect_images(payload: ImageCollectRequest) -> ImageCollectResponse:
    items = await image_ingest_service.ingest_urls(
        payload.location,
        [str(url) for url in payload.urls],
    )
    if not items:
        err = ErrorResponse(
            success=False,
            message="采集失败，未下载到有效图片",
            error_code="IMAGE_COLLECT_FAILED",
        )
        raise HTTPException(status_code=400, detail=err.model_dump())

    return ImageCollectResponse(
        location=payload.location,
        image_ids=[item.image_id for item in items],
        items=items,
    )
