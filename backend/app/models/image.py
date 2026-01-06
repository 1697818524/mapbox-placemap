"""
图片相关数据模型
"""
from typing import Optional
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
