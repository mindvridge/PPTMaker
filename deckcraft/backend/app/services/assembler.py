"""
python-pptx PPTX 조립 서비스

Presentation JSON → .pptx 바이트.
한국어 폰트(Pretendard) 3중 설정(latin + ea + cs)을 보장합니다.
"""

from __future__ import annotations

import io
import logging
import re
from typing import Sequence

import httpx
from pptx import Presentation as PptxPresentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn, nsmap
from pptx.util import Pt, Emu

from app.models.schemas import (
    Background,
    BackgroundType,
    ChartProps,
    ChartType,
    ElementType,
    FontWeight,
    ImageFit,
    Presentation,
    ShapeProps,
    ShapeType,
    Slide,
    SlideElement,
    TableProps,
    TextAlign,
    TextProps,
    VerticalAlign,
)

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────

# 16:9 슬라이드 크기 (EMU)
SLIDE_WIDTH = 13333400
SLIDE_HEIGHT = 7500938

# 4:3 슬라이드 크기 (EMU)
SLIDE_WIDTH_4_3 = 12192000
SLIDE_HEIGHT_4_3 = 9144000

# python-pptx 정렬 매핑
_ALIGN_MAP = {
    TextAlign.left: PP_ALIGN.LEFT,
    TextAlign.center: PP_ALIGN.CENTER,
    TextAlign.right: PP_ALIGN.RIGHT,
}

_VANCHOR_MAP = {
    VerticalAlign.top: MSO_ANCHOR.TOP,
    VerticalAlign.middle: MSO_ANCHOR.MIDDLE,
    VerticalAlign.bottom: MSO_ANCHOR.BOTTOM,
}

_CHART_TYPE_MAP = {
    ChartType.bar: XL_CHART_TYPE.COLUMN_CLUSTERED,
    ChartType.line: XL_CHART_TYPE.LINE,
    ChartType.pie: XL_CHART_TYPE.PIE,
    ChartType.donut: XL_CHART_TYPE.DOUGHNUT,
    ChartType.area: XL_CHART_TYPE.AREA,
}


# ─── Coordinate helpers ──────────────────────────────────────────────


def pct_to_emu(
    pct_x: float,
    pct_y: float,
    pct_w: float,
    pct_h: float,
    slide_w: int = SLIDE_WIDTH,
    slide_h: int = SLIDE_HEIGHT,
) -> tuple[int, int, int, int]:
    """퍼센트 좌표 → EMU 변환."""
    return (
        int(slide_w * pct_x / 100),
        int(slide_h * pct_y / 100),
        int(slide_w * pct_w / 100),
        int(slide_h * pct_h / 100),
    )


def _hex_to_rgb(hex_color: str) -> RGBColor:
    """hex (#RRGGBB) → RGBColor."""
    h = hex_color.lstrip("#")
    return RGBColor(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


# ─── Korean font helper ──────────────────────────────────────────────


def _set_korean_font(run, font_name: str = "Pretendard") -> None:
    """한국어 폰트를 latin + ea + cs 모두 설정 (이것이 없으면 한글이 깨짐)."""
    run.font.name = font_name  # latin

    rPr = run._r.get_or_add_rPr()

    # East Asian 폰트 (한글 필수)
    ea = rPr.find(qn("a:ea"))
    if ea is None:
        ea = parse_xml(f'<a:ea {_ns_attr()} typeface="{font_name}"/>')
        rPr.append(ea)
    else:
        ea.set("typeface", font_name)

    # Complex Script 폰트
    cs = rPr.find(qn("a:cs"))
    if cs is None:
        cs = parse_xml(f'<a:cs {_ns_attr()} typeface="{font_name}"/>')
        rPr.append(cs)
    else:
        cs.set("typeface", font_name)


def _ns_attr() -> str:
    """OxmlElement에 필요한 namespace 속성."""
    return 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'


# ─── Markdown-subset parser ──────────────────────────────────────────


_MD_PATTERN = re.compile(
    r"(\*\*(.+?)\*\*"  # **bold**
    r"|\*(.+?)\*"       # *italic*
    r"|([^*]+))",       # plain text
)


def _parse_markdown_runs(
    text: str,
) -> list[tuple[str, bool, bool]]:
    """마크다운 서브셋 파싱 → [(text, is_bold, is_italic), ...]."""
    runs: list[tuple[str, bool, bool]] = []
    for m in _MD_PATTERN.finditer(text):
        if m.group(2):       # **bold**
            runs.append((m.group(2), True, False))
        elif m.group(3):     # *italic*
            runs.append((m.group(3), False, True))
        elif m.group(4):     # plain
            runs.append((m.group(4), False, False))
    return runs if runs else [(text, False, False)]


# ─── PptxAssembler ────────────────────────────────────────────────────


class PptxAssembler:
    """Presentation JSON → .pptx 바이트."""

    def __init__(self) -> None:
        self._http = httpx.Client(timeout=30.0)

    def assemble(self, presentation: Presentation) -> bytes:
        """Presentation JSON → .pptx 바이트 반환."""
        prs = PptxPresentation()

        # 슬라이드 크기 설정
        if presentation.metadata.aspect_ratio.value == "16:9":
            prs.slide_width = Emu(SLIDE_WIDTH)
            prs.slide_height = Emu(SLIDE_HEIGHT)
            slide_w, slide_h = SLIDE_WIDTH, SLIDE_HEIGHT
        else:
            prs.slide_width = Emu(SLIDE_WIDTH_4_3)
            prs.slide_height = Emu(SLIDE_HEIGHT_4_3)
            slide_w, slide_h = SLIDE_WIDTH_4_3, SLIDE_HEIGHT_4_3

        # 테마 폰트 설정
        self._set_theme_fonts(prs, presentation.design_system.fonts.title)

        # 슬라이드 생성
        blank_layout = prs.slide_layouts[6]  # blank layout
        for slide_data in sorted(presentation.slides, key=lambda s: s.order):
            pptx_slide = prs.slides.add_slide(blank_layout)
            self._render_slide(
                pptx_slide, slide_data, presentation, slide_w, slide_h
            )

        # 바이트로 반환
        buf = io.BytesIO()
        prs.save(buf)
        return buf.getvalue()

    # ── slide rendering ───────────────────────────────────────────────

    def _render_slide(
        self,
        pptx_slide,
        slide: Slide,
        presentation: Presentation,
        slide_w: int,
        slide_h: int,
    ) -> None:
        """하나의 슬라이드를 렌더링."""
        # 배경
        self._apply_background(pptx_slide, slide.background)

        # 요소를 z_index 순서로 렌더링
        for elem in sorted(slide.elements, key=lambda e: e.z_index):
            self._render_element(pptx_slide, elem, presentation, slide_w, slide_h)

        # 발표자 노트
        if slide.speaker_notes:
            notes_slide = pptx_slide.notes_slide
            notes_slide.notes_text_frame.text = slide.speaker_notes

    # ── background ────────────────────────────────────────────────────

    def _apply_background(self, pptx_slide, bg: Background) -> None:
        """슬라이드 배경 적용."""
        background = pptx_slide.background
        fill = background.fill

        if bg.type == BackgroundType.solid and bg.color:
            fill.solid()
            fill.fore_color.rgb = _hex_to_rgb(bg.color)

        elif bg.type == BackgroundType.gradient and bg.gradient:
            fill.gradient()
            fill.gradient_stops[0].color.rgb = _hex_to_rgb(bg.gradient.from_color)
            fill.gradient_stops[1].color.rgb = _hex_to_rgb(bg.gradient.to)

        elif bg.type == BackgroundType.image and bg.image:
            # 이미지 배경은 별도 처리 필요 (python-pptx 제한)
            pass

    # ── element dispatch ──────────────────────────────────────────────

    def _render_element(
        self,
        pptx_slide,
        elem: SlideElement,
        presentation: Presentation,
        slide_w: int,
        slide_h: int,
    ) -> None:
        """요소 타입별 렌더링 디스패치."""
        left, top, width, height = pct_to_emu(
            elem.position.x,
            elem.position.y,
            elem.position.width,
            elem.position.height,
            slide_w,
            slide_h,
        )

        if elem.type == ElementType.text and elem.text_props:
            self._render_text(pptx_slide, elem.text_props, left, top, width, height)

        elif elem.type == ElementType.image and elem.image_props:
            self._render_image(pptx_slide, elem.image_props, left, top, width, height)

        elif elem.type == ElementType.shape and elem.shape_props:
            self._render_shape(
                pptx_slide, elem.shape_props, left, top, width, height
            )

        elif elem.type == ElementType.chart and elem.chart_props:
            self._render_chart(
                pptx_slide, elem.chart_props, left, top, width, height
            )

        elif elem.type == ElementType.table and elem.table_props:
            self._render_table(
                pptx_slide, elem.table_props, left, top, width, height
            )

    # ── text ──────────────────────────────────────────────────────────

    def _render_text(
        self,
        pptx_slide,
        props: TextProps,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """텍스트 요소 렌더링 (마크다운 파싱 포함)."""
        txBox = pptx_slide.shapes.add_textbox(
            Emu(left), Emu(top), Emu(width), Emu(height)
        )
        tf = txBox.text_frame
        tf.word_wrap = True

        # 세로 정렬
        if props.vertical_align in _VANCHOR_MAP:
            tf.paragraphs[0]  # ensure at least one paragraph
            # XML 직접 설정
            txBody = tf._txBody
            bodyPr = txBody.find(qn("a:bodyPr"))
            if bodyPr is not None:
                anchor_val = {
                    VerticalAlign.top: "t",
                    VerticalAlign.middle: "ctr",
                    VerticalAlign.bottom: "b",
                }
                bodyPr.set("anchor", anchor_val.get(props.vertical_align, "t"))

        # 줄바꿈 분리하여 paragraph 생성
        lines = props.content.split("\n")
        for i, line in enumerate(lines):
            if i == 0:
                para = tf.paragraphs[0]
            else:
                para = tf.add_paragraph()

            para.alignment = _ALIGN_MAP.get(props.align, PP_ALIGN.LEFT)

            if props.line_height:
                para.line_spacing = Pt(props.font_size * props.line_height)

            # 마크다운 파싱
            md_runs = _parse_markdown_runs(line)
            for text, is_bold, is_italic in md_runs:
                run = para.add_run()
                run.text = text

                run.font.size = Pt(props.font_size)
                run.font.bold = is_bold or (props.font_weight == FontWeight.bold)
                run.font.italic = is_italic

                if props.color and props.color.startswith("#"):
                    run.font.color.rgb = _hex_to_rgb(props.color)

                _set_korean_font(run, props.font_family)

    # ── image ─────────────────────────────────────────────────────────

    def _render_image(
        self,
        pptx_slide,
        props,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """이미지 요소 렌더링 (URL이면 다운로드 후 삽입)."""
        try:
            if props.src.startswith(("http://", "https://")):
                resp = self._http.get(props.src)
                resp.raise_for_status()
                image_stream = io.BytesIO(resp.content)
            else:
                image_stream = props.src

            pptx_slide.shapes.add_picture(
                image_stream, Emu(left), Emu(top), Emu(width), Emu(height)
            )
        except Exception as exc:
            logger.warning("Image render failed for %s: %s", props.src, exc)
            # 이미지 실패 시 placeholder 사각형
            shape = pptx_slide.shapes.add_shape(
                1,  # MSO_SHAPE.RECTANGLE
                Emu(left), Emu(top), Emu(width), Emu(height),
            )
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor(0xE0, 0xE0, 0xE0)

    # ── shape ─────────────────────────────────────────────────────────

    def _render_shape(
        self,
        pptx_slide,
        props: ShapeProps,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """도형 요소 렌더링."""
        shape_type_map = {
            ShapeType.rectangle: 1,   # MSO_SHAPE.RECTANGLE
            ShapeType.circle: 9,      # MSO_SHAPE.OVAL
            ShapeType.triangle: 5,    # MSO_SHAPE.ISOSCELES_TRIANGLE
            ShapeType.line: 1,
            ShapeType.arrow: 1,
        }
        auto_shape = shape_type_map.get(props.shape_type, 1)
        shape = pptx_slide.shapes.add_shape(
            auto_shape, Emu(left), Emu(top), Emu(width), Emu(height)
        )

        if props.fill and props.fill.startswith("#"):
            shape.fill.solid()
            shape.fill.fore_color.rgb = _hex_to_rgb(props.fill)

        if props.stroke and props.stroke.startswith("#"):
            shape.line.color.rgb = _hex_to_rgb(props.stroke)
            if props.stroke_width:
                shape.line.width = Pt(props.stroke_width)

    # ── chart ─────────────────────────────────────────────────────────

    def _render_chart(
        self,
        pptx_slide,
        props: ChartProps,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """차트 요소 렌더링."""
        chart_type = _CHART_TYPE_MAP.get(
            props.chart_type, XL_CHART_TYPE.COLUMN_CLUSTERED
        )

        chart_data = CategoryChartData()
        chart_data.categories = props.data.labels

        for ds in props.data.datasets:
            chart_data.add_series(ds.label, ds.values)

        pptx_slide.shapes.add_chart(
            chart_type,
            Emu(left), Emu(top), Emu(width), Emu(height),
            chart_data,
        )

    # ── table ─────────────────────────────────────────────────────────

    def _render_table(
        self,
        pptx_slide,
        props: TableProps,
        left: int,
        top: int,
        width: int,
        height: int,
    ) -> None:
        """테이블 요소 렌더링."""
        rows = len(props.rows) + 1  # +1 for header
        cols = len(props.headers)
        if cols == 0:
            return

        table_shape = pptx_slide.shapes.add_table(
            rows, cols, Emu(left), Emu(top), Emu(width), Emu(height)
        )
        table = table_shape.table

        # 헤더
        for j, header in enumerate(props.headers):
            cell = table.cell(0, j)
            cell.text = header
            for paragraph in cell.text_frame.paragraphs:
                for run in paragraph.runs:
                    run.font.bold = True
                    run.font.size = Pt(12)
                    _set_korean_font(run)

        # 데이터 행
        for i, row in enumerate(props.rows):
            for j, val in enumerate(row):
                if j < cols:
                    cell = table.cell(i + 1, j)
                    cell.text = val
                    for paragraph in cell.text_frame.paragraphs:
                        for run in paragraph.runs:
                            run.font.size = Pt(11)
                            _set_korean_font(run)

    # ── theme fonts ───────────────────────────────────────────────────

    def _set_theme_fonts(self, prs: PptxPresentation, font_name: str) -> None:
        """테마 XML에서 majorFont, minorFont의 latin/ea/cs를 설정."""
        try:
            theme = prs.slide_masters[0].element.find(
                f".//{qn('a:theme')}"
            )
            if theme is None:
                return

            for font_tag in ("a:majorFont", "a:minorFont"):
                font_elem = theme.find(f".//{qn(font_tag)}")
                if font_elem is not None:
                    for sub_tag in ("a:latin", "a:ea", "a:cs"):
                        sub = font_elem.find(qn(sub_tag))
                        if sub is not None:
                            sub.set("typeface", font_name)
        except Exception as exc:
            logger.debug("Theme font setting skipped: %s", exc)


# ─── Module-level singleton ───────────────────────────────────────────

pptx_assembler = PptxAssembler()
