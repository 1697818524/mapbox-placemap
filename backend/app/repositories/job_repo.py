"""
Pipeline 任务仓储（内存版）
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.pipeline import (
    ArtifactItem,
    PipelineJob,
    PipelineJobCreateRequest,
    PipelineJobStatus,
    PipelineStageName,
    PipelineStageProgress,
)


class JobRepository:
    """简易内存仓储，后续可替换为数据库实现。"""

    def __init__(self, storage_file: str = "data/jobs/_meta/jobs.json") -> None:
        self._jobs: Dict[str, PipelineJob] = {}
        self._artifacts: Dict[str, List[ArtifactItem]] = {}
        self._lock = Lock()
        self._storage_file = Path(storage_file)
        self._storage_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        if not self._storage_file.exists():
            return
        try:
            payload = json.loads(self._storage_file.read_text(encoding="utf-8"))
            jobs_dict = payload.get("jobs", {})
            artifacts_dict = payload.get("artifacts", {})
            self._jobs = {job_id: PipelineJob.model_validate(data) for job_id, data in jobs_dict.items()}
            self._artifacts = {
                job_id: [ArtifactItem.model_validate(item) for item in items]
                for job_id, items in artifacts_dict.items()
            }
        except Exception:
            # 容错：磁盘数据异常时不阻塞服务启动
            self._jobs = {}
            self._artifacts = {}

    def _flush_to_disk(self) -> None:
        payload = {
            "jobs": {job_id: job.model_dump(mode="json") for job_id, job in self._jobs.items()},
            "artifacts": {
                job_id: [artifact.model_dump(mode="json") for artifact in items]
                for job_id, items in self._artifacts.items()
            },
        }
        self._storage_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create_job(self, payload: PipelineJobCreateRequest) -> PipelineJob:
        now = datetime.now()
        job_id = f"job_{now.strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        job = PipelineJob(
            job_id=job_id,
            status=PipelineJobStatus.QUEUED,
            location=payload.location,
            image_ids=payload.image_ids,
            options=payload.options,
            created_at=now,
            updated_at=now,
        )

        with self._lock:
            self._jobs[job_id] = job
            self._artifacts[job_id] = []
            self._flush_to_disk()
        return job

    def get_job(self, job_id: str) -> Optional[PipelineJob]:
        with self._lock:
            return self._jobs.get(job_id)

    def update_job_status(
        self,
        job_id: str,
        status: PipelineJobStatus,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Optional[PipelineJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            now = datetime.now()
            if status == PipelineJobStatus.RUNNING and not job.started_at:
                job.started_at = now
            if status in (PipelineJobStatus.SUCCEEDED, PipelineJobStatus.FAILED, PipelineJobStatus.CANCELLED):
                job.finished_at = now

            job.status = status
            job.error_code = error_code
            job.error_message = error_message
            job.updated_at = now
            self._flush_to_disk()
            return job

    def update_stage(
        self,
        job_id: str,
        stage: PipelineStageName,
        status: PipelineJobStatus,
        progress: float,
        message: Optional[str] = None,
    ) -> Optional[PipelineJob]:
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None

            now = datetime.now()
            target = None
            for stage_item in job.stages:
                if stage_item.stage == stage:
                    target = stage_item
                    break

            if target is None:
                target = PipelineStageProgress(
                    stage=stage,
                    status=status,
                    progress=progress,
                    started_at=now if status == PipelineJobStatus.RUNNING else None,
                    message=message,
                )
                job.stages.append(target)
            else:
                target.status = status
                target.progress = progress
                target.message = message
                if status == PipelineJobStatus.RUNNING and not target.started_at:
                    target.started_at = now

            if status in (PipelineJobStatus.SUCCEEDED, PipelineJobStatus.FAILED, PipelineJobStatus.CANCELLED):
                target.finished_at = now

            job.current_stage = stage
            job.progress = progress if status == PipelineJobStatus.RUNNING else job.progress
            job.updated_at = now
            self._flush_to_disk()
            return job

    def add_artifact(self, job_id: str, artifact: ArtifactItem) -> bool:
        with self._lock:
            if job_id not in self._jobs:
                return False
            self._artifacts[job_id].append(artifact)
            self._flush_to_disk()
            return True

    def list_artifacts(self, job_id: str) -> List[ArtifactItem]:
        with self._lock:
            return list(self._artifacts.get(job_id, []))


def ensure_job_dirs(job_id: str, base_dir: str = "data/jobs") -> Dict[str, str]:
    """初始化单个 job 的产物目录结构。"""
    root = Path(base_dir) / job_id
    dirs = {
        "root": root,
        "input": root / "input",
        "shadow": root / "shadow",
        "semantic_raw": root / "semantic_raw",
        "semantic_5class": root / "semantic_5class",
        "superpixel": root / "superpixel",
        "records": root / "records",
        "cluster": root / "cluster",
        "schemes": root / "schemes",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return {key: str(value) for key, value in dirs.items()}
