/**
 * Fabric.js 유틸리티 함수
 * 슬라이드 JSON ↔ Fabric.js 캔버스 변환에 사용되는 공통 헬퍼.
 */

const BASE_WIDTH = 1280;
const BASE_HEIGHT = 720;

/** 퍼센트 → 픽셀 */
export function pctToPx(pct: number, base: number): number {
  return (pct / 100) * base;
}

/** 픽셀 → 퍼센트 */
export function pxToPct(px: number, base: number): number {
  return (px / base) * 100;
}

/** Fabric 객체 → 퍼센트 position */
export function fabricToPosition(obj: {
  left: number;
  top: number;
  width: number;
  height: number;
  scaleX?: number;
  scaleY?: number;
}) {
  return {
    x: pxToPct(obj.left, BASE_WIDTH),
    y: pxToPct(obj.top, BASE_HEIGHT),
    width: pxToPct(obj.width * (obj.scaleX ?? 1), BASE_WIDTH),
    height: pxToPct(obj.height * (obj.scaleY ?? 1), BASE_HEIGHT),
  };
}

/** 슬라이드 캔버스 크기 계산 (컨테이너에 맞춤) */
export function calcCanvasScale(
  containerW: number,
  containerH: number,
  canvasW: number = BASE_WIDTH,
  canvasH: number = BASE_HEIGHT
): number {
  const padding = 40;
  const scaleX = (containerW - padding * 2) / canvasW;
  const scaleY = (containerH - padding * 2) / canvasH;
  return Math.min(scaleX, scaleY, 1);
}
