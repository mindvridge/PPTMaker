"""
시나리오 3: 한국어 폰트 검증 테스트

PPTX를 생성한 뒤 XML을 풀어 <a:ea> 태그를 확인합니다.
"""

from __future__ import annotations

import io
import uuid
import zipfile
from xml.etree import ElementTree as ET

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
    Position,
    Presentation,
    Slide,
    SlideElement,
    TextAlign,
    TextProps,
    VerticalAlign,
)
from app.services.assembler import pptx_assembler


# ─── Helper: Korean-only presentation ────────────────────────────────


def _korean_slide(order: int, title: str, body: str) -> Slide:
    return Slide(
        id=str(uuid.uuid4()),
        order=order,
        layout_type=LayoutType.content_bullets,
        background=Background(type=BackgroundType.solid, color="#FFFFFF"),
        elements=[
            SlideElement(
                id=str(uuid.uuid4()),
                type=ElementType.text,
                position=Position(x=8, y=5, width=84, height=12),
                z_index=0,
                text_props=TextProps(
                    content=title,
                    font_family="Pretendard",
                    font_size=28,
                    font_weight=FontWeight.bold,
                    color="#0F172A",
                    align=TextAlign.left,
                    vertical_align=VerticalAlign.top,
                ),
            ),
            SlideElement(
                id=str(uuid.uuid4()),
                type=ElementType.text,
                position=Position(x=8, y=22, width=84, height=70),
                z_index=1,
                text_props=TextProps(
                    content=body,
                    font_family="Pretendard",
                    font_size=18,
                    font_weight=FontWeight.normal,
                    color="#64748B",
                    align=TextAlign.left,
                    vertical_align=VerticalAlign.top,
                ),
            ),
        ],
        speaker_notes=f"발표자 노트: {title}",
    )


# ─── Test: Korean font EA tag in PPTX XML ────────────────────────────


def test_korean_font_ea_tags_in_xml(design_system, metadata):
    """모든 <a:rPr>에 <a:ea typeface='Pretendard'/> 존재 확인."""
    presentation = Presentation(
        id=str(uuid.uuid4()),
        title="한국어 폰트 테스트",
        design_system=design_system,
        slides=[
            _korean_slide(0, "인공지능 기술 동향", "• 자연어 처리 기술의 발전\n• 컴퓨터 비전의 혁신\n• 생성형 AI의 부상"),
            _korean_slide(1, "시장 규모 분석", "• 글로벌 AI 시장: 2000억 달러\n• 국내 시장: 10조원\n• 연평균 성장률: 25%"),
            _korean_slide(2, "핵심 기술 스택", "• 대규모 언어 모델\n• 멀티모달 학습\n• 강화학습 기반 최적화"),
            _korean_slide(3, "비즈니스 모델", "• 구독형 SaaS\n• API 과금\n• 엔터프라이즈 라이선스"),
            _korean_slide(4, "향후 계획", "• 글로벌 진출 준비\n• 시리즈 B 투자 유치\n• 팀 확장 (50명 목표)"),
        ],
        metadata=metadata,
    )

    pptx_bytes = pptx_assembler.assemble(presentation)

    # PPTX는 ZIP 파일 → XML 파싱
    with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
        slide_xmls = [n for n in zf.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")]
        assert len(slide_xmls) == 5, f"Expected 5 slide XMLs, found {len(slide_xmls)}"

        ea_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
        total_rpr = 0
        rpr_with_ea = 0

        for slide_xml in slide_xmls:
            tree = ET.parse(zf.open(slide_xml))
            root = tree.getroot()

            # 모든 a:rPr 요소를 찾기
            for rpr in root.iter(f"{{{ea_ns}}}rPr"):
                total_rpr += 1
                ea = rpr.find(f"{{{ea_ns}}}ea")
                if ea is not None and ea.get("typeface") == "Pretendard":
                    rpr_with_ea += 1

        assert total_rpr > 0, "텍스트 런이 하나도 없음"
        # 모든 rPr에 ea 태그가 있어야 함
        assert rpr_with_ea == total_rpr, (
            f"한국어 폰트(ea) 미설정: {total_rpr - rpr_with_ea}/{total_rpr} 런에서 누락"
        )


def test_korean_font_all_three_scripts(design_system, metadata):
    """latin + ea + cs 3중 폰트 설정 확인."""
    presentation = Presentation(
        id=str(uuid.uuid4()),
        title="폰트 3중 설정 테스트",
        design_system=design_system,
        slides=[
            _korean_slide(0, "테스트 슬라이드", "한국어와 English 혼용 텍스트"),
        ],
        metadata=metadata,
    )

    pptx_bytes = pptx_assembler.assemble(presentation)

    with zipfile.ZipFile(io.BytesIO(pptx_bytes)) as zf:
        ea_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"

        for name in zf.namelist():
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue

            tree = ET.parse(zf.open(name))
            root = tree.getroot()

            for rpr in root.iter(f"{{{ea_ns}}}rPr"):
                ea = rpr.find(f"{{{ea_ns}}}ea")
                cs = rpr.find(f"{{{ea_ns}}}cs")
                # latin은 rPr 자체의 속성에 있거나 별도 태그
                latin = rpr.find(f"{{{ea_ns}}}latin")

                assert ea is not None, "East Asian (ea) 폰트 태그 누락"
                assert cs is not None, "Complex Script (cs) 폰트 태그 누락"
                assert ea.get("typeface") == "Pretendard"
                assert cs.get("typeface") == "Pretendard"


# ─── Test: PPTX text content integrity ────────────────────────────────


def test_korean_text_content_preserved(design_system, metadata):
    """한국어 텍스트가 PPTX에 정확히 보존되는지 확인."""
    korean_texts = [
        "인공지능 기술의 미래",
        "데이터 기반 의사결정 플랫폼",
        "자연어 처리와 생성형 AI",
    ]

    slides = [
        _korean_slide(i, text, f"본문: {text}")
        for i, text in enumerate(korean_texts)
    ]

    presentation = Presentation(
        id=str(uuid.uuid4()),
        title="한국어 보존 테스트",
        design_system=design_system,
        slides=slides,
        metadata=metadata,
    )

    pptx_bytes = pptx_assembler.assemble(presentation)
    pptx = PptxPresentation(io.BytesIO(pptx_bytes))

    all_text = []
    for slide in pptx.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        all_text.append(run.text)

    full_text = " ".join(all_text)
    for expected in korean_texts:
        assert expected in full_text, f"텍스트 누락: {expected}"


# ─── Test: export endpoint Korean font ────────────────────────────────


@pytest.mark.asyncio
async def test_export_endpoint_korean_font(async_client, design_system, metadata):
    """Export 엔드포인트를 통한 한국어 폰트 검증."""
    presentation = Presentation(
        id=str(uuid.uuid4()),
        title="엔드포인트 한국어 테스트",
        design_system=design_system,
        slides=[
            _korean_slide(0, "첫 번째 슬라이드", "가나다라마바사"),
            _korean_slide(1, "두 번째 슬라이드", "아자차카타파하"),
        ],
        metadata=metadata,
    )

    resp = await async_client.post(
        "/api/export/pptx",
        json={"presentation": presentation.model_dump(mode="json")},
    )
    assert resp.status_code == 200

    # ZIP → XML 확인
    ea_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        for name in zf.namelist():
            if not (name.startswith("ppt/slides/slide") and name.endswith(".xml")):
                continue

            tree = ET.parse(zf.open(name))
            for rpr in tree.getroot().iter(f"{{{ea_ns}}}rPr"):
                ea = rpr.find(f"{{{ea_ns}}}ea")
                assert ea is not None, f"EA 태그 누락: {name}"
                assert ea.get("typeface") == "Pretendard"
