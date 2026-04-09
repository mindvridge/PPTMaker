"""
DeckCraft 슬라이드 데이터 모델 (Pydantic v2)

shared/slide-schema.json, frontend/src/lib/slide-model.ts 와 동기화됨.
LLM이 이 JSON을 생성하고, python-pptx가 이 모델로 PPTX를 조립합니다.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────────────


class Language(str, Enum):
    ko = "ko"
    en = "en"


class AspectRatio(str, Enum):
    WIDE = "16:9"
    STANDARD = "4:3"


class StylePreset(str, Enum):
    modern_minimal = "modern_minimal"
    corporate = "corporate"
    creative = "creative"
    academic = "academic"


class LayoutType(str, Enum):
    title_hero = "title_hero"
    title_image = "title_image"
    content_bullets = "content_bullets"
    two_column = "two_column"
    three_column = "three_column"
    image_text_left = "image_text_left"
    image_text_right = "image_text_right"
    full_image = "full_image"
    chart_with_text = "chart_with_text"
    comparison = "comparison"
    timeline = "timeline"
    stats_kpi = "stats_kpi"
    quote = "quote"
    section_header = "section_header"
    table = "table"
    ending = "ending"
    blank = "blank"


class FontWeight(str, Enum):
    normal = "normal"
    bold = "bold"


class TextAlign(str, Enum):
    left = "left"
    center = "center"
    right = "right"


class VerticalAlign(str, Enum):
    top = "top"
    middle = "middle"
    bottom = "bottom"


class ImageFit(str, Enum):
    cover = "cover"
    contain = "contain"
    fill = "fill"


class ShapeType(str, Enum):
    rectangle = "rectangle"
    circle = "circle"
    triangle = "triangle"
    line = "line"
    arrow = "arrow"


class ChartType(str, Enum):
    bar = "bar"
    line = "line"
    pie = "pie"
    donut = "donut"
    area = "area"


class TableStyle(str, Enum):
    striped = "striped"
    bordered = "bordered"
    minimal = "minimal"


class BackgroundType(str, Enum):
    solid = "solid"
    gradient = "gradient"
    image = "image"


class ElementType(str, Enum):
    text = "text"
    image = "image"
    shape = "shape"
    chart = "chart"
    icon = "icon"
    table = "table"


# ─── Sub-models ───────────────────────────────────────────────────────


class ColorPalette(BaseModel):
    primary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    secondary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    accent: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    background: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    surface: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    text_primary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    text_secondary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class Fonts(BaseModel):
    title: str
    subtitle: str
    body: str
    caption: str


class DesignSystem(BaseModel):
    color_palette: ColorPalette
    fonts: Fonts
    style_preset: StylePreset


class Metadata(BaseModel):
    created_at: datetime
    language: Language
    aspect_ratio: AspectRatio


class Position(BaseModel):
    """퍼센트 좌표 (0-100)"""

    x: float = Field(ge=0, le=100)
    y: float = Field(ge=0, le=100)
    width: float = Field(ge=0, le=100)
    height: float = Field(ge=0, le=100)


class TextProps(BaseModel):
    content: str
    font_family: str
    font_size: float = Field(gt=0, description="pt 단위")
    font_weight: FontWeight
    color: str = Field(description="hex 색상 또는 design_system 참조 키")
    align: TextAlign
    vertical_align: VerticalAlign
    line_height: Optional[float] = None


class ImageProps(BaseModel):
    src: str = Field(description="URL 또는 로컬 경로")
    alt: str
    fit: ImageFit
    ai_prompt: Optional[str] = Field(
        default=None, description="AI 이미지 생성 프롬프트 (미생성 시)"
    )
    border_radius: Optional[float] = Field(default=None, ge=0)


class ShapeProps(BaseModel):
    shape_type: ShapeType
    fill: str
    stroke: Optional[str] = None
    stroke_width: Optional[float] = Field(default=None, ge=0)
    border_radius: Optional[float] = Field(default=None, ge=0)


class ChartDataset(BaseModel):
    label: str
    values: list[float]
    color: Optional[str] = None


class ChartData(BaseModel):
    labels: list[str]
    datasets: list[ChartDataset]


class ChartProps(BaseModel):
    chart_type: ChartType
    data: ChartData
    show_legend: bool = True


class TableProps(BaseModel):
    headers: list[str]
    rows: list[list[str]]
    style: TableStyle = TableStyle.striped


class Gradient(BaseModel):
    from_color: str = Field(alias="from")
    to: str
    direction: float


class Background(BaseModel):
    type: BackgroundType
    color: Optional[str] = None
    gradient: Optional[Gradient] = None
    image: Optional[ImageProps] = None


# ─── SlideElement ─────────────────────────────────────────────────────


class SlideElement(BaseModel):
    id: str
    type: ElementType
    position: Position
    rotation: float = 0
    opacity: float = Field(default=1, ge=0, le=1)
    z_index: int

    text_props: Optional[TextProps] = None
    image_props: Optional[ImageProps] = None
    shape_props: Optional[ShapeProps] = None
    chart_props: Optional[ChartProps] = None
    table_props: Optional[TableProps] = None


# ─── Slide ────────────────────────────────────────────────────────────


class Slide(BaseModel):
    id: str
    order: int = Field(ge=0)
    layout_type: LayoutType
    background: Background
    elements: list[SlideElement]
    speaker_notes: str
    transition: Optional[str] = None


# ─── Presentation (root) ─────────────────────────────────────────────


class Presentation(BaseModel):
    id: str
    title: str
    design_system: DesignSystem
    slides: list[Slide] = Field(min_length=1)
    metadata: Metadata


# ─── Plan / Request / Response models ────────────────────────────────


class SlideOutline(BaseModel):
    """LLM이 생성하는 슬라이드 아웃라인 (상세 콘텐츠 생성 전)"""

    order: int = Field(ge=0)
    layout_type: LayoutType
    title: str
    key_points: list[str] = Field(default_factory=list, max_length=5)
    speaker_notes: str = ""
    needs_image: bool = False
    image_description: Optional[str] = None


class PresentationPlan(BaseModel):
    """LLM이 생성하는 프레젠테이션 계획 (아웃라인)"""

    title: str
    design_system: DesignSystem
    slides: list[SlideOutline]
    metadata: Metadata


class GeneratePlanRequest(BaseModel):
    topic: str
    requirements: Optional[str] = None
    style: Optional[str] = None
    slide_count: Optional[int] = Field(default=None, ge=3, le=30)
    language: Language = Language.ko


class GenerateFullRequest(BaseModel):
    plan: PresentationPlan


class GenerateImageRequest(BaseModel):
    prompt: str
    style: Optional[str] = None
    size: Optional[str] = "1024x576"


class ExportRequest(BaseModel):
    presentation: Presentation


class ExportPngRequest(BaseModel):
    presentation: Presentation
    slide_index: int = Field(ge=0)
