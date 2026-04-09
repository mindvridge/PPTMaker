from fastapi import APIRouter

router = APIRouter()


@router.post("/")
async def generate_presentation():
    """주제를 받아 AI로 PPT를 생성합니다."""
    return {"message": "Not implemented yet"}
