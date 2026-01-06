"""
数据模型模块
"""
from .image import ImageResult
from .common import APIResponse, ErrorResponse

__all__ = [
    "ImageResult",
    "APIResponse",
    "ErrorResponse",
]
