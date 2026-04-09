"""
시나리오 1: 기본 생성 플로 E2E 테스트

LLM 호출을 mock하여 전체 파이프라인을 검증합니다:
  plan 생성 → full 생성 → PPTX 내보내기 → 파일 검증
"""

from __future__ import annotations

import io
import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from pptx import Presentation as PptxPresentation
from pptx.oxml.ns import qn

from app.models.schemas import (
    Background,
    BackgroundType,
    DesignSystem,
    ElementType,
    FontWeight,
    LayoutType,
    Metadata,
    Position,
    Presentation,
    PresentationPlan,
    Slide,
    SlideElement,
    TextAlign,
    TextProps,
    VerticalAlign,
)


# ─── Helper: create a mock slide for LLM response ────────────────────


def _mock_slide(order: int, layout: LayoutType, title: str) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "order": order,
        "layout_type": layout.value,
        "background": {"type": "solid", "color": "#FFFFFF"},
        "elements": [
            {
                "id": str(uuid.uuid4()),
                "type": "text",
                "position": {"x": 10, "y": 10, "width": 80, "height": 15},
                "z_index": 0,
                "text_props": {
                    "content": title,
                    "font_family": "Pretendard",
                    "font_size": 28,
                    "font_weight": "bold",
                    "color": "#0F172A",
                    "align": "left",
                    "vertical_align": "top",
                },
            },
            {
                "id": str(uuid.uuid4()),
                "type": "text",
                "position": {"x": 10, "y": 30, "width": 80, "height": 50},
                "z_index": 1,
                "text_props": {
                    "content": "한국어 본문 텍스트 내용입니다.",
                    "font_family": "Pretendard",
                    "font_size": 18,
                    "font_weight": "normal",
                    "color": "#64748B",
                    "align": "left",
                    "vertical_align": "top",
                },
            },
        ],
        "speaker_notes": f"슬라이드 {order + 1} 발표자 노트",
    }


# ─── Test: PPTX export with sample presentation ──────────────────────


@pytest.mark.asyncio
async def test_export_pptx_generates_valid_file(
    async_client,
    sample_presentation,
):
    """PPTX 내보내기 → python-pptx로 열어서 기본 검증."""
    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": sample_presentation.model_dump(mode="json")},
    )
    assert resp.status_code == 200
    assert "application/vnd.openxmlformats" in resp.headers["content-type"]

    # python-pptx로 열기
    pptx = PptxPresentation(io.BytesIO(resp.content))
    assert len(pptx.slides) == 10


@pytest.mark.asyncio
async def test_export_pptx_slide_count_matches(
    async_client,
    sample_presentation,
):
    """슬라이드 수가 Presentation JSON과 일치하는지 확인."""
    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": sample_presentation.model_dump(mode="json")},
    )
    pptx = PptxPresentation(io.BytesIO(resp.content))
    assert len(pptx.slides) == len(sample_presentation.slides)


@pytest.mark.asyncio
async def test_export_pptx_contains_korean_text(
    async_client,
    sample_presentation,
):
    """PPTX에 한국어 텍스트가 포함되어 있는지 확인."""
    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": sample_presentation.model_dump(mode="json")},
    )
    pptx = PptxPresentation(io.BytesIO(resp.content))

    all_text = []
    for slide in pptx.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        all_text.append(run.text)

    full_text = " ".join(all_text)
    # 한국어 텍스트 포함 확인
    assert "투자" in full_text or "스타트업" in full_text or "소개" in full_text


@pytest.mark.asyncio
async def test_export_pptx_has_speaker_notes(
    async_client,
    sample_presentation,
):
    """발표자 노트가 포함되어 있는지 확인."""
    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": sample_presentation.model_dump(mode="json")},
    )
    pptx = PptxPresentation(io.BytesIO(resp.content))

    notes_found = False
    for slide in pptx.slides:
        if slide.has_notes_slide:
            notes_text = slide.notes_slide.notes_text_frame.text
            if notes_text:
                notes_found = True
                break

    assert notes_found, "발표자 노트가 하나도 없음"


# ─── Test: full generation with mocked LLM ───────────────────────────


@pytest.mark.asyncio
async def test_generate_plan_mock(async_client, sample_plan):
    """Plan 생성 엔드포인트 (LLM mock)."""
    mock_plan_json = sample_plan.model_dump_json()

    with patch(
        "app.services.llm.AsyncLLMClient.generate_presentation_plan_stream"
    ) as mock_stream:
        # Mock: yield entire JSON as single token, then complete
        async def fake_stream(*args, **kwargs):
            yield mock_plan_json

        mock_stream.return_value = fake_stream()

        resp = await async_client.post(
            "/api/generate/plan",
            json={
                "topic": "AI 스타트업 투자 유치",
                "slide_count": 10,
                "style": "modern_minimal",
                "language": "ko",
            },
        )
        assert resp.status_code == 200
        # SSE response
        assert "text/event-stream" in resp.headers["content-type"]


@pytest.mark.asyncio
async def test_generate_full_mock(async_client, sample_plan, sample_presentation):
    """Full 생성 엔드포인트 (LLM mock)."""
    mock_slides = sample_presentation.slides

    with patch(
        "app.services.llm.AsyncLLMClient.generate_slide_content"
    ) as mock_gen, patch(
        "app.services.llm.AsyncLLMClient.generate_image_prompts"
    ) as mock_img:

        async def fake_gen(plan, idx):
            return mock_slides[idx]

        mock_gen.side_effect = fake_gen
        mock_img.return_value = ["a photo of technology", "a chart illustration"]

        resp = await async_client.post(
            "/api/generate/full",
            json={"plan": sample_plan.model_dump(mode="json")},
        )
        assert resp.status_code == 200


# ─── Test: end-to-end pipeline (mocked LLM → export) ─────────────────


@pytest.mark.asyncio
async def test_e2e_generate_and_export(async_client, sample_presentation):
    """생성된 presentation을 바로 PPTX로 내보내기."""
    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": sample_presentation.model_dump(mode="json")},
    )
    assert resp.status_code == 200

    pptx = PptxPresentation(io.BytesIO(resp.content))

    # 슬라이드 수 검증
    assert len(pptx.slides) == 10

    # 텍스트 존재 검증
    text_count = 0
    for slide in pptx.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                text_count += len(shape.text_frame.paragraphs)
    assert text_count > 0, "텍스트 요소가 하나도 없음"
