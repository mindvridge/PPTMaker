"use client";

import { useEffect } from "react";
import { Toolbar } from "@/components/editor/Toolbar";
import { SlideCanvas } from "@/components/editor/SlideCanvas";
import { SlideListPanel } from "@/components/panels/SlideListPanel";
import { RightPanel } from "@/components/panels/RightPanel";
import { StatusBar } from "@/components/editor/StatusBar";
import { useUIStore } from "@/stores/uiStore";
import { usePresentationStore } from "@/stores/presentationStore";
import { cn } from "@/lib/cn";

export default function EditorPage({
  params,
}: {
  params: { id: string };
}) {
  const leftPanelOpen = useUIStore((s) => s.leftPanelOpen);
  const rightPanelOpen = useUIStore((s) => s.rightPanelOpen);
  const presentation = usePresentationStore((s) => s.presentation);

  // If no presentation loaded yet, show loading
  if (!presentation) {
    return (
      <div className="flex items-center justify-center h-screen text-gray-400">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4" />
          <p className="text-sm">프레젠테이션 로딩 중...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden">
      <Toolbar />

      <div className="flex flex-1 min-h-0">
        <div
          className={cn(
            "border-r border-gray-200 bg-gray-50 transition-all duration-200 flex-shrink-0",
            leftPanelOpen ? "w-[240px]" : "w-0 overflow-hidden"
          )}
        >
          {leftPanelOpen && <SlideListPanel />}
        </div>

        <div className="flex-1 min-w-0 canvas-container relative">
          <SlideCanvas />
        </div>

        <div
          className={cn(
            "border-l border-gray-200 bg-white transition-all duration-200 flex-shrink-0",
            rightPanelOpen ? "w-[320px]" : "w-0 overflow-hidden"
          )}
        >
          {rightPanelOpen && <RightPanel />}
        </div>
      </div>

      <StatusBar />
    </div>
  );
}
