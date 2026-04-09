"""
PPT 수정 API 엔드포인트

- PUT  /api/edit/{presentation_id} — 프레젠테이션 전체 수정
- POST /api/edit/refine-slide — AI로 슬라이드 수정
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import Presentation, Slide
from app.services.llm import llm_client
from app.services.designer import design_engine

logger = logging.getLogger(__name__)
router = APIRouter()


class RefineSlideRequest(BaseModel):
    slide: Slide
    instruction: str
    design_system: dict | None = None


@router.put("/{presentation_id}")
async def update_presentation(presentation_id: str, presentation: Presentation):
    """프레젠테이션을 수정합니다."""
    # 레이아웃 엔진으로 좌표 재계산
    updated_slides = []
    for slide in presentation.slides:
        updated = design_engine.apply_layout(slide, presentation.design_system)
        updated_slides.append(updated)
    presentation = presentation.model_copy(update={"slides": updated_slides})

    return presentation.model_dump(mode="json")


@router.post("/refine-slide")
async def refine_slide(req: RefineSlideRequest):
    """자연어 명령으로 슬라이드를 AI 수정합니다."""
    try:
        refined = await llm_client.refine_slide(req.slide, req.instruction)
        return refined.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Slide refinement failed")
        raise HTTPException(status_code=500, detail=str(exc))
