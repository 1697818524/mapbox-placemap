"""
配色方案生成路由（规则版；GA 后续接入）
"""
from fastapi import APIRouter, HTTPException

from app.models.common import ErrorResponse
from app.models.scheme import GenerateSchemesRequest, GenerateSchemesResponse
from app.services.scheme_generate import SchemeGenerateService

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])

_scheme_service = SchemeGenerateService()


@router.post("/generate", response_model=GenerateSchemesResponse, summary="生成多套配色方案")
async def generate_schemes(payload: GenerateSchemesRequest) -> GenerateSchemesResponse:
    if not payload.currentScheme.layers:
        err = ErrorResponse(
            success=False,
            message="currentScheme.layers 不能为空",
            error_code="SCHEME_EMPTY_BASE",
        )
        raise HTTPException(status_code=400, detail=err.model_dump())

    schemes = _scheme_service.generate(
        payload.currentScheme,
        payload.count,
        job_id=payload.job_id,
        semantic_mode=payload.semantic_mode,
        layer_semantics=payload.layer_semantics,
        population=payload.population,
        generations=payload.generations,
    )
    return GenerateSchemesResponse(schemes=schemes)
