"""
Pipeline 任务相关数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PipelineJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStageName(str, Enum):
    INGEST = "ingest"
    SHADOW = "shadow"
    SEMANTIC = "semantic"
    SUPERPIXEL = "superpixel"
    CLUSTER = "cluster"
    SCHEME = "scheme"


class ArtifactType(str, Enum):
    INPUT_IMAGE = "input_image"
    SHADOW_IMAGE = "shadow_image"
    SEMANTIC_RAW_ID = "semantic_raw_id"
    SEMANTIC_5CLASS_ID = "semantic_5class_id"
    SUPERPIXEL_LABEL = "superpixel_label"
    RECORD_CSV = "record_csv"
    PALETTE_CSV = "palette_csv"
    SCHEME_JSON = "scheme_json"


class PipelineOptions(BaseModel):
    enable_shadow: bool = True
    enable_semantic: bool = True
    enable_superpixel: bool = True
    enable_cluster: bool = True
    enable_scheme: bool = True
    semantic_model: str = "oneformer_cityscapes"
    slic_n_segments: int = 400
    slic_compactness: float = 10.0
    cluster_k_min: int = 6
    cluster_k_max: int = 20
    scheme_count: int = 5
    # NSGA-II 双目标：和谐度 + 地方表征性（需 cluster 产物）
    enable_ga_scheme: bool = False
    ga_population: int = 40
    ga_generations: int = 25
    scheme_background_semantic: str = "green"


class PipelineJobCreateRequest(BaseModel):
    location: str = Field(..., min_length=1)
    image_ids: List[str] = Field(..., min_length=1, max_length=20)
    options: PipelineOptions = Field(default_factory=PipelineOptions)


class PipelineJobCreateResponse(BaseModel):
    job_id: str
    status: PipelineJobStatus
    message: str = "Pipeline job created"


class PipelineStageProgress(BaseModel):
    stage: PipelineStageName
    status: PipelineJobStatus
    progress: float = Field(default=0, ge=0, le=100)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    message: Optional[str] = None


class PipelineJob(BaseModel):
    job_id: str
    status: PipelineJobStatus
    location: str
    image_ids: List[str]
    options: PipelineOptions
    current_stage: Optional[PipelineStageName] = None
    progress: float = Field(default=0, ge=0, le=100)
    stages: List[PipelineStageProgress] = Field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class PipelineJobDetail(PipelineJob):
    """GET 详情：附带 cluster 调色板文件数量"""

    palette_csv_count: int = Field(0, description="data/jobs/{job_id}/cluster 下 palette_*.csv 数量")


class ArtifactItem(BaseModel):
    artifact_id: str
    type: ArtifactType
    stage: PipelineStageName
    path: str
    url: Optional[str] = None
    image_id: Optional[str] = None
    extra: Dict[str, Any] = Field(default_factory=dict)


class PipelineArtifactsResponse(BaseModel):
    job_id: str
    items: List[ArtifactItem]
