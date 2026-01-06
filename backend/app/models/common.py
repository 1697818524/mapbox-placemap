"""
通用数据模型
"""
from typing import Any, Optional
from pydantic import BaseModel


class APIResponse(BaseModel):
    """统一 API 响应格式"""

    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """错误响应格式"""

    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[Any] = None
