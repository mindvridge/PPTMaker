"use client";

import { useEditorStore } from "@/stores/editorStore";
import { usePresentationStore } from "@/stores/presentationStore";
import { Minus, Plus } from "lucide-react";

export function StatusBar() {
  const zoom = useEditorStore((s) => s.zoom);
  const zoomIn = useEditorStore((s) => s.zoomIn);
  const zoomOut = useEditorStore((s) => s.zoomOut);
  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);

  const totalSlides = presentation?.slides.length ?? 0;

  return (
    <div className="h-7 bg-gray-100 border-t border-gray-200 flex items-center justify-between px-4 text-xs text-gray-500 flex-shrink-0">
      <div>
        {totalSlides > 0 && (
          <span>
            슬라이드 {currentSlideIndex + 1} / {totalSlides}
          </span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={zoomOut}
          className="p-0.5 hover:bg-gray-200 rounded"
          aria-label="축소"
        >
          <Minus size={14} />
        </button>
        <span className="w-12 text-center">{zoom}%</span>
        <button
          onClick={zoomIn}
          className="p-0.5 hover:bg-gray-200 rounded"
          aria-label="확대"
        >
          <Plus size={14} />
        </button>
      </div>
    </div>
  );
}
