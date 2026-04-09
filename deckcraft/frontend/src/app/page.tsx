"use client";

import { Toolbar } from "@/components/editor/Toolbar";
import { SlideCanvas } from "@/components/editor/SlideCanvas";
import { SlideListPanel } from "@/components/panels/SlideListPanel";
import { RightPanel } from "@/components/panels/RightPanel";
import { StatusBar } from "@/components/editor/StatusBar";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/cn";

export default function Home() {
  const leftPanelOpen = useUIStore((s) => s.leftPanelOpen);
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden">
      {/* 상단 툴바 */}
      <Toolbar />

      {/* 메인 영역 */}
      <div className="flex flex-1 min-h-0">
        {/* 왼쪽 패널 — 슬라이드 썸네일 */}
        <div
          className={cn(
            "border-r border-gray-200 bg-gray-50 transition-all duration-200 flex-shrink-0",
            leftPanelOpen ? "w-[240px]" : "w-0 overflow-hidden"
          )}
        >
          {leftPanelOpen && <SlideListPanel />}
        </div>

        {/* 중앙 캔버스 */}
        <div className="flex-1 min-w-0 canvas-container relative">
          <SlideCanvas />
        </div>

        {/* 오른쪽 패널 — 속성 + AI */}
        <div
          className={cn(
            "border-l border-gray-200 bg-white transition-all duration-200 flex-shrink-0",
            rightPanelOpen ? "w-[320px]" : "w-0 overflow-hidden"
          )}
        >
          {rightPanelOpen && <RightPanel />}
        </div>
      </div>

      {/* 하단 상태바 */}
      <StatusBar />
    </div>
  );
}
