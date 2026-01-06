"""
图片处理工具函数
"""
import httpx
from typing import Optional
from PIL import Image
from io import BytesIO
from app.config import settings


async def download_image(url: str) -> Optional[Image.Image]:
    """
    下载图片

    Args:
        url: 图片URL

    Returns:
        PIL Image 对象，失败返回 None
    """
    try:
        async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
            response = await client.get(
                url,
                headers={"User-Agent": settings.USER_AGENT},
                follow_redirects=True,
            )
            response.raise_for_status()

            # 验证内容类型
            content_type = response.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                return None

            # 打开图片
            image = Image.open(BytesIO(response.content))
            return image
    except Exception as e:
        print(f"下载图片失败 {url}: {e}")
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
