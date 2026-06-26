"""
图片处理工具函数
"""
import urllib.request
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from PIL import Image
from io import BytesIO
from app.config import settings
from app.utils.ssl_context import get_ssl_context

_executor = ThreadPoolExecutor(max_workers=4)
_SSL_CTX = get_ssl_context()


def _download_sync(url: str) -> Optional[bytes]:
    """同步下载图片，返回原始字节。"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": settings.USER_AGENT})
        kwargs = {"timeout": settings.REQUEST_TIMEOUT}
        if url.startswith("https"):
            kwargs["context"] = _SSL_CTX
        with urllib.request.urlopen(req, **kwargs) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if not content_type.startswith("image/"):
                return None
            return resp.read()
    except Exception as e:
        print(f"下载图片失败 {url}: {e}")
        return None


async def download_image(url: str) -> Optional[Image.Image]:
    """
    下载图片

    Args:
        url: 图片URL

    Returns:
        PIL Image 对象，失败返回 None
    """
    loop = asyncio.get_running_loop()
    data = await loop.run_in_executor(_executor, _download_sync, url)
    if data is None:
        return None
    try:
        return Image.open(BytesIO(data))
    except Exception as e:
        print(f"打开图片失败 {url}: {e}")
        return None


def resize_image(image: Image.Image, max_size: int = None) -> Image.Image:
    """
    调整图片大小

    Args:
        image: PIL Image 对象
        max_size: 最大尺寸（像素），默认使用配置中的值

    Returns:
        调整后的图片
    """
    if max_size is None:
        max_size = settings.MAX_IMAGE_SIZE

    if image.width <= max_size and image.height <= max_size:
        return image

    # 计算缩放比例
    ratio = min(max_size / image.width, max_size / image.height)
    new_width = int(image.width * ratio)
    new_height = int(image.height * ratio)

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def validate_image_format(image: Image.Image) -> bool:
    """
    验证图片格式

    Args:
        image: PIL Image 对象

    Returns:
        是否为有效格式
    """
    valid_formats = {"JPEG", "PNG", "WEBP", "GIF"}
    return image.format in valid_formats
