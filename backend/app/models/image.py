"""
图片相关数据模型
"""
from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ImageResult(BaseModel):
    """图片搜索结果模型"""

    url: HttpUrl = Field(..., description="图片URL")
    thumbnail: Optional[HttpUrl] = Field(None, description="缩略图URL")
    title: Optional[str] = Field(None, description="图片标题")
    width: Optional[int] = Field(None, description="图片宽度")
    height: Optional[int] = Field(None, description="图片高度")

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://example.com/image.jpg",
                "thumbnail": "https://example.com/thumb.jpg",
                "title": "风景图片",
                "width": 1920,
                "height": 1080,
            }
        }


class CollectedImage(BaseModel):
    """已入库图片信息"""

    image_id: str = Field(..., description="图片ID")
    filename: str = Field(..., description="文件名")
    path: str = Field(..., description="本地存储路径")
    source: str = Field(..., description="来源(upload/search)")
    original_url: Optional[HttpUrl] = Field(None, description="原始URL")


class ImageCollectRequest(BaseModel):
    """搜索结果采集请求"""

    location: str = Field(..., min_length=1, description="地点名")
    urls: List[HttpUrl] = Field(
        ...,
        min_length=1,
        max_length=20,
        description="待采集图片 URL，单次最多 20 张",
    )


class ImageCollectResponse(BaseModel):
    """图片采集响应"""

    location: str
    image_ids: List[str]
    items: List[CollectedImage]
