"""
配色方案 API 模型（与前端 stores / api/scheme 对齐）
"""
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ColorSchemeItem(BaseModel):
    """
    单层配色项。

    - id: Mapbox 图层 id，用于与地图样式对应；不参与聚类/GA 等数值计算，仅作关联键。
    - color: HEX 颜色。
    - weight: 占比（权重）。
    - semantic: 与分割流水线一致的粗语义类型（五类 + 可选扩展）；便于展示与追溯，计算逻辑可不读取该字段。
    """

    id: str = Field(..., description="图层 id（Mapbox layer id）")
    color: str = Field(..., description="HEX 颜色，如 #RRGGBB")
    weight: float = Field(0.0, ge=0.0, description="占比/权重")
    semantic: Optional[str] = Field(
        None,
        description="粗语义：architecture | roadnet | green | landmark | water 等，与 semantic_assign 五类一致",
    )


class ColorScheme(BaseModel):
    layers: List[ColorSchemeItem]


class SchemeScores(BaseModel):
    semantic_fit: float = Field(0.0, ge=0.0, le=1.0)
    readability: float = Field(0.0, ge=0.0, le=1.0)
    diversity: float = Field(0.0, ge=0.0, le=1.0)
    harmony: Optional[float] = Field(None, ge=0.0, le=1.0, description="色相模板和谐度（GA 双目标之一）")
    place_representativeness: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="地方表征性 overall（对齐 my_work objective1）"
    )


class ColorSchemeWithId(BaseModel):
    id: str
    layers: List[ColorSchemeItem]
    scores: Optional[SchemeScores] = None


class GenerateSchemesRequest(BaseModel):
    currentScheme: ColorScheme
    count: int = Field(5, ge=1, le=20)
    job_id: Optional[str] = None
    population: int = Field(40, ge=8, le=200)
    generations: int = Field(25, ge=1, le=200)
    semantic_mode: Literal["local", "global"] = "local"
    layer_semantics: Dict[str, str] = Field(default_factory=dict)


class GenerateSchemesResponse(BaseModel):
    schemes: List[ColorSchemeWithId]


class PipelineSchemesResponse(BaseModel):
    """从任务产物目录读取已落盘的 scheme JSON。"""

    job_id: str
    schemes: List[ColorSchemeWithId]
