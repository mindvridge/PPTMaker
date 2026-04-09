"""
내보내기 API 엔드포인트

- POST /api/export/pptx — Presentation JSON → .pptx 다운로드
- POST /api/export/pdf — Presentation JSON → .pdf 다운로드
- POST /api/export/png — 특정 슬라이드 → .png 다운로드
- GET  /api/export/thumbnail/{presentation_id}/{slide_index} — 캐시된 썸네일
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, Response

from app.models.schemas import ExportPngRequest, ExportRequest
from app.services.assembler import pptx_assembler

logger = logging.getLogger(__name__)
router = APIRouter()

# ─── 임시 파일 경로 ──────────────────────────────────────────────────

EXPORT_DIR = Path(os.getenv("EXPORT_DIR", "/tmp/deckcraft/exports"))
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Redis 캐시 (선택적)
_thumbnail_cache: dict[str, bytes] = {}


# ─── helpers ──────────────────────────────────────────────────────────


def _presentation_hash(presentation_json: str) -> str:
    """프레젠테이션 JSON의 짧은 해시를 생성."""
    return hashlib.sha256(presentation_json.encode()).hexdigest()[:16]


async def _pptx_to_pdf(pptx_path: Path) -> Path:
    """LibreOffice headless로 PPTX → PDF 변환."""
    pdf_path = pptx_path.with_suffix(".pdf")
    proc = await asyncio.create_subprocess_exec(
        "soffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        str(pptx_path.parent),
        str(pptx_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(
            f"LibreOffice 변환 실패: {stderr.decode('utf-8', errors='replace')}"
        )
    if not pdf_path.exists():
        raise RuntimeError("PDF 파일이 생성되지 않았습니다.")
    return pdf_path


async def _pdf_to_png(pdf_path: Path, page_index: int = 0) -> Path:
    """pdftoppm으로 PDF → PNG 변환 (특정 페이지)."""
    output_prefix = pdf_path.with_suffix("")
    proc = await asyncio.create_subprocess_exec(
        "pdftoppm",
        "-png",
        "-r", "150",
        "-f", str(page_index + 1),
        "-l", str(page_index + 1),
        "-singlefile",
        str(pdf_path),
        str(output_prefix),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    png_path = Path(f"{output_prefix}.png")
    if proc.returncode != 0 or not png_path.exists():
        raise RuntimeError(
            f"PNG 변환 실패: {stderr.decode('utf-8', errors='replace')}"
        )
    return png_path


# ─── POST /pptx ───────────────────────────────────────────────────────


@router.post("/pptx")
async def export_pptx(req: ExportRequest):
    """Presentation JSON → .pptx 파일 다운로드."""
    try:
        pptx_bytes = pptx_assembler.assemble(req.presentation)
    except Exception as exc:
        logger.exception("PPTX 생성 실패")
        raise HTTPException(status_code=500, detail=f"PPTX 생성 실패: {exc}")

    safe_title = (
        req.presentation.title.replace(" ", "_")[:50] or "presentation"
    )
    filename = f"{safe_title}.pptx"

    # RFC 5987: use ASCII fallback + UTF-8 encoded filename*
    from urllib.parse import quote
    ascii_fallback = "presentation.pptx"
    encoded = quote(filename)
    content_disp = (
        f"attachment; filename=\"{ascii_fallback}\"; "
        f"filename*=UTF-8''{encoded}"
    )

    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": content_disp},
    )


# ─── POST /pdf ────────────────────────────────────────────────────────


@router.post("/pdf")
async def export_pdf(req: ExportRequest):
    """Presentation JSON → .pdf 파일 다운로드."""
    try:
        pptx_bytes = pptx_assembler.assemble(req.presentation)
    except Exception as exc:
        logger.exception("PPTX 생성 실패")
        raise HTTPException(status_code=500, detail=f"PPTX 생성 실패: {exc}")

    # 임시 PPTX 저장
    h = _presentation_hash(req.presentation.model_dump_json())
    pptx_path = EXPORT_DIR / f"{h}.pptx"
    pptx_path.write_bytes(pptx_bytes)

    try:
        pdf_path = await _pptx_to_pdf(pptx_path)
    except Exception as exc:
        logger.exception("PDF 변환 실패")
        raise HTTPException(status_code=500, detail=f"PDF 변환 실패: {exc}")
    finally:
        pptx_path.unlink(missing_ok=True)

    safe_title = (
        req.presentation.title.replace(" ", "_")[:50] or "presentation"
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{safe_title}.pdf",
    )


# ─── POST /png ────────────────────────────────────────────────────────


@router.post("/png")
async def export_png(req: ExportPngRequest):
    """특정 슬라이드를 PNG로 내보내기."""
    if req.slide_index >= len(req.presentation.slides):
        raise HTTPException(status_code=400, detail="slide_index 범위 초과")

    try:
        pptx_bytes = pptx_assembler.assemble(req.presentation)
    except Exception as exc:
        logger.exception("PPTX 생성 실패")
        raise HTTPException(status_code=500, detail=f"PPTX 생성 실패: {exc}")

    h = _presentation_hash(req.presentation.model_dump_json())
    pptx_path = EXPORT_DIR / f"{h}_png.pptx"
    pptx_path.write_bytes(pptx_bytes)

    try:
        pdf_path = await _pptx_to_pdf(pptx_path)
        png_path = await _pdf_to_png(pdf_path, req.slide_index)
    except Exception as exc:
        logger.exception("PNG 변환 실패")
        raise HTTPException(status_code=500, detail=f"PNG 변환 실패: {exc}")
    finally:
        pptx_path.unlink(missing_ok=True)

    return FileResponse(
        path=str(png_path),
        media_type="image/png",
        filename=f"slide_{req.slide_index}.png",
    )


# ─── GET /thumbnail/{presentation_id}/{slide_index} ──────────────────


@router.get("/thumbnail/{presentation_id}/{slide_index}")
async def get_thumbnail(presentation_id: str, slide_index: int):
    """캐싱된 슬라이드 썸네일 반환 (Redis 캐시)."""
    cache_key = f"{presentation_id}:{slide_index}"

    # 메모리 캐시 확인
    if cache_key in _thumbnail_cache:
        return Response(
            content=_thumbnail_cache[cache_key],
            media_type="image/png",
        )

    # 캐시 미스 — 파일 시스템 확인
    png_path = EXPORT_DIR / f"{presentation_id}_slide{slide_index}.png"
    if png_path.exists():
        png_bytes = png_path.read_bytes()
        _thumbnail_cache[cache_key] = png_bytes
        return Response(content=png_bytes, media_type="image/png")

    raise HTTPException(status_code=404, detail="썸네일을 찾을 수 없습니다.")
