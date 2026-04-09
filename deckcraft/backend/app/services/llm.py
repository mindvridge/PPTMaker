"""
LLM 호출 서비스 — 슬라이드 JSON 생성

AsyncLLMClient는 OpenAI 호환 API(vLLM Qwen3-235B)를 기본으로 사용하고,
실패 시 OpenAI/Anthropic API로 폴백합니다.
"""

from __future__ import annotations

import json
import logging
import os
from typing import AsyncIterator

import httpx

from app.models.schemas import (
    DesignSystem,
    Language,
    Presentation,
    PresentationPlan,
    Slide,
    SlideOutline,
)

logger = logging.getLogger(__name__)

# ─── 환경변수 ─────────────────────────────────────────────────────────

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
VLLM_API_KEY = os.getenv("VLLM_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

MAX_RETRIES = 3

# ─── 시스템 프롬프트 ──────────────────────────────────────────────────

SYSTEM_PROMPT_PLAN = """\
당신은 프레젠테이션 디자인 전문가입니다. 사용자의 주제를 받아 고품질 프레젠테이션 계획을 JSON으로 생성합니다.

규칙:
- 슬라이드당 텍스트는 최대 50단어, 불릿은 최대 5개
- 한국어가 기본이며, 영어 혼용 가능
- layout_type은 반드시 다음 중 선택: title_hero, title_image, content_bullets, two_column, three_column, image_text_left, image_text_right, full_image, chart_with_text, comparison, timeline, stats_kpi, quote, section_header, table, ending, blank
- 첫 슬라이드는 title_hero 또는 title_image, 마지막 슬라이드는 ending 사용
- 디자인 시스템의 컬러 팔레트는 접근성(WCAG AA 대비율 4.5:1 이상) 고려
- style_preset: modern_minimal, corporate, creative, academic 중 주제에 맞게 선택
- 폰트는 Pretendard 패밀리 사용 (title: "Pretendard Bold", subtitle: "Pretendard SemiBold", body: "Pretendard", caption: "Pretendard Light")

JSON 출력 형식 (PresentationPlan):
{
  "title": "프레젠테이션 제목",
  "design_system": {
    "color_palette": { "primary": "#hex", "secondary": "#hex", "accent": "#hex", "background": "#hex", "surface": "#hex", "text_primary": "#hex", "text_secondary": "#hex" },
    "fonts": { "title": "Pretendard Bold", "subtitle": "Pretendard SemiBold", "body": "Pretendard", "caption": "Pretendard Light" },
    "style_preset": "modern_minimal"
  },
  "slides": [
    { "order": 0, "layout_type": "title_hero", "title": "...", "key_points": ["..."], "speaker_notes": "...", "needs_image": false, "image_description": null }
  ],
  "metadata": { "created_at": "ISO datetime", "language": "ko", "aspect_ratio": "16:9" }
}
"""

SYSTEM_PROMPT_SLIDE = """\
당신은 프레젠테이션 콘텐츠 전문가입니다. 슬라이드 아웃라인을 받아 상세 콘텐츠가 포함된 완전한 Slide JSON을 생성합니다.

규칙:
- 슬라이드당 텍스트 최대 50단어, 불릿 최대 5개
- 한국어 기본, 영어 혼용 가능
- elements의 position은 0으로 설정 (DesignEngine이 계산)
- text_props.content에서 **볼드**, *이탤릭* 마크다운 사용 가능
- color 필드에는 hex 색상 또는 design_system 참조 키("primary", "text_primary" 등) 사용
- 각 element에 고유 id (UUID 형식) 부여

JSON 출력 형식 (Slide):
{
  "id": "uuid", "order": 0, "layout_type": "...",
  "background": { "type": "solid", "color": "#hex" },
  "elements": [ { "id": "uuid", "type": "text", "position": {"x":0,"y":0,"width":0,"height":0}, "z_index": 0, "text_props": {...} } ],
  "speaker_notes": "..."
}
"""

SYSTEM_PROMPT_REFINE = """\
당신은 프레젠테이션 편집 전문가입니다. 기존 슬라이드 JSON과 사용자의 수정 명령을 받아 수정된 Slide JSON을 반환합니다.
기존 요소의 id는 유지하고, 수정 명령에 따라 content, color, layout 등을 변경합니다.
수정하지 않는 필드는 그대로 유지합니다.
"""

SYSTEM_PROMPT_REFINE_FULL = """\
당신은 PPT 슬라이드 편집 전문가입니다.
현재 슬라이드의 JSON과 사용자의 수정 요청을 받아, 수정된 JSON을 반환하세요.

규칙:
- 요청된 부분만 수정하고 나머지는 그대로 유지
- position 좌표를 직접 변경하지 말 것 (layout_type 변경으로 대신)
- 텍스트 수정은 직접 text_props.content를 변경
- 스타일 변경은 design_system의 해당 값을 변경
- 새 요소 추가 시 적절한 z_index 부여
- 기존 요소의 id는 반드시 유지

JSON 출력 형식:
{
  "modified_slides": [ ... (수정된 Slide JSON 배열) ],
  "changes_summary": "변경 사항 한국어 요약"
}
"""

SYSTEM_PROMPT_SUGGEST = """\
당신은 프레젠테이션 품질 분석 전문가입니다.
주어진 슬라이드를 분석하고 개선점을 제안합니다.

분석 항목:
- content: 텍스트 내용의 명확성, 분량, 흐름
- design: 색상, 폰트 크기, 여백, 시각적 균형
- layout: 레이아웃 타입의 적절성, 요소 배치

JSON 출력 형식:
{
  "suggestions": [
    { "type": "content"|"design"|"layout", "description": "개선 제안 (한국어)" }
  ]
}
"""

SYSTEM_PROMPT_THEME = """\
당신은 프레젠테이션 디자인 시스템 전문가입니다.
요청된 스타일에 맞는 새로운 DesignSystem을 생성하세요.

규칙:
- color_palette의 모든 색상은 #RRGGBB 형식
- WCAG AA 대비율 4.5:1 이상 보장
- text_primary와 background 사이 충분한 대비
- 스타일 프리셋에 맞는 분위기 (modern_minimal: 깔끔, corporate: 격식, creative: 생동감, academic: 차분)
- 폰트는 Pretendard 패밀리 유지

JSON 출력 형식 (DesignSystem):
{
  "color_palette": { "primary": "#hex", "secondary": "#hex", "accent": "#hex", "background": "#hex", "surface": "#hex", "text_primary": "#hex", "text_secondary": "#hex" },
  "fonts": { "title": "...", "subtitle": "...", "body": "...", "caption": "..." },
  "style_preset": "..."
}
"""

SYSTEM_PROMPT_IMAGE = """\
당신은 프레젠테이션 이미지 프롬프트 전문가입니다. 슬라이드 내용을 분석하여 고품질 이미지 생성 프롬프트를 영어로 작성합니다.

규칙:
- 프롬프트는 반드시 영어로 작성
- 프레젠테이션에 적합한 전문적이고 깔끔한 이미지 스타일
- 각 프롬프트는 구체적인 시각적 요소를 포함
- 형식: ["prompt1", "prompt2", ...]
"""


# ─── Provider configs ─────────────────────────────────────────────────


def _provider_configs() -> list[dict]:
    """Return ordered list of provider configs for fallback chain."""
    configs = []
    if VLLM_BASE_URL:
        configs.append(
            {
                "name": "vllm",
                "base_url": VLLM_BASE_URL,
                "api_key": VLLM_API_KEY or "not-needed",
                "model": os.getenv("VLLM_MODEL", "Qwen/Qwen3-235B-A22B"),
            }
        )
    if OPENAI_API_KEY:
        configs.append(
            {
                "name": "openai",
                "base_url": "https://api.openai.com/v1",
                "api_key": OPENAI_API_KEY,
                "model": os.getenv("OPENAI_MODEL", "gpt-4o"),
            }
        )
    if ANTHROPIC_API_KEY:
        configs.append(
            {
                "name": "anthropic",
                "base_url": "https://api.anthropic.com/v1",
                "api_key": ANTHROPIC_API_KEY,
                "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
                "is_anthropic": True,
            }
        )
    return configs


# ─── AsyncLLMClient ───────────────────────────────────────────────────


class AsyncLLMClient:
    """OpenAI-compatible async LLM client with retry + fallback."""

    def __init__(self) -> None:
        self._providers = _provider_configs()
        self._http = httpx.AsyncClient(timeout=120.0)

    async def close(self) -> None:
        await self._http.aclose()

    # ── core request (OpenAI chat completions) ────────────────────────

    async def _chat_completion(
        self,
        messages: list[dict],
        *,
        json_mode: bool = True,
        temperature: float = 0.7,
    ) -> str:
        """Try each provider with retries, return raw content string."""
        last_error: Exception | None = None

        for provider in self._providers:
            if provider.get("is_anthropic"):
                for attempt in range(MAX_RETRIES):
                    try:
                        return await self._anthropic_request(
                            provider, messages, temperature
                        )
                    except Exception as exc:
                        last_error = exc
                        logger.warning(
                            "anthropic attempt %d failed: %s", attempt + 1, exc
                        )
                continue

            for attempt in range(MAX_RETRIES):
                try:
                    body: dict = {
                        "model": provider["model"],
                        "messages": messages,
                        "temperature": temperature,
                    }
                    if json_mode:
                        body["response_format"] = {"type": "json_object"}

                    resp = await self._http.post(
                        f"{provider['base_url']}/chat/completions",
                        json=body,
                        headers={
                            "Authorization": f"Bearer {provider['api_key']}",
                            "Content-Type": "application/json",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    return data["choices"][0]["message"]["content"]
                except Exception as exc:
                    last_error = exc
                    logger.warning(
                        "%s attempt %d failed: %s",
                        provider["name"],
                        attempt + 1,
                        exc,
                    )

        raise RuntimeError(
            f"All LLM providers failed. Last error: {last_error}"
        )

    async def _anthropic_request(
        self,
        provider: dict,
        messages: list[dict],
        temperature: float,
    ) -> str:
        """Call Anthropic Messages API."""
        system_msg = ""
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_msg = m["content"]
            else:
                api_messages.append(m)

        body = {
            "model": provider["model"],
            "max_tokens": 4096,
            "temperature": temperature,
            "system": system_msg,
            "messages": api_messages,
        }
        resp = await self._http.post(
            f"{provider['base_url']}/messages",
            json=body,
            headers={
                "x-api-key": provider["api_key"],
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]

    # ── streaming (OpenAI SSE) ────────────────────────────────────────

    async def _chat_completion_stream(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream tokens from the first available provider (OpenAI-compat only)."""
        for provider in self._providers:
            if provider.get("is_anthropic"):
                continue
            try:
                body = {
                    "model": provider["model"],
                    "messages": messages,
                    "temperature": temperature,
                    "stream": True,
                    "response_format": {"type": "json_object"},
                }
                async with self._http.stream(
                    "POST",
                    f"{provider['base_url']}/chat/completions",
                    json=body,
                    headers={
                        "Authorization": f"Bearer {provider['api_key']}",
                        "Content-Type": "application/json",
                    },
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data: "):
                            continue
                        payload = line[6:]
                        if payload.strip() == "[DONE]":
                            return
                        chunk = json.loads(payload)
                        delta = chunk["choices"][0].get("delta", {})
                        if "content" in delta and delta["content"]:
                            yield delta["content"]
                return
            except Exception as exc:
                logger.warning("stream %s failed: %s", provider["name"], exc)

        raise RuntimeError("No streaming provider available")

    # ── public methods ────────────────────────────────────────────────

    async def generate_presentation_plan(
        self,
        topic: str,
        requirements: str | None = None,
        style: str | None = None,
        slide_count: int | None = None,
        language: str = "ko",
    ) -> PresentationPlan:
        """주제 + 요구사항을 받아 프레젠테이션 아웃라인 JSON을 생성."""
        user_parts = [f"주제: {topic}"]
        if requirements:
            user_parts.append(f"요구사항: {requirements}")
        if style:
            user_parts.append(f"스타일: {style}")
        if slide_count:
            user_parts.append(f"슬라이드 수: {slide_count}장")
        user_parts.append(f"언어: {language}")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_PLAN},
            {"role": "user", "content": "\n".join(user_parts)},
        ]
        raw = await self._chat_completion(messages)
        return PresentationPlan.model_validate_json(raw)

    async def generate_presentation_plan_stream(
        self,
        topic: str,
        requirements: str | None = None,
        style: str | None = None,
        slide_count: int | None = None,
        language: str = "ko",
    ) -> AsyncIterator[str]:
        """스트리밍 버전 — SSE 토큰을 그대로 yield."""
        user_parts = [f"주제: {topic}"]
        if requirements:
            user_parts.append(f"요구사항: {requirements}")
        if style:
            user_parts.append(f"스타일: {style}")
        if slide_count:
            user_parts.append(f"슬라이드 수: {slide_count}장")
        user_parts.append(f"언어: {language}")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_PLAN},
            {"role": "user", "content": "\n".join(user_parts)},
        ]
        async for token in self._chat_completion_stream(messages):
            yield token

    async def generate_slide_content(
        self,
        plan: PresentationPlan,
        slide_index: int,
    ) -> Slide:
        """개별 슬라이드 상세 콘텐츠 생성."""
        outline: SlideOutline = plan.slides[slide_index]
        context = (
            f"프레젠테이션 제목: {plan.title}\n"
            f"디자인 시스템: {plan.design_system.model_dump_json()}\n"
            f"슬라이드 아웃라인:\n{outline.model_dump_json(indent=2)}"
        )
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_SLIDE},
            {"role": "user", "content": context},
        ]
        raw = await self._chat_completion(messages)
        return Slide.model_validate_json(raw)

    async def refine_slide(
        self,
        slide: Slide,
        instruction: str,
    ) -> Slide:
        """자연어 수정 명령으로 기존 슬라이드를 수정."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_REFINE},
            {
                "role": "user",
                "content": (
                    f"기존 슬라이드:\n{slide.model_dump_json(indent=2)}\n\n"
                    f"수정 명령: {instruction}"
                ),
            },
        ]
        raw = await self._chat_completion(messages)
        return Slide.model_validate_json(raw)

    async def generate_image_prompts(
        self,
        slides: list[Slide],
    ) -> list[str]:
        """슬라이드 목록에서 이미지 프롬프트를 영어로 생성."""
        slide_summaries = []
        for s in slides:
            texts = [
                e.text_props.content
                for e in s.elements
                if e.text_props
            ]
            slide_summaries.append(
                f"Slide {s.order} ({s.layout_type.value}): {' | '.join(texts)}"
            )

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_IMAGE},
            {
                "role": "user",
                "content": "다음 슬라이드들에 필요한 이미지 프롬프트를 생성해주세요:\n"
                + "\n".join(slide_summaries),
            },
        ]
        raw = await self._chat_completion(messages)
        return json.loads(raw)

    # ── Phase 4: advanced editing methods ─────────────────────────

    async def refine_presentation(
        self,
        presentation: Presentation,
        slide_index: int | None,
        instruction: str,
    ) -> dict:
        """프레젠테이션(또는 단일 슬라이드)을 자연어 명령으로 수정.

        Returns dict with "modified_slides" and "changes_summary".
        """
        if slide_index is not None:
            slides_json = presentation.slides[slide_index].model_dump_json(indent=2)
            context = f"대상: 슬라이드 {slide_index + 1}\n{slides_json}"
        else:
            slides_json = json.dumps(
                [s.model_dump(mode="json") for s in presentation.slides],
                ensure_ascii=False,
                indent=2,
            )
            context = f"전체 슬라이드 ({len(presentation.slides)}장):\n{slides_json}"

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_REFINE_FULL},
            {
                "role": "user",
                "content": (
                    f"디자인 시스템:\n{presentation.design_system.model_dump_json(indent=2)}\n\n"
                    f"{context}\n\n"
                    f"수정 명령: {instruction}"
                ),
            },
        ]
        raw = await self._chat_completion(messages)
        return json.loads(raw)

    async def suggest_improvements(
        self,
        presentation: Presentation,
        slide_index: int,
    ) -> dict:
        """슬라이드의 개선점을 분석하여 제안."""
        slide = presentation.slides[slide_index]
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_SUGGEST},
            {
                "role": "user",
                "content": (
                    f"프레젠테이션 제목: {presentation.title}\n"
                    f"디자인 시스템: {presentation.design_system.model_dump_json()}\n\n"
                    f"분석 대상 슬라이드 (#{slide_index + 1}):\n"
                    f"{slide.model_dump_json(indent=2)}"
                ),
            },
        ]
        raw = await self._chat_completion(messages)
        return json.loads(raw)

    async def generate_new_theme(
        self,
        new_style: str,
        current_design: DesignSystem,
    ) -> DesignSystem:
        """새로운 스타일에 맞는 DesignSystem을 생성."""
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT_THEME},
            {
                "role": "user",
                "content": (
                    f"요청 스타일: {new_style}\n\n"
                    f"현재 디자인 시스템 (참고용):\n{current_design.model_dump_json(indent=2)}"
                ),
            },
        ]
        raw = await self._chat_completion(messages)
        return DesignSystem.model_validate_json(raw)


# ─── Module-level singleton ───────────────────────────────────────────

llm_client = AsyncLLMClient()
