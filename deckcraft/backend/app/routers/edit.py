"""
PPT 수정 API 엔드포인트

- POST /api/edit/refine        — 자연어 명령으로 슬라이드(들) 수정
- POST /api/edit/batch         — 여러 수정 명령을 순차 적용
- POST /api/edit/suggest       — 슬라이드 개선점 분석
- POST /api/edit/change-theme  — 디자인 테마 일괄 변경
- POST /api/edit/refine-slide  — (Phase 2 호환) 단일 슬라이드 AI 수정
- PUT  /api/edit/{id}          — 프레젠테이션 전체 업데이트 + 좌표 재계산
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import (
    BatchEditRequest,
    ChangeThemeRequest,
    Presentation,
    RefineRequest,
    RefineResponse,
    Slide,
    SuggestRequest,
    SuggestResponse,
    Suggestion,
)
from app.services.llm import llm_client
from app.services.designer import design_engine

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Legacy compat (Phase 2 frontend uses this) ──────────────────────


class RefineSlideRequest(BaseModel):
    slide: Slide
    instruction: str
    design_system: dict | None = None


@router.post("/refine-slide")
async def refine_slide_legacy(req: RefineSlideRequest):
    """자연어 명령으로 단일 슬라이드를 AI 수정합니다 (Phase 2 호환)."""
    try:
        refined = await llm_client.refine_slide(req.slide, req.instruction)
        return refined.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Slide refinement failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ─── PUT /{presentation_id} ──────────────────────────────────────────


@router.put("/{presentation_id}")
async def update_presentation(presentation_id: str, presentation: Presentation):
    """프레젠테이션을 업데이트합니다 (레이아웃 좌표 재계산 포함)."""
    updated_slides = []
    for slide in presentation.slides:
        updated = design_engine.apply_layout(slide, presentation.design_system)
        updated_slides.append(updated)
    presentation = presentation.model_copy(update={"slides": updated_slides})
    return presentation.model_dump(mode="json")


# ─── POST /refine ─────────────────────────────────────────────────────


@router.post("/refine", response_model=RefineResponse)
async def refine(req: RefineRequest):
    """자연어 수정 명령으로 슬라이드(들)를 수정합니다.

    slide_index가 None이면 전체 PPT를 대상으로 수정합니다.
    """
    try:
        result = await llm_client.refine_presentation(
            presentation=req.presentation,
            slide_index=req.slide_index,
            instruction=req.instruction,
        )

        # LLM 결과를 Pydantic으로 검증
        modified_slides = [
            Slide.model_validate(s) for s in result.get("modified_slides", [])
        ]

        # 레이아웃 엔진으로 좌표 재계산
        modified_slides = [
            design_engine.apply_layout(s, req.presentation.design_system)
            for s in modified_slides
        ]

        return RefineResponse(
            modified_slides=modified_slides,
            changes_summary=result.get("changes_summary", "수정 완료"),
        )
    except Exception as exc:
        logger.exception("Refine failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ─── POST /batch ──────────────────────────────────────────────────────


@router.post("/batch")
async def batch_edit(req: BatchEditRequest):
    """여러 수정 명령을 순차 적용합니다."""
    presentation = req.presentation

    all_summaries: list[str] = []
    for i, instruction in enumerate(req.instructions):
        try:
            result = await llm_client.refine_presentation(
                presentation=presentation,
                slide_index=None,
                instruction=instruction,
            )

            modified_slides = [
                Slide.model_validate(s)
                for s in result.get("modified_slides", [])
            ]

            if modified_slides:
                # 수정된 슬라이드를 presentation에 반영
                modified_map = {s.id: s for s in modified_slides}
                new_slides = []
                for s in presentation.slides:
                    if s.id in modified_map:
                        new_slides.append(modified_map[s.id])
                    else:
                        new_slides.append(s)
                presentation = presentation.model_copy(
                    update={"slides": new_slides}
                )

            summary = result.get("changes_summary", f"명령 {i + 1} 적용 완료")
            all_summaries.append(summary)

        except Exception as exc:
            logger.warning("Batch step %d failed: %s", i + 1, exc)
            all_summaries.append(f"명령 {i + 1} 실패: {exc}")

    # 최종 좌표 재계산
    final_slides = [
        design_engine.apply_layout(s, presentation.design_system)
        for s in presentation.slides
    ]
    presentation = presentation.model_copy(update={"slides": final_slides})

    return {
        "presentation": presentation.model_dump(mode="json"),
        "summaries": all_summaries,
    }


# ─── POST /suggest ────────────────────────────────────────────────────


@router.post("/suggest", response_model=SuggestResponse)
async def suggest(req: SuggestRequest):
    """슬라이드의 개선점을 분석합니다."""
    if req.slide_index >= len(req.presentation.slides):
        raise HTTPException(status_code=400, detail="slide_index 범위 초과")

    try:
        result = await llm_client.suggest_improvements(
            presentation=req.presentation,
            slide_index=req.slide_index,
        )

        suggestions = [
            Suggestion.model_validate(s)
            for s in result.get("suggestions", [])
        ]

        return SuggestResponse(suggestions=suggestions)
    except Exception as exc:
        logger.exception("Suggest failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ─── POST /change-theme ──────────────────────────────────────────────


@router.post("/change-theme")
async def change_theme(req: ChangeThemeRequest):
    """디자인 테마를 변경하고 모든 슬라이드에 적용합니다."""
    try:
        new_design = await llm_client.generate_new_theme(
            new_style=req.new_style,
            current_design=req.presentation.design_system,
        )

        # 새 디자인 시스템으로 프레젠테이션 업데이트
        presentation = req.presentation.model_copy(
            update={"design_system": new_design}
        )

        # 모든 슬라이드에 새 디자인 적용 (배경색, 텍스트 색상 등)
        updated_slides = []
        for slide in presentation.slides:
            # 배경색 업데이트: solid이면 새 배경색으로
            if slide.background.type.value == "solid":
                from app.models.schemas import Background, BackgroundType

                slide = slide.model_copy(
                    update={
                        "background": Background(
                            type=BackgroundType.solid,
                            color=new_design.color_palette.background,
                        )
                    }
                )

            # 텍스트 색상 업데이트: design_system 참조 키면 새 값으로
            updated_elements = []
            for elem in slide.elements:
                if elem.text_props:
                    color = elem.text_props.color
                    palette = new_design.color_palette.model_dump()
                    if color in palette:
                        elem = elem.model_copy(
                            update={
                                "text_props": elem.text_props.model_copy(
                                    update={"color": palette[color]}
                                )
                            }
                        )
                updated_elements.append(elem)

            slide = slide.model_copy(update={"elements": updated_elements})

            # 레이아웃 엔진으로 재계산
            slide = design_engine.apply_layout(slide, new_design)
            updated_slides.append(slide)

        presentation = presentation.model_copy(
            update={"slides": updated_slides}
        )

        return presentation.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Theme change failed")
        raise HTTPException(status_code=500, detail=str(exc))
