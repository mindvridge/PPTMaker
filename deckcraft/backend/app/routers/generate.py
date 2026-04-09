"""
PPT 생성 API 엔드포인트

- POST /api/generate/plan — 프레젠테이션 계획(아웃라인) 생성 (SSE 스트리밍)
- POST /api/generate/full — 전체 슬라이드 콘텐츠 생성
- POST /api/generate/from-document — 문서 업로드 → PPT 계획
- POST /api/generate/image — 이미지 생성
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from app.models.schemas import (
    GenerateFullRequest,
    GenerateImageRequest,
    GeneratePlanRequest,
    Language,
    Metadata,
    Presentation,
    PresentationPlan,
)
from app.services.llm import llm_client
from app.services.designer import design_engine
from app.services.image_gen import generate_image

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── SSE helpers ──────────────────────────────────────────────────────


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ─── POST /plan ───────────────────────────────────────────────────────


@router.post("/plan")
async def generate_plan(req: GeneratePlanRequest):
    """주제를 받아 프레젠테이션 계획을 SSE 스트리밍으로 생성."""

    async def stream():
        yield _sse_event("status", {"step": "generating_plan", "progress": 0.0})

        try:
            collected = ""
            async for token in llm_client.generate_presentation_plan_stream(
                topic=req.topic,
                requirements=req.requirements,
                style=req.style,
                slide_count=req.slide_count,
                language=req.language.value,
            ):
                collected += token
                yield _sse_event("token", {"content": token})

            # 스트리밍 완료 후 전체 JSON 파싱 및 검증
            plan = PresentationPlan.model_validate_json(collected)
            yield _sse_event(
                "complete",
                {"progress": 1.0, "plan": plan.model_dump(mode="json")},
            )

        except Exception as exc:
            logger.exception("Plan generation failed")
            # 스트리밍 실패 시 non-streaming 폴백
            try:
                plan = await llm_client.generate_presentation_plan(
                    topic=req.topic,
                    requirements=req.requirements,
                    style=req.style,
                    slide_count=req.slide_count,
                    language=req.language.value,
                )
                yield _sse_event(
                    "complete",
                    {"progress": 1.0, "plan": plan.model_dump(mode="json")},
                )
            except Exception as fallback_exc:
                logger.exception("Fallback plan generation also failed")
                yield _sse_event(
                    "error",
                    {"message": str(fallback_exc)},
                )

    return StreamingResponse(stream(), media_type="text/event-stream")


# ─── POST /full ───────────────────────────────────────────────────────


@router.post("/full")
async def generate_full(req: GenerateFullRequest):
    """확정된 계획으로 전체 슬라이드 콘텐츠를 생성 (SSE 스트리밍)."""
    plan = req.plan
    total_slides = len(plan.slides)

    async def stream():
        slides = []
        yield _sse_event(
            "status",
            {"step": "start", "progress": 0.0, "total_slides": total_slides},
        )

        # a. 각 슬라이드 콘텐츠 병렬 생성
        async def gen_one(idx: int):
            slide = await llm_client.generate_slide_content(plan, idx)
            # 레이아웃 엔진으로 좌표 계산
            slide = design_engine.apply_layout(slide, plan.design_system)
            return idx, slide

        tasks = [gen_one(i) for i in range(total_slides)]

        for coro in asyncio.as_completed(tasks):
            try:
                idx, slide = await coro
                slides.append((idx, slide))
                progress = len(slides) / total_slides * 0.7
                yield _sse_event(
                    "slide_complete",
                    {
                        "step": f"slide_{idx}_content",
                        "progress": progress,
                        "slide_index": idx,
                        "slide": slide.model_dump(mode="json"),
                    },
                )
            except Exception as exc:
                logger.warning("Slide %d generation failed: %s", idx, exc)
                yield _sse_event(
                    "slide_error",
                    {"slide_index": idx, "message": str(exc)},
                )

        # 순서 정렬
        slides.sort(key=lambda x: x[0])
        ordered_slides = [s for _, s in slides]

        # b. 이미지 프롬프트 생성
        yield _sse_event(
            "status", {"step": "generating_image_prompts", "progress": 0.75}
        )
        try:
            image_prompts = await llm_client.generate_image_prompts(ordered_slides)
            yield _sse_event(
                "image_prompts",
                {"progress": 0.85, "prompts": image_prompts},
            )
        except Exception as exc:
            logger.warning("Image prompt generation failed: %s", exc)
            image_prompts = []

        # c. 이미지 생성 (선택적 — 프롬프트가 있는 경우)
        if image_prompts:
            yield _sse_event(
                "status", {"step": "generating_images", "progress": 0.85}
            )

        # d. 전체 Presentation JSON 조립
        presentation = Presentation(
            id=str(uuid.uuid4()),
            title=plan.title,
            design_system=plan.design_system,
            slides=ordered_slides,
            metadata=Metadata(
                created_at=datetime.now(timezone.utc),
                language=plan.metadata.language,
                aspect_ratio=plan.metadata.aspect_ratio,
            ),
        )

        yield _sse_event(
            "complete",
            {
                "progress": 1.0,
                "presentation": presentation.model_dump(mode="json"),
            },
        )

    return StreamingResponse(stream(), media_type="text/event-stream")


# ─── POST /from-document ─────────────────────────────────────────────


@router.post("/from-document")
async def generate_from_document(
    file: UploadFile = File(...),
    language: str = Form("ko"),
    style: str | None = Form(None),
    slide_count: int | None = Form(None),
):
    """업로드된 문서(PDF, DOCX, TXT)에서 PPT 계획을 생성."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일명이 없습니다.")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    allowed = {"pdf", "docx", "txt", "md"}
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용: {', '.join(allowed)}",
        )

    content_bytes = await file.read()

    # 텍스트 추출 (간단한 구현; PDF/DOCX는 추후 라이브러리 추가)
    if ext == "txt" or ext == "md":
        text = content_bytes.decode("utf-8", errors="replace")
    elif ext == "pdf":
        # TODO: PyPDF2 or pdfplumber
        text = content_bytes.decode("utf-8", errors="replace")
    elif ext == "docx":
        # TODO: python-docx
        text = content_bytes.decode("utf-8", errors="replace")
    else:
        text = content_bytes.decode("utf-8", errors="replace")

    # 텍스트를 주제로 사용하여 계획 생성
    topic = f"다음 문서 내용을 기반으로 프레젠테이션을 만들어주세요:\n\n{text[:5000]}"
    try:
        plan = await llm_client.generate_presentation_plan(
            topic=topic,
            style=style,
            slide_count=slide_count,
            language=language,
        )
        return plan.model_dump(mode="json")
    except Exception as exc:
        logger.exception("Document-based generation failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ─── POST /image ──────────────────────────────────────────────────────


@router.post("/image")
async def generate_image_endpoint(req: GenerateImageRequest):
    """이미지 생성 API (ComfyUI FLUX / fal.ai)."""
    try:
        url = await generate_image(
            prompt=req.prompt,
            style=req.style,
            size=req.size,
        )
        return {"url": url}
    except Exception as exc:
        logger.exception("Image generation failed")
        raise HTTPException(status_code=500, detail=str(exc))
