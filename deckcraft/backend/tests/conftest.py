"""
테스트용 픽스처 — 실제 LLM 호출 없이 테스트할 수 있는 목(mock) 데이터.
"""

import uuid
from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.schemas import (
    Background,
    BackgroundType,
    ColorPalette,
    DesignSystem,
    ElementType,
    FontWeight,
    Fonts,
    LayoutType,
    Language,
    AspectRatio,
    Metadata,
    Position,
    Presentation,
    PresentationPlan,
    Slide,
    SlideElement,
    SlideOutline,
    StylePreset,
    TextAlign,
    TextProps,
    VerticalAlign,
)


@pytest.fixture
def design_system() -> DesignSystem:
    return DesignSystem(
        color_palette=ColorPalette(
            primary="#1E40AF",
            secondary="#3B82F6",
            accent="#F59E0B",
            background="#FFFFFF",
            surface="#F8FAFC",
            text_primary="#0F172A",
            text_secondary="#64748B",
        ),
        fonts=Fonts(
            title="Pretendard Bold",
            subtitle="Pretendard SemiBold",
            body="Pretendard",
            caption="Pretendard Light",
        ),
        style_preset=StylePreset.modern_minimal,
    )


@pytest.fixture
def metadata() -> Metadata:
    return Metadata(
        created_at=datetime.now(timezone.utc),
        language=Language.ko,
        aspect_ratio=AspectRatio.WIDE,
    )


def _make_text_element(
    content: str,
    x: float = 10,
    y: float = 10,
    w: float = 80,
    h: float = 15,
    font_size: float = 24,
    font_weight: str = "bold",
    color: str = "#0F172A",
    z_index: int = 0,
) -> SlideElement:
    return SlideElement(
        id=str(uuid.uuid4()),
        type=ElementType.text,
        position=Position(x=x, y=y, width=w, height=h),
        z_index=z_index,
        text_props=TextProps(
            content=content,
            font_family="Pretendard",
            font_size=font_size,
            font_weight=FontWeight(font_weight),
            color=color,
            align=TextAlign.left,
            vertical_align=VerticalAlign.top,
        ),
    )


def _make_slide(
    order: int,
    layout: LayoutType,
    title: str,
    body: str = "",
) -> Slide:
    elements = [_make_text_element(title, y=5, font_size=28, font_weight="bold")]
    if body:
        elements.append(
            _make_text_element(body, y=22, h=70, font_size=18, font_weight="normal", z_index=1)
        )
    return Slide(
        id=str(uuid.uuid4()),
        order=order,
        layout_type=layout,
        background=Background(type=BackgroundType.solid, color="#FFFFFF"),
        elements=elements,
        speaker_notes=f"슬라이드 {order + 1} 발표자 노트",
    )


@pytest.fixture
def sample_slides() -> list[Slide]:
    return [
        _make_slide(0, LayoutType.title_hero, "AI 스타트업 투자 유치", "혁신적인 기술로 미래를 만듭니다"),
        _make_slide(1, LayoutType.content_bullets, "회사 소개", "• 설립: 2024년\n• 팀: 10명\n• 기술: 자연어 처리"),
        _make_slide(2, LayoutType.two_column, "시장 분석", "국내 AI 시장 규모 10조원\n연평균 성장률 25%"),
        _make_slide(3, LayoutType.stats_kpi, "핵심 지표", "MAU 50만\nARR 30억\n성장률 200%"),
        _make_slide(4, LayoutType.image_text_left, "핵심 기술", "특허 출원 3건\n독자 알고리즘 개발"),
        _make_slide(5, LayoutType.chart_with_text, "매출 추이", "전년 대비 300% 성장"),
        _make_slide(6, LayoutType.timeline, "로드맵", "Q1: 베타 출시\nQ2: 정식 출시\nQ3: 글로벌 진출"),
        _make_slide(7, LayoutType.comparison, "경쟁사 비교", "우리 vs 경쟁사 A"),
        _make_slide(8, LayoutType.quote, "고객 리뷰", "업무 효율이 200% 향상되었습니다"),
        _make_slide(9, LayoutType.ending, "감사합니다", "contact@example.com"),
    ]


@pytest.fixture
def sample_presentation(
    design_system: DesignSystem,
    metadata: Metadata,
    sample_slides: list[Slide],
) -> Presentation:
    return Presentation(
        id=str(uuid.uuid4()),
        title="AI 스타트업 투자 유치",
        design_system=design_system,
        slides=sample_slides,
        metadata=metadata,
    )


@pytest.fixture
def sample_plan(
    design_system: DesignSystem,
    metadata: Metadata,
) -> PresentationPlan:
    layouts = [
        ("타이틀", LayoutType.title_hero),
        ("회사 소개", LayoutType.content_bullets),
        ("시장 분석", LayoutType.two_column),
        ("핵심 지표", LayoutType.stats_kpi),
        ("핵심 기술", LayoutType.image_text_left),
        ("매출 추이", LayoutType.chart_with_text),
        ("로드맵", LayoutType.timeline),
        ("경쟁사 비교", LayoutType.comparison),
        ("고객 리뷰", LayoutType.quote),
        ("감사합니다", LayoutType.ending),
    ]
    return PresentationPlan(
        title="AI 스타트업 투자 유치",
        design_system=design_system,
        slides=[
            SlideOutline(
                order=i,
                layout_type=lt,
                title=title,
                key_points=[f"포인트 {j+1}" for j in range(3)],
                speaker_notes=f"슬라이드 {i+1} 노트",
            )
            for i, (title, lt) in enumerate(layouts)
        ],
        metadata=metadata,
    )


@pytest.fixture
def async_client():
    """FastAPI 테스트 클라이언트."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
