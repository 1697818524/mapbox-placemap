"""
Pipeline 任务路由
"""
from __future__ import annotations

import json
from pathlib import Path
import csv
from uuid import uuid4

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from app.models.common import ErrorResponse
from app.models.pipeline import (
    ArtifactItem,
    ArtifactType,
    PipelineArtifactsResponse,
    PipelineJob,
    PipelineJobCreateRequest,
    PipelineJobCreateResponse,
    PipelineJobDetail,
    PipelineJobStatus,
    PipelineStageName,
)
from app.models.scheme import ColorSchemeWithId, PipelineSchemesResponse
from app.repositories.job_repo import JobRepository, ensure_job_dirs
from app.services.semantic_segment import SemanticSegmentService
from app.services.palette_cluster import PaletteClusterService
from app.services.semantic_assign import SemanticAssignService
from app.services.shadow_process import ShadowProcessService
from app.services.superpixel import SuperpixelService
from app.services.scheme_generate import SchemeGenerateService, default_color_scheme
from app.services.ga_optimize import run_nsga2_schemes

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])

job_repository = JobRepository()
shadow_service = ShadowProcessService()
semantic_service = SemanticSegmentService()
superpixel_service = SuperpixelService()
semantic_assign_service = SemanticAssignService()
palette_cluster_service = PaletteClusterService()
scheme_generate_service = SchemeGenerateService()


def _raise_job_not_found(job_id: str) -> None:
    err = ErrorResponse(
        success=False,
        message=f"Job not found: {job_id}",
        error_code="PIPELINE_JOB_NOT_FOUND",
    )
    raise HTTPException(status_code=404, detail=err.model_dump())


@router.post("/jobs", response_model=PipelineJobCreateResponse, summary="创建 pipeline 任务")
async def create_pipeline_job(payload: PipelineJobCreateRequest) -> PipelineJobCreateResponse:
    job = job_repository.create_job(payload)
    ensure_job_dirs(job.job_id)
    return PipelineJobCreateResponse(job_id=job.job_id, status=job.status)


@router.get("/jobs/{job_id}", response_model=PipelineJobDetail, summary="查询 pipeline 任务状态")
async def get_pipeline_job(job_id: str) -> PipelineJobDetail:
    job = job_repository.get_job(job_id)
    if not job:
        _raise_job_not_found(job_id)
    palette_n = _palette_csv_count(job_id)
    return PipelineJobDetail(**job.model_dump(), palette_csv_count=palette_n)


@router.get("/jobs/{job_id}/artifacts", response_model=PipelineArtifactsResponse, summary="查询任务产物")
async def get_pipeline_artifacts(job_id: str) -> PipelineArtifactsResponse:
    job = job_repository.get_job(job_id)
    if not job:
        _raise_job_not_found(job_id)

    items = job_repository.list_artifacts(job_id)
    return PipelineArtifactsResponse(job_id=job_id, items=items)


@router.get("/jobs/{job_id}/schemes", response_model=PipelineSchemesResponse, summary="读取任务已生成的配色方案 JSON")
async def get_pipeline_job_schemes(job_id: str) -> PipelineSchemesResponse:
    job = job_repository.get_job(job_id)
    if not job:
        _raise_job_not_found(job_id)

    schemes: list[ColorSchemeWithId] = []
    for art in job_repository.list_artifacts(job_id):
        if art.type != ArtifactType.SCHEME_JSON:
            continue
        try:
            path = Path(art.path)
            if not path.is_file():
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            schemes.append(ColorSchemeWithId.model_validate(raw))
        except Exception:
            continue

    schemes.sort(key=lambda s: s.id)
    return PipelineSchemesResponse(job_id=job_id, schemes=schemes)


@router.post("/jobs/{job_id}/mock-start", response_model=PipelineJob, summary="模拟启动任务（开发调试）")
async def mock_start_job(job_id: str) -> PipelineJob:
    job = job_repository.update_job_status(job_id, PipelineJobStatus.RUNNING)
    if not job:
        _raise_job_not_found(job_id)
    return job


def _palette_csv_count(job_id: str) -> int:
    cluster_dir = Path("data/jobs") / job_id / "cluster"
    if not cluster_dir.is_dir():
        return 0
    return len(list(cluster_dir.glob("palette_*.csv")))


def _process_shadow_semantic_one(
    image_id: str,
    src_path: str,
    dirs: dict[str, str],
    enable_shadow: bool,
    enable_semantic: bool,
) -> tuple[str, str, str | None, ArtifactItem | None, ArtifactItem | None]:
    """
    单张图：可选去阴影 → 可选语义分割。
    返回 (image_id, 后续超像素用的 RGB 底图路径, 语义 png 路径或 None, shadow 产物, semantic 产物)。
    """
    input_for_semantic = src_path
    shadow_art: ArtifactItem | None = None
    sem_art: ArtifactItem | None = None
    sem_png_path: str | None = None

    if enable_shadow:
        src_ext = Path(src_path).suffix.lower() or ".png"
        shadow_path = str(Path(dirs["shadow"]) / f"{image_id}{src_ext}")
        level = shadow_service.process_to_path(src_path, shadow_path)
        input_for_semantic = shadow_path
        shadow_art = ArtifactItem(
            artifact_id=f"art_{uuid4().hex[:10]}",
            type=ArtifactType.SHADOW_IMAGE,
            stage=PipelineStageName.SHADOW,
            path=shadow_path,
            image_id=image_id,
            extra={"level": level},
        )

    if enable_semantic:
        sem_png_path = str(Path(dirs["semantic_raw"]) / f"{image_id}.png")
        semantic_service.run_on_image(input_for_semantic, sem_png_path)
        sem_art = ArtifactItem(
            artifact_id=f"art_{uuid4().hex[:10]}",
            type=ArtifactType.SEMANTIC_RAW_ID,
            stage=PipelineStageName.SEMANTIC,
            path=sem_png_path,
            image_id=image_id,
        )

    return image_id, input_for_semantic, sem_png_path, shadow_art, sem_art


def _resolve_image_path(location: str, image_id: str) -> str | None:
    base = Path("data/ingest") / location
    if not base.exists():
        return None
    matches = list(base.glob(f"{image_id}.*"))
    if not matches:
        return None
    return str(matches[0])


def _execute_pipeline_job(job_id: str) -> None:
    """实际执行各阶段；调用前应将任务置为 RUNNING。"""
    job = job_repository.get_job(job_id)
    if not job:
        return

    dirs = ensure_job_dirs(job_id)
    total = len(job.image_ids)
    if total == 0:
        job_repository.update_job_status(
            job_id,
            PipelineJobStatus.FAILED,
            error_code="PIPELINE_INVALID_OPTIONS",
            error_message="No image_ids provided",
        )
        return

    # Stage 1: ingest resolve
    job_repository.update_stage(job_id, PipelineStageName.INGEST, PipelineJobStatus.RUNNING, 0, "Resolving input images")
    resolved = []
    for image_id in job.image_ids:
        src = _resolve_image_path(job.location, image_id)
        if src:
            resolved.append((image_id, src))
            job_repository.add_artifact(
                job_id,
                ArtifactItem(
                    artifact_id=f"art_{uuid4().hex[:10]}",
                    type=ArtifactType.INPUT_IMAGE,
                    stage=PipelineStageName.INGEST,
                    path=src,
                    image_id=image_id,
                ),
            )
    if not resolved:
        job_repository.update_stage(
            job_id,
            PipelineStageName.INGEST,
            PipelineJobStatus.FAILED,
            0,
            "No input images resolved from image_ids",
        )
        job_repository.update_job_status(
            job_id,
            PipelineJobStatus.FAILED,
            error_code="PIPELINE_STAGE_FAILED",
            error_message="No valid input images found",
        )
        return

    job_repository.update_stage(job_id, PipelineStageName.INGEST, PipelineJobStatus.SUCCEEDED, 100, "Input resolved")

    # Stage 2–3: shadow + semantic（多图并行；单图内仍为先 shadow 再 semantic）
    shadow_outputs: dict[str, str] = {}
    semantic_outputs: dict[str, str] = {}
    enable_shadow = job.options.enable_shadow
    enable_semantic = job.options.enable_semantic

    if not enable_shadow and not enable_semantic:
        for image_id, src_path in resolved:
            shadow_outputs[image_id] = src_path
    else:
        if enable_shadow:
            job_repository.update_stage(
                job_id,
                PipelineStageName.SHADOW,
                PipelineJobStatus.RUNNING,
                0,
                "Running shadow enhancement (parallel)",
            )
        if enable_semantic:
            job_repository.update_stage(
                job_id,
                PipelineStageName.SEMANTIC,
                PipelineJobStatus.RUNNING,
                0,
                "Running semantic segmentation (parallel)",
            )

        max_workers = max(1, min(len(resolved), 8, os.cpu_count() or 4))
        completed = 0
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                futures = [
                    pool.submit(
                        _process_shadow_semantic_one,
                        image_id,
                        src_path,
                        dirs,
                        enable_shadow,
                        enable_semantic,
                    )
                    for image_id, src_path in resolved
                ]
                for fut in as_completed(futures):
                    image_id, input_superpixel, sem_png, shadow_art, sem_art = fut.result()
                    shadow_outputs[image_id] = input_superpixel
                    if sem_png:
                        semantic_outputs[image_id] = sem_png
                    if shadow_art:
                        job_repository.add_artifact(job_id, shadow_art)
                    if sem_art:
                        job_repository.add_artifact(job_id, sem_art)
                    completed += 1
                    pct = (completed / total) * 100.0
                    if enable_shadow:
                        job_repository.update_stage(
                            job_id,
                            PipelineStageName.SHADOW,
                            PipelineJobStatus.RUNNING,
                            pct,
                            "Shadow (parallel)",
                        )
                    if enable_semantic:
                        job_repository.update_stage(
                            job_id,
                            PipelineStageName.SEMANTIC,
                            PipelineJobStatus.RUNNING,
                            pct,
                            "Semantic (parallel)",
                        )
        except Exception as exc:
            fail_stage = PipelineStageName.SHADOW if enable_shadow else PipelineStageName.SEMANTIC
            job_repository.update_stage(
                job_id,
                fail_stage,
                PipelineJobStatus.FAILED,
                100.0,
                f"Shadow/semantic parallel stage failed: {exc}",
            )
            job_repository.update_job_status(
                job_id,
                PipelineJobStatus.FAILED,
                error_code="PIPELINE_STAGE_FAILED",
                error_message=f"Shadow/semantic failed: {exc}",
            )
            return

        if enable_shadow:
            job_repository.update_stage(
                job_id,
                PipelineStageName.SHADOW,
                PipelineJobStatus.SUCCEEDED,
                100,
                "Shadow done",
            )
        if enable_semantic:
            job_repository.update_stage(
                job_id,
                PipelineStageName.SEMANTIC,
                PipelineJobStatus.SUCCEEDED,
                100,
                "Semantic done",
            )

    # Stage 4: superpixel + semantic assign
    all_records = []
    if job.options.enable_superpixel:
        job_repository.update_stage(
            job_id,
            PipelineStageName.SUPERPIXEL,
            PipelineJobStatus.RUNNING,
            0,
            "Running superpixel and semantic assignment",
        )
        for idx, (image_id, _) in enumerate(resolved, start=1):
            try:
                src = shadow_outputs.get(image_id) or _resolve_image_path(job.location, image_id)
                sem_path = semantic_outputs.get(image_id)
                if not src or not sem_path:
                    continue

                # decode semantic color to train id and coarse map
                sem_rgb = cv2.cvtColor(cv2.imread(sem_path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
                train_id_map = semantic_assign_service.decode_cityscapes_color_to_train_id(sem_rgb)
                coarse_map = semantic_assign_service.to_coarse_map(train_id_map)
                coarse_id_out = str(Path(dirs["semantic_5class"]) / f"{image_id}_id.png")
                coarse_color_out = str(Path(dirs["semantic_5class"]) / f"{image_id}_color.png")
                semantic_assign_service.save_coarse_outputs(coarse_map, coarse_id_out, coarse_color_out)
                job_repository.add_artifact(
                    job_id,
                    ArtifactItem(
                        artifact_id=f"art_{uuid4().hex[:10]}",
                        type=ArtifactType.SEMANTIC_5CLASS_ID,
                        stage=PipelineStageName.SUPERPIXEL,
                        path=coarse_id_out,
                        image_id=image_id,
                    ),
                )

                segments = superpixel_service.run_slic(
                    src,
                    n_segments=job.options.slic_n_segments,
                    compactness=job.options.slic_compactness,
                )
                labels_npy = str(Path(dirs["superpixel"]) / f"{image_id}_labels.npy")
                labels_png = str(Path(dirs["superpixel"]) / f"{image_id}_labels.png")
                superpixel_service.save_segments(segments, labels_npy, labels_png)
                job_repository.add_artifact(
                    job_id,
                    ArtifactItem(
                        artifact_id=f"art_{uuid4().hex[:10]}",
                        type=ArtifactType.SUPERPIXEL_LABEL,
                        stage=PipelineStageName.SUPERPIXEL,
                        path=labels_npy,
                        image_id=image_id,
                    ),
                )

                records = semantic_assign_service.assign_superpixel_semantics(
                    image_path=src,
                    segments=segments,
                    coarse_map=coarse_map,
                    image_id=image_id,
                )
                all_records.extend(records)

                job_repository.update_stage(
                    job_id,
                    PipelineStageName.SUPERPIXEL,
                    PipelineJobStatus.RUNNING,
                    (idx / total) * 100.0,
                    "Running superpixel and semantic assignment",
                )
            except Exception as exc:
                job_repository.update_stage(
                    job_id,
                    PipelineStageName.SUPERPIXEL,
                    PipelineJobStatus.FAILED,
                    (idx / total) * 100.0,
                    f"Superpixel stage failed: {exc}",
                )
                job_repository.update_job_status(
                    job_id,
                    PipelineJobStatus.FAILED,
                    error_code="PIPELINE_STAGE_FAILED",
                    error_message=f"Superpixel failed: {exc}",
                )
                return

        # save records
        if all_records:
            records_csv = str(Path(dirs["records"]) / "all_superpixel_semantics.csv")
            with open(records_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["image_id", "segment", "R", "G", "B", "coarse_id", "coarse_semantic"],
                )
                writer.writeheader()
                writer.writerows(all_records)
            job_repository.add_artifact(
                job_id,
                ArtifactItem(
                    artifact_id=f"art_{uuid4().hex[:10]}",
                    type=ArtifactType.RECORD_CSV,
                    stage=PipelineStageName.SUPERPIXEL,
                    path=records_csv,
                ),
            )

        job_repository.update_stage(
            job_id,
            PipelineStageName.SUPERPIXEL,
            PipelineJobStatus.SUCCEEDED,
            100,
            "Superpixel done",
        )

    # Stage 5: cluster
    if job.options.enable_cluster and all_records:
        job_repository.update_stage(
            job_id,
            PipelineStageName.CLUSTER,
            PipelineJobStatus.RUNNING,
            0,
            "Running palette clustering",
        )
        try:
            palette_files = palette_cluster_service.cluster_by_semantic(
                records=all_records,
                out_dir=dirs["cluster"],
                k_min=job.options.cluster_k_min,
                k_max=job.options.cluster_k_max,
            )
            for palette_path in palette_files:
                job_repository.add_artifact(
                    job_id,
                    ArtifactItem(
                        artifact_id=f"art_{uuid4().hex[:10]}",
                        type=ArtifactType.PALETTE_CSV,
                        stage=PipelineStageName.CLUSTER,
                        path=palette_path,
                    ),
                )
            job_repository.update_stage(
                job_id,
                PipelineStageName.CLUSTER,
                PipelineJobStatus.SUCCEEDED,
                100,
                "Cluster done",
            )
        except Exception as exc:
            job_repository.update_stage(
                job_id,
                PipelineStageName.CLUSTER,
                PipelineJobStatus.FAILED,
                100,
                f"Cluster stage failed: {exc}",
            )
            job_repository.update_job_status(
                job_id,
                PipelineJobStatus.FAILED,
                error_code="PIPELINE_STAGE_FAILED",
                error_message=f"Cluster failed: {exc}",
            )
            return

    # Stage 6: schemes (rule-based)
    if job.options.enable_scheme:
        job_repository.update_stage(
            job_id,
            PipelineStageName.SCHEME,
            PipelineJobStatus.RUNNING,
            0,
            "Generating color schemes (rule-based / NSGA-II)",
        )
        try:
            base_scheme = default_color_scheme()
            use_ga = (
                job.options.enable_ga_scheme
                and Path(dirs["cluster"]).is_dir()
                and list(Path(dirs["cluster"]).glob("palette_*.csv"))
            )
            if use_ga:
                schemes = run_nsga2_schemes(
                    cluster_dir=dirs["cluster"],
                    base_scheme=base_scheme,
                    population=job.options.ga_population,
                    generations=job.options.ga_generations,
                    output_count=job.options.scheme_count,
                    background_semantic=job.options.scheme_background_semantic,
                    seed=abs(hash(job_id)) % (2**31),
                    scheme_id_prefix=job_id,
                )
            if not use_ga or not schemes:
                schemes = scheme_generate_service.generate(
                    base_scheme,
                    job.options.scheme_count,
                    job_id=job_id,
                )
            scheme_paths = scheme_generate_service.save_schemes_json(schemes, dirs["schemes"])
            for path in scheme_paths:
                job_repository.add_artifact(
                    job_id,
                    ArtifactItem(
                        artifact_id=f"art_{uuid4().hex[:10]}",
                        type=ArtifactType.SCHEME_JSON,
                        stage=PipelineStageName.SCHEME,
                        path=path,
                    ),
                )
            job_repository.update_stage(
                job_id,
                PipelineStageName.SCHEME,
                PipelineJobStatus.SUCCEEDED,
                100,
                "Schemes generated",
            )
        except Exception as exc:
            job_repository.update_stage(
                job_id,
                PipelineStageName.SCHEME,
                PipelineJobStatus.FAILED,
                100,
                f"Scheme stage failed: {exc}",
            )
            job_repository.update_job_status(
                job_id,
                PipelineJobStatus.FAILED,
                error_code="PIPELINE_STAGE_FAILED",
                error_message=f"Scheme failed: {exc}",
            )
            return

    job_repository.update_job_status(job_id, PipelineJobStatus.SUCCEEDED)


def _raise_pipeline_conflict(message: str, code: str = "PIPELINE_ALREADY_RUNNING") -> None:
    err = ErrorResponse(success=False, message=message, error_code=code)
    raise HTTPException(status_code=409, detail=err.model_dump())


@router.post(
    "/jobs/{job_id}/run",
    response_model=PipelineJob,
    status_code=status.HTTP_202_ACCEPTED,
    summary="执行 pipeline 任务（异步）",
    description="立即返回 202，在后台执行任务；轮询 GET /jobs/{job_id} 查看进度。",
)
async def run_pipeline_job_async(job_id: str, background_tasks: BackgroundTasks) -> PipelineJob:
    job = job_repository.get_job(job_id)
    if not job:
        _raise_job_not_found(job_id)
    if job.status == PipelineJobStatus.RUNNING:
        _raise_pipeline_conflict("该任务已在执行中，请稍后再试")

    ensure_job_dirs(job_id)
    job_repository.update_job_status(job_id, PipelineJobStatus.RUNNING)
    background_tasks.add_task(_execute_pipeline_job, job_id)
    updated = job_repository.get_job(job_id)
    assert updated is not None
    return updated


@router.post(
    "/jobs/{job_id}/run-sync",
    response_model=PipelineJob,
    summary="执行 pipeline 任务（同步）",
    description="阻塞直至全部阶段完成，适合调试或脚本。",
)
async def run_pipeline_job_sync(job_id: str) -> PipelineJob:
    job = job_repository.get_job(job_id)
    if not job:
        _raise_job_not_found(job_id)
    if job.status == PipelineJobStatus.RUNNING:
        _raise_pipeline_conflict("该任务已在执行中（可能由异步 /run 触发），请稍后再试")

    ensure_job_dirs(job_id)
    job_repository.update_job_status(job_id, PipelineJobStatus.RUNNING)
    _execute_pipeline_job(job_id)
    updated = job_repository.get_job(job_id)
    assert updated is not None
    return updated
