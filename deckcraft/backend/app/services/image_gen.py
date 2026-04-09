"""
이미지 생성 서비스

ComfyUI FLUX API 또는 fal.ai API를 호출하여 프레젠테이션용 이미지를 생성합니다.
"""

from __future__ import annotations

import logging
import os

import httpx

logger = logging.getLogger(__name__)

COMFYUI_BASE_URL = os.getenv("COMFYUI_BASE_URL", "")
FAL_API_KEY = os.getenv("FAL_API_KEY", "")


async def generate_image(
    prompt: str,
    style: str | None = None,
    size: str | None = "1024x576",
) -> str:
    """이미지 생성 후 URL을 반환."""

    if style:
        prompt = f"{prompt}, {style} style"

    # fal.ai FLUX 우선
    if FAL_API_KEY:
        return await _fal_generate(prompt, size)

    # ComfyUI 폴백
    if COMFYUI_BASE_URL:
        return await _comfyui_generate(prompt, size)

    raise RuntimeError(
        "이미지 생성 서비스가 설정되지 않았습니다. "
        "FAL_API_KEY 또는 COMFYUI_BASE_URL을 설정하세요."
    )


async def _fal_generate(prompt: str, size: str | None) -> str:
    """fal.ai FLUX API 호출."""
    width, height = (int(d) for d in (size or "1024x576").split("x"))

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://fal.run/fal-ai/flux/dev",
            json={
                "prompt": prompt,
                "image_size": {"width": width, "height": height},
                "num_images": 1,
            },
            headers={
                "Authorization": f"Key {FAL_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["images"][0]["url"]


async def _comfyui_generate(prompt: str, size: str | None) -> str:
    """ComfyUI FLUX API 호출."""
    width, height = (int(d) for d in (size or "1024x576").split("x"))

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            f"{COMFYUI_BASE_URL}/api/generate",
            json={
                "prompt": prompt,
                "width": width,
                "height": height,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("url", data.get("image_url", ""))
