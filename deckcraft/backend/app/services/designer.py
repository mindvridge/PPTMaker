"""
디자인 시스템 / 레이아웃 엔진

LLM은 layout_type만 선택하고, 이 엔진이 elements의 position(x/y/width/height)을
실제 퍼센트 좌표로 계산합니다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from app.models.schemas import (
    Background,
    BackgroundType,
    DesignSystem,
    ElementType,
    FontWeight,
    LayoutType,
    Position,
    Slide,
    SlideElement,
    TextAlign,
    TextProps,
    VerticalAlign,
)


# ─── Layout spec data class ──────────────────────────────────────────


@dataclass
class ElementSpec:
    """단일 요소의 배치 사양."""

    role: str  # "title", "subtitle", "body", "image", "chart", etc.
    element_type: ElementType
    x: float
    y: float
    width: float
    height: float
    font_size: float = 24.0
    font_weight: FontWeight = FontWeight.normal
    align: TextAlign = TextAlign.left
    vertical_align: VerticalAlign = VerticalAlign.top
    color_key: str = "text_primary"
    z_index: int = 0


@dataclass
class LayoutSpec:
    """레이아웃 타입별 요소 배치 규칙."""

    layout_type: LayoutType
    elements: list[ElementSpec] = field(default_factory=list)
    bg_color_key: str = "background"


# ─── Layout definitions (16:9 기준, 퍼센트) ──────────────────────────

_TITLE_ELEMENT = ElementSpec(
    role="title",
    element_type=ElementType.text,
    x=8, y=5, width=84, height=12,
    font_size=28, font_weight=FontWeight.bold,
    color_key="text_primary",
)

LAYOUT_SPECS: dict[LayoutType, LayoutSpec] = {
    LayoutType.title_hero: LayoutSpec(
        layout_type=LayoutType.title_hero,
        bg_color_key="primary",
        elements=[
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=10, y=30, width=80, height=20,
                font_size=44, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="background",
            ),
            ElementSpec(
                role="subtitle", element_type=ElementType.text,
                x=15, y=55, width=70, height=10,
                font_size=20, align=TextAlign.center,
                vertical_align=VerticalAlign.middle,
                color_key="background",
            ),
        ],
    ),
    LayoutType.title_image: LayoutSpec(
        layout_type=LayoutType.title_image,
        elements=[
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=10, y=35, width=80, height=15,
                font_size=40, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="background", z_index=1,
            ),
            ElementSpec(
                role="subtitle", element_type=ElementType.text,
                x=15, y=55, width=70, height=10,
                font_size=18, align=TextAlign.center,
                color_key="background", z_index=1,
            ),
            ElementSpec(
                role="bg_image", element_type=ElementType.image,
                x=0, y=0, width=100, height=100,
                z_index=0,
            ),
        ],
    ),
    LayoutType.content_bullets: LayoutSpec(
        layout_type=LayoutType.content_bullets,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="body", element_type=ElementType.text,
                x=8, y=22, width=84, height=70,
                font_size=18, color_key="text_primary",
            ),
        ],
    ),
    LayoutType.two_column: LayoutSpec(
        layout_type=LayoutType.two_column,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="col_left", element_type=ElementType.text,
                x=8, y=22, width=40, height=70,
                font_size=16, color_key="text_primary",
            ),
            ElementSpec(
                role="col_right", element_type=ElementType.text,
                x=52, y=22, width=40, height=70,
                font_size=16, color_key="text_primary",
            ),
        ],
    ),
    LayoutType.three_column: LayoutSpec(
        layout_type=LayoutType.three_column,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="col_1_icon", element_type=ElementType.icon,
                x=5, y=25, width=28, height=15,
            ),
            ElementSpec(
                role="col_1_heading", element_type=ElementType.text,
                x=5, y=42, width=28, height=8,
                font_size=18, font_weight=FontWeight.bold,
                align=TextAlign.center, color_key="text_primary",
            ),
            ElementSpec(
                role="col_1_text", element_type=ElementType.text,
                x=5, y=52, width=28, height=38,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
            ElementSpec(
                role="col_2_icon", element_type=ElementType.icon,
                x=36, y=25, width=28, height=15,
            ),
            ElementSpec(
                role="col_2_heading", element_type=ElementType.text,
                x=36, y=42, width=28, height=8,
                font_size=18, font_weight=FontWeight.bold,
                align=TextAlign.center, color_key="text_primary",
            ),
            ElementSpec(
                role="col_2_text", element_type=ElementType.text,
                x=36, y=52, width=28, height=38,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
            ElementSpec(
                role="col_3_icon", element_type=ElementType.icon,
                x=67, y=25, width=28, height=15,
            ),
            ElementSpec(
                role="col_3_heading", element_type=ElementType.text,
                x=67, y=42, width=28, height=8,
                font_size=18, font_weight=FontWeight.bold,
                align=TextAlign.center, color_key="text_primary",
            ),
            ElementSpec(
                role="col_3_text", element_type=ElementType.text,
                x=67, y=52, width=28, height=38,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
        ],
    ),
    LayoutType.image_text_left: LayoutSpec(
        layout_type=LayoutType.image_text_left,
        elements=[
            ElementSpec(
                role="image", element_type=ElementType.image,
                x=0, y=0, width=50, height=100,
            ),
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=55, y=15, width=40, height=15,
                font_size=28, font_weight=FontWeight.bold,
                color_key="text_primary",
            ),
            ElementSpec(
                role="body", element_type=ElementType.text,
                x=55, y=35, width=40, height=55,
                font_size=16, color_key="text_primary",
            ),
        ],
    ),
    LayoutType.image_text_right: LayoutSpec(
        layout_type=LayoutType.image_text_right,
        elements=[
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=5, y=15, width=40, height=15,
                font_size=28, font_weight=FontWeight.bold,
                color_key="text_primary",
            ),
            ElementSpec(
                role="body", element_type=ElementType.text,
                x=5, y=35, width=40, height=55,
                font_size=16, color_key="text_primary",
            ),
            ElementSpec(
                role="image", element_type=ElementType.image,
                x=50, y=0, width=50, height=100,
            ),
        ],
    ),
    LayoutType.full_image: LayoutSpec(
        layout_type=LayoutType.full_image,
        elements=[
            ElementSpec(
                role="bg_image", element_type=ElementType.image,
                x=0, y=0, width=100, height=100,
                z_index=0,
            ),
            ElementSpec(
                role="overlay", element_type=ElementType.shape,
                x=0, y=60, width=100, height=40,
                z_index=1,
            ),
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=8, y=65, width=84, height=15,
                font_size=32, font_weight=FontWeight.bold,
                align=TextAlign.left, color_key="background",
                z_index=2,
            ),
            ElementSpec(
                role="subtitle", element_type=ElementType.text,
                x=8, y=82, width=84, height=10,
                font_size=16, color_key="background",
                z_index=2,
            ),
        ],
    ),
    LayoutType.chart_with_text: LayoutSpec(
        layout_type=LayoutType.chart_with_text,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="chart", element_type=ElementType.chart,
                x=5, y=22, width=55, height=70,
            ),
            ElementSpec(
                role="insight", element_type=ElementType.text,
                x=63, y=22, width=32, height=70,
                font_size=16, color_key="text_primary",
            ),
        ],
    ),
    LayoutType.comparison: LayoutSpec(
        layout_type=LayoutType.comparison,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="left_header", element_type=ElementType.text,
                x=8, y=22, width=38, height=10,
                font_size=22, font_weight=FontWeight.bold,
                align=TextAlign.center, color_key="primary",
            ),
            ElementSpec(
                role="left_body", element_type=ElementType.text,
                x=8, y=34, width=38, height=58,
                font_size=16, color_key="text_primary",
            ),
            ElementSpec(
                role="vs_label", element_type=ElementType.text,
                x=46, y=35, width=8, height=10,
                font_size=20, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="accent",
            ),
            ElementSpec(
                role="right_header", element_type=ElementType.text,
                x=54, y=22, width=38, height=10,
                font_size=22, font_weight=FontWeight.bold,
                align=TextAlign.center, color_key="secondary",
            ),
            ElementSpec(
                role="right_body", element_type=ElementType.text,
                x=54, y=34, width=38, height=58,
                font_size=16, color_key="text_primary",
            ),
        ],
    ),
    LayoutType.timeline: LayoutSpec(
        layout_type=LayoutType.timeline,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="timeline_line", element_type=ElementType.shape,
                x=10, y=50, width=80, height=1,
            ),
            ElementSpec(
                role="step_1", element_type=ElementType.text,
                x=8, y=30, width=18, height=40,
                font_size=14, align=TextAlign.center,
                color_key="text_primary",
            ),
            ElementSpec(
                role="step_2", element_type=ElementType.text,
                x=28, y=55, width=18, height=40,
                font_size=14, align=TextAlign.center,
                color_key="text_primary",
            ),
            ElementSpec(
                role="step_3", element_type=ElementType.text,
                x=48, y=30, width=18, height=40,
                font_size=14, align=TextAlign.center,
                color_key="text_primary",
            ),
            ElementSpec(
                role="step_4", element_type=ElementType.text,
                x=68, y=55, width=18, height=40,
                font_size=14, align=TextAlign.center,
                color_key="text_primary",
            ),
        ],
    ),
    LayoutType.stats_kpi: LayoutSpec(
        layout_type=LayoutType.stats_kpi,
        elements=[
            _TITLE_ELEMENT,
            # 기본 3-card 레이아웃 (동적으로 조정됨)
            ElementSpec(
                role="kpi_1_number", element_type=ElementType.text,
                x=5, y=28, width=26, height=20,
                font_size=40, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="primary",
            ),
            ElementSpec(
                role="kpi_1_label", element_type=ElementType.text,
                x=5, y=50, width=26, height=10,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
            ElementSpec(
                role="kpi_1_change", element_type=ElementType.text,
                x=5, y=62, width=26, height=8,
                font_size=12, align=TextAlign.center,
                color_key="accent",
            ),
            ElementSpec(
                role="kpi_2_number", element_type=ElementType.text,
                x=37, y=28, width=26, height=20,
                font_size=40, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="primary",
            ),
            ElementSpec(
                role="kpi_2_label", element_type=ElementType.text,
                x=37, y=50, width=26, height=10,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
            ElementSpec(
                role="kpi_2_change", element_type=ElementType.text,
                x=37, y=62, width=26, height=8,
                font_size=12, align=TextAlign.center,
                color_key="accent",
            ),
            ElementSpec(
                role="kpi_3_number", element_type=ElementType.text,
                x=69, y=28, width=26, height=20,
                font_size=40, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="primary",
            ),
            ElementSpec(
                role="kpi_3_label", element_type=ElementType.text,
                x=69, y=50, width=26, height=10,
                font_size=14, align=TextAlign.center,
                color_key="text_secondary",
            ),
            ElementSpec(
                role="kpi_3_change", element_type=ElementType.text,
                x=69, y=62, width=26, height=8,
                font_size=12, align=TextAlign.center,
                color_key="accent",
            ),
        ],
    ),
    LayoutType.quote: LayoutSpec(
        layout_type=LayoutType.quote,
        bg_color_key="surface",
        elements=[
            ElementSpec(
                role="quote_mark", element_type=ElementType.text,
                x=10, y=15, width=10, height=15,
                font_size=72, font_weight=FontWeight.bold,
                color_key="accent",
            ),
            ElementSpec(
                role="quote_text", element_type=ElementType.text,
                x=12, y=30, width=76, height=30,
                font_size=24, align=TextAlign.center,
                vertical_align=VerticalAlign.middle,
                color_key="text_primary",
            ),
            ElementSpec(
                role="attribution", element_type=ElementType.text,
                x=12, y=65, width=76, height=10,
                font_size=16, align=TextAlign.center,
                color_key="text_secondary",
            ),
        ],
    ),
    LayoutType.section_header: LayoutSpec(
        layout_type=LayoutType.section_header,
        bg_color_key="primary",
        elements=[
            ElementSpec(
                role="section_number", element_type=ElementType.text,
                x=10, y=25, width=80, height=15,
                font_size=18, align=TextAlign.center,
                color_key="background",
            ),
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=10, y=40, width=80, height=20,
                font_size=36, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="background",
            ),
        ],
    ),
    LayoutType.table: LayoutSpec(
        layout_type=LayoutType.table,
        elements=[
            _TITLE_ELEMENT,
            ElementSpec(
                role="table", element_type=ElementType.table,
                x=8, y=22, width=84, height=70,
            ),
        ],
    ),
    LayoutType.ending: LayoutSpec(
        layout_type=LayoutType.ending,
        bg_color_key="primary",
        elements=[
            ElementSpec(
                role="title", element_type=ElementType.text,
                x=10, y=25, width=80, height=20,
                font_size=40, font_weight=FontWeight.bold,
                align=TextAlign.center, vertical_align=VerticalAlign.middle,
                color_key="background",
            ),
            ElementSpec(
                role="subtitle", element_type=ElementType.text,
                x=15, y=50, width=70, height=10,
                font_size=18, align=TextAlign.center,
                color_key="background",
            ),
            ElementSpec(
                role="contact", element_type=ElementType.text,
                x=20, y=68, width=60, height=15,
                font_size=14, align=TextAlign.center,
                color_key="background",
            ),
        ],
    ),
    LayoutType.blank: LayoutSpec(
        layout_type=LayoutType.blank,
        elements=[],
    ),
}


# ─── Helpers ──────────────────────────────────────────────────────────


def _resolve_color(key: str, design: DesignSystem) -> str:
    """color_key를 실제 hex 색상으로 변환. 이미 hex면 그대로 반환."""
    if key.startswith("#"):
        return key
    palette = design.color_palette.model_dump()
    return palette.get(key, design.color_palette.text_primary)


def _luminance(hex_color: str) -> float:
    """상대 밝기 계산 (sRGB)."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) / 255.0 for i in (0, 2, 4))

    def linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * linear(r) + 0.7152 * linear(g) + 0.0722 * linear(b)


def _is_dark_bg(hex_color: str) -> bool:
    """배경이 어두운지 판단."""
    return _luminance(hex_color) < 0.4


def _auto_text_color(bg_color: str, design: DesignSystem) -> str:
    """배경 밝기에 따라 텍스트 색상을 자동 결정."""
    bg_hex = _resolve_color(bg_color, design)
    if _is_dark_bg(bg_hex):
        return design.color_palette.background  # 밝은 텍스트
    return design.color_palette.text_primary  # 어두운 텍스트


def _adjust_font_size(base_size: float, text_length: int) -> float:
    """텍스트 길이에 따라 폰트 크기를 자동 조절."""
    if text_length > 200:
        return max(base_size * 0.7, 12)
    if text_length > 100:
        return max(base_size * 0.85, 14)
    return base_size


def _adjust_bullet_height(base_height: float, bullet_count: int) -> float:
    """불릿 개수에 따라 영역 높이를 동적 계산."""
    if bullet_count <= 3:
        return base_height
    extra = (bullet_count - 3) * 5
    return min(base_height + extra, 75)


# ─── DesignEngine ─────────────────────────────────────────────────────


class DesignEngine:
    """LLM의 layout_type 선택을 실제 좌표로 변환하는 엔진."""

    def get_layout_spec(self, layout_type: LayoutType) -> LayoutSpec:
        """레이아웃 타입별 요소 배치 규칙을 반환."""
        return LAYOUT_SPECS.get(
            layout_type,
            LAYOUT_SPECS[LayoutType.blank],
        )

    def apply_layout(
        self,
        slide: Slide,
        design_system: DesignSystem,
    ) -> Slide:
        """slide의 layout_type에 따라 elements의 position을 자동 계산."""
        spec = self.get_layout_spec(slide.layout_type)

        # 배경 설정
        slide = self._apply_background(slide, spec, design_system)

        # 기존 요소에 레이아웃 좌표 적용
        updated_elements = self._position_elements(
            slide.elements, spec, design_system
        )
        slide = slide.model_copy(update={"elements": updated_elements})
        return slide

    def _apply_background(
        self,
        slide: Slide,
        spec: LayoutSpec,
        design: DesignSystem,
    ) -> Slide:
        """레이아웃 스펙에 따라 배경을 설정 (기존 배경이 없으면)."""
        if slide.background.type != BackgroundType.solid or slide.background.color:
            return slide

        bg_color = _resolve_color(spec.bg_color_key, design)
        new_bg = Background(type=BackgroundType.solid, color=bg_color)
        return slide.model_copy(update={"background": new_bg})

    def _position_elements(
        self,
        elements: list[SlideElement],
        spec: LayoutSpec,
        design: DesignSystem,
    ) -> list[SlideElement]:
        """요소들에 레이아웃 스펙의 좌표를 적용."""
        if not spec.elements:
            return elements

        result: list[SlideElement] = []
        spec_map = {s.role: s for s in spec.elements}

        for i, elem in enumerate(elements):
            # role 매칭: 이름 기반 또는 순서 기반
            matched_spec = self._match_spec(elem, i, spec.elements, spec_map)
            if matched_spec:
                elem = self._apply_spec_to_element(elem, matched_spec, design)
            result.append(elem)

        return result

    def _match_spec(
        self,
        elem: SlideElement,
        index: int,
        spec_list: list[ElementSpec],
        spec_map: dict[str, ElementSpec],
    ) -> ElementSpec | None:
        """요소와 매칭되는 spec을 찾는다."""
        # 같은 타입의 spec들을 순서대로 매칭
        same_type_specs = [
            s for s in spec_list if s.element_type == elem.type
        ]
        # index로 매칭 시도
        type_index = 0
        for j, s in enumerate(spec_list):
            if s.element_type == elem.type:
                if type_index == self._count_preceding_same_type(
                    elem, index, spec_list
                ):
                    return s
                type_index += 1

        # 폴백: 같은 타입의 첫 번째 spec
        return same_type_specs[0] if same_type_specs else None

    def _count_preceding_same_type(
        self,
        elem: SlideElement,
        index: int,
        spec_list: list[ElementSpec],
    ) -> int:
        """현재 요소 앞에 같은 타입의 요소가 몇 개인지."""
        # 단순화: index를 spec list 크기로 모듈러
        same_type_count = sum(
            1 for s in spec_list if s.element_type == elem.type
        )
        if same_type_count == 0:
            return 0
        return index % same_type_count

    def _apply_spec_to_element(
        self,
        elem: SlideElement,
        spec: ElementSpec,
        design: DesignSystem,
    ) -> SlideElement:
        """spec의 좌표와 스타일을 element에 적용."""
        new_pos = Position(
            x=spec.x, y=spec.y,
            width=spec.width, height=spec.height,
        )
        updates: dict = {
            "position": new_pos,
            "z_index": spec.z_index,
        }

        if elem.text_props:
            tp = elem.text_props
            text_len = len(tp.content) if tp.content else 0
            adjusted_size = _adjust_font_size(spec.font_size, text_len)
            color = _resolve_color(spec.color_key, design)

            updates["text_props"] = tp.model_copy(
                update={
                    "font_size": adjusted_size,
                    "font_weight": spec.font_weight,
                    "align": spec.align,
                    "vertical_align": spec.vertical_align,
                    "color": color,
                }
            )

        return elem.model_copy(update=updates)

    def create_slide_from_spec(
        self,
        layout_type: LayoutType,
        design: DesignSystem,
        content_map: dict[str, str] | None = None,
    ) -> Slide:
        """레이아웃 스펙과 콘텐츠 맵으로 완전한 슬라이드를 생성."""
        spec = self.get_layout_spec(layout_type)
        content_map = content_map or {}

        bg_color = _resolve_color(spec.bg_color_key, design)
        bg = Background(type=BackgroundType.solid, color=bg_color)

        elements: list[SlideElement] = []
        for i, es in enumerate(spec.elements):
            content = content_map.get(es.role, "")
            color = _resolve_color(es.color_key, design)

            text_props = None
            if es.element_type == ElementType.text:
                text_props = TextProps(
                    content=content,
                    font_family=design.fonts.title
                    if es.font_weight == FontWeight.bold
                    else design.fonts.body,
                    font_size=_adjust_font_size(es.font_size, len(content)),
                    font_weight=es.font_weight,
                    color=color,
                    align=es.align,
                    vertical_align=es.vertical_align,
                )

            elements.append(
                SlideElement(
                    id=str(uuid.uuid4()),
                    type=es.element_type,
                    position=Position(
                        x=es.x, y=es.y,
                        width=es.width, height=es.height,
                    ),
                    z_index=es.z_index or i,
                    text_props=text_props,
                )
            )

        return Slide(
            id=str(uuid.uuid4()),
            order=0,
            layout_type=layout_type,
            background=bg,
            elements=elements,
            speaker_notes="",
        )


# ─── Module-level singleton ───────────────────────────────────────────

design_engine = DesignEngine()
