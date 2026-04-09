from fastapi import APIRouter

router = APIRouter()


@router.post("/{presentation_id}/pptx")
async def export_pptx(presentation_id: str):
    """프레젠테이션을 PPTX로 내보냅니다."""
    return {"message": "Not implemented yet"}


@router.post("/{presentation_id}/pdf")
async def export_pdf(presentation_id: str):
    """프레젠테이션을 PDF로 내보냅니다."""
    return {"message": "Not implemented yet"}
