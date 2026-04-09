from fastapi import APIRouter

router = APIRouter()


@router.put("/{presentation_id}")
async def update_presentation(presentation_id: str):
    """프레젠테이션을 수정합니다."""
    return {"message": "Not implemented yet"}
