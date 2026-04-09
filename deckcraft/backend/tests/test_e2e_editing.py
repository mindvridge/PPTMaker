"""
시나리오 2: 수정 플로 E2E 테스트

LLM 호출을 mock하여 편집 API를 검증합니다:
  refine → change-theme → suggest → batch
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.schemas import (
    ColorPalette,
    DesignSystem,
    Fonts,
    LayoutType,
    Presentation,
    StylePreset,
)


# ─── Test: refine single slide ────────────────────────────────────────


@pytest.mark.asyncio
async def test_refine_single_slide(async_client, sample_presentation):
    """단일 슬라이드 수정 → 변경 사항 확인."""
    original_title = sample_presentation.slides[0].elements[0].text_props.content

    # Mock LLM response
    modified_slide = sample_presentation.slides[0].model_dump(mode="json")
    modified_slide["elements"][0]["text_props"]["content"] = "혁신의 시작, AI로 미래를 열다"

    mock_result = {
        "modified_slides": [modified_slide],
        "changes_summary": "첫 번째 슬라이드의 제목을 더 임팩트있게 변경했습니다.",
    }

    with patch(
        "app.services.llm.AsyncLLMClient.refine_presentation",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        resp = await async_client.post(
            "/api/edit/refine",
            json={
                "presentation": sample_presentation.model_dump(mode="json"),
                "slide_index": 0,
                "instruction": "제목을 더 임팩트있게 바꿔줘",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "modified_slides" in data
    assert "changes_summary" in data
    assert len(data["modified_slides"]) == 1

    new_title = data["modified_slides"][0]["elements"][0]["text_props"]["content"]
    assert new_title != original_title
    assert new_title == "혁신의 시작, AI로 미래를 열다"


@pytest.mark.asyncio
async def test_refine_entire_presentation(async_client, sample_presentation):
    """전체 PPT 수정 (slide_index=null)."""
    all_slides = [s.model_dump(mode="json") for s in sample_presentation.slides]
    # Modify all speaker notes
    for s in all_slides:
        s["speaker_notes"] = s["speaker_notes"] + " (수정됨)"

    mock_result = {
        "modified_slides": all_slides,
        "changes_summary": "전체 발표자 노트를 수정했습니다.",
    }

    with patch(
        "app.services.llm.AsyncLLMClient.refine_presentation",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        resp = await async_client.post(
            "/api/edit/refine",
            json={
                "presentation": sample_presentation.model_dump(mode="json"),
                "slide_index": None,
                "instruction": "전체 발표자 노트를 격식체로 바꿔줘",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["modified_slides"]) == 10


# ─── Test: change theme ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_change_theme(async_client, sample_presentation):
    """디자인 테마 변경 → color_palette가 바뀌는지 확인."""
    original_primary = sample_presentation.design_system.color_palette.primary

    new_design = DesignSystem(
        color_palette=ColorPalette(
            primary="#1B4332",
            secondary="#2D6A4F",
            accent="#40916C",
            background="#F0F4F0",
            surface="#D8E8D8",
            text_primary="#1B4332",
            text_secondary="#52796F",
        ),
        fonts=Fonts(
            title="Pretendard Bold",
            subtitle="Pretendard SemiBold",
            body="Pretendard",
            caption="Pretendard Light",
        ),
        style_preset=StylePreset.corporate,
    )

    with patch(
        "app.services.llm.AsyncLLMClient.generate_new_theme",
        new_callable=AsyncMock,
        return_value=new_design,
    ):
        resp = await async_client.post(
            "/api/edit/change-theme",
            json={
                "presentation": sample_presentation.model_dump(mode="json"),
                "new_style": "corporate",
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    new_primary = data["design_system"]["color_palette"]["primary"]
    assert new_primary != original_primary
    assert new_primary == "#1B4332"
    assert data["design_system"]["style_preset"] == "corporate"


# ─── Test: suggest improvements ───────────────────────────────────────


@pytest.mark.asyncio
async def test_suggest_improvements(async_client, sample_presentation):
    """슬라이드 개선점 제안 API."""
    mock_result = {
        "suggestions": [
            {"type": "content", "description": "제목이 너무 일반적입니다. 구체적인 수치를 포함하세요."},
            {"type": "design", "description": "배경색과 텍스트색의 대비가 부족합니다."},
            {"type": "layout", "description": "content_bullets 대신 stats_kpi 레이아웃이 더 적합합니다."},
        ]
    }

    with patch(
        "app.services.llm.AsyncLLMClient.suggest_improvements",
        new_callable=AsyncMock,
        return_value=mock_result,
    ):
        resp = await async_client.post(
            "/api/edit/suggest",
            json={
                "presentation": sample_presentation.model_dump(mode="json"),
                "slide_index": 1,
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) == 3
    types = {s["type"] for s in data["suggestions"]}
    assert types == {"content", "design", "layout"}


# ─── Test: batch edit ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_batch_edit(async_client, sample_presentation):
    """여러 수정 명령 순차 적용."""
    slides_json = [s.model_dump(mode="json") for s in sample_presentation.slides]

    with patch(
        "app.services.llm.AsyncLLMClient.refine_presentation",
        new_callable=AsyncMock,
    ) as mock_refine:
        mock_refine.return_value = {
            "modified_slides": slides_json,
            "changes_summary": "수정 완료",
        }

        resp = await async_client.post(
            "/api/edit/batch",
            json={
                "presentation": sample_presentation.model_dump(mode="json"),
                "instructions": [
                    "모든 제목을 격식체로 바꿔줘",
                    "불릿 포인트를 최대 3개로 줄여줘",
                ],
            },
        )

    assert resp.status_code == 200
    data = resp.json()
    assert "presentation" in data
    assert "summaries" in data
    assert len(data["summaries"]) == 2
    # LLM이 2번 호출되었는지 확인
    assert mock_refine.call_count == 2


# ─── Test: suggest with invalid slide_index ───────────────────────────


@pytest.mark.asyncio
async def test_suggest_invalid_index(async_client, sample_presentation):
    """범위 초과 slide_index → 400."""
    resp = await async_client.post(
        "/api/edit/suggest",
        json={
            "presentation": sample_presentation.model_dump(mode="json"),
            "slide_index": 999,
        },
    )
    assert resp.status_code == 400


# ─── Test: legacy refine-slide endpoint ───────────────────────────────


@pytest.mark.asyncio
async def test_refine_slide_legacy(async_client, sample_presentation):
    """Phase 2 호환 refine-slide 엔드포인트."""
    slide = sample_presentation.slides[0]
    refined = slide.model_copy(deep=True)

    with patch(
        "app.services.llm.AsyncLLMClient.refine_slide",
        new_callable=AsyncMock,
        return_value=refined,
    ):
        resp = await async_client.post(
            "/api/edit/refine-slide",
            json={
                "slide": slide.model_dump(mode="json"),
                "instruction": "제목 변경",
            },
        )

    assert resp.status_code == 200
