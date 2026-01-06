"""
图片搜索路由
"""
from typing import List
from fastapi import APIRouter, Query, HTTPException
from app.models.image import ImageResult
from app.services.image_search import ImageSearchService

router = APIRouter(prefix="/api/images", tags=["图片搜索"])

# 创建服务实例
image_search_service = ImageSearchService()


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
