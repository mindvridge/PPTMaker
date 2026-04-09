"use client";

import { useCallback, useRef, useState } from "react";
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Plus, Copy, Trash2, ChevronUp, ChevronDown } from "lucide-react";
import { usePresentationStore } from "@/stores/presentationStore";
import { cn } from "@/lib/cn";
import type { Slide, LayoutType } from "@/lib/slide-model";

// ─── Layout options for new slide ────────────────────────────────────

const LAYOUT_OPTIONS: { value: LayoutType; label: string }[] = [
  { value: "content_bullets", label: "불릿 리스트" },
  { value: "two_column", label: "2컬럼" },
  { value: "three_column", label: "3컬럼" },
  { value: "image_text_left", label: "이미지+텍스트(좌)" },
  { value: "image_text_right", label: "이미지+텍스트(우)" },
  { value: "title_hero", label: "타이틀" },
  { value: "section_header", label: "섹션 헤더" },
  { value: "stats_kpi", label: "KPI 카드" },
  { value: "chart_with_text", label: "차트" },
  { value: "comparison", label: "비교" },
  { value: "timeline", label: "타임라인" },
  { value: "quote", label: "인용" },
  { value: "table", label: "테이블" },
  { value: "ending", label: "엔딩" },
  { value: "blank", label: "빈 슬라이드" },
];

function newBlankSlide(layoutType: LayoutType, order: number): Slide {
  return {
    id: crypto.randomUUID(),
    order,
    layout_type: layoutType,
    background: { type: "solid", color: "#ffffff" },
    elements: [],
    speaker_notes: "",
  };
}

// ─── Sortable slide thumbnail ────────────────────────────────────────

function SortableSlideThumbnail({
  slide,
  index,
  isActive,
  onClick,
  onContextMenu,
}: {
  slide: Slide;
  index: number;
  isActive: boolean;
  onClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}) {
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: slide.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  // Simple color preview from background
  const bgColor =
    slide.background.type === "solid" && slide.background.color
      ? slide.background.color
      : "#ffffff";

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...attributes}
      {...listeners}
      onClick={onClick}
      onContextMenu={onContextMenu}
      className={cn(
        "group relative mx-3 mb-2 cursor-pointer rounded-md border-2 transition-all",
        isActive
          ? "border-blue-500 shadow-md"
          : "border-transparent hover:border-gray-300"
      )}
    >
      {/* Slide number */}
      <div className="absolute -left-1 top-0 text-[10px] text-gray-400 font-medium">
        {index + 1}
      </div>

      {/* Thumbnail */}
      <div
        className="ml-4 aspect-video rounded-sm overflow-hidden"
        style={{ backgroundColor: bgColor }}
      >
        {/* Mini preview: show first text element */}
        <div className="p-1.5 text-[6px] leading-tight text-gray-700 truncate">
          {slide.elements
            .filter((e) => e.type === "text" && e.text_props)
            .slice(0, 2)
            .map((e) => (
              <div key={e.id} className="truncate">
                {e.text_props?.content}
              </div>
            ))}
          {slide.elements.length === 0 && (
            <div className="text-gray-400 text-center mt-2">
              {slide.layout_type}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Context menu ────────────────────────────────────────────────────

function ContextMenu({
  x,
  y,
  onDuplicate,
  onDelete,
  onMoveUp,
  onMoveDown,
  onClose,
}: {
  x: number;
  y: number;
  onDuplicate: () => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onClose: () => void;
}) {
  const items = [
    { icon: Copy, label: "복제", action: onDuplicate },
    { icon: ChevronUp, label: "위로 이동", action: onMoveUp },
    { icon: ChevronDown, label: "아래로 이동", action: onMoveDown },
    { icon: Trash2, label: "삭제", action: onDelete, danger: true },
  ];

  return (
    <>
      <div className="fixed inset-0 z-40" onClick={onClose} />
      <div
        className="fixed z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[140px]"
        style={{ left: x, top: y }}
      >
        {items.map((item) => (
          <button
            key={item.label}
            onClick={() => {
              item.action();
              onClose();
            }}
            className={cn(
              "flex items-center gap-2 w-full px-3 py-1.5 text-sm hover:bg-gray-100 text-left",
              (item as any).danger && "text-red-600 hover:bg-red-50"
            )}
          >
            <item.icon size={14} />
            {item.label}
          </button>
        ))}
      </div>
    </>
  );
}

// ─── Main panel ──────────────────────────────────────────────────────

export function SlideListPanel() {
  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);
  const setCurrentSlideIndex = usePresentationStore((s) => s.setCurrentSlideIndex);
  const addSlide = usePresentationStore((s) => s.addSlide);
  const removeSlide = usePresentationStore((s) => s.removeSlide);
  const reorderSlides = usePresentationStore((s) => s.reorderSlides);

  const [contextMenu, setContextMenu] = useState<{
    x: number;
    y: number;
    index: number;
  } | null>(null);
  const [showLayoutPicker, setShowLayoutPicker] = useState(false);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  const slides = presentation?.slides ?? [];

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over || active.id === over.id) return;

      const fromIndex = slides.findIndex((s) => s.id === active.id);
      const toIndex = slides.findIndex((s) => s.id === over.id);
      if (fromIndex !== -1 && toIndex !== -1) {
        reorderSlides(fromIndex, toIndex);
      }
    },
    [slides, reorderSlides]
  );

  const handleAddSlide = (layout: LayoutType) => {
    const slide = newBlankSlide(layout, slides.length);
    addSlide(slide);
    setShowLayoutPicker(false);
  };

  const handleContextMenu = (e: React.MouseEvent, index: number) => {
    e.preventDefault();
    setContextMenu({ x: e.clientX, y: e.clientY, index });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-200">
        <span className="text-xs font-medium text-gray-600">슬라이드</span>
        <div className="relative">
          <button
            onClick={() => setShowLayoutPicker(!showLayoutPicker)}
            className="p-1 hover:bg-gray-200 rounded text-gray-600"
            aria-label="슬라이드 추가"
          >
            <Plus size={16} />
          </button>

          {showLayoutPicker && (
            <>
              <div
                className="fixed inset-0 z-40"
                onClick={() => setShowLayoutPicker(false)}
              />
              <div className="absolute right-0 top-full mt-1 z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 w-44 max-h-64 overflow-y-auto">
                {LAYOUT_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => handleAddSlide(opt.value)}
                    className="block w-full px-3 py-1.5 text-sm text-left hover:bg-gray-100"
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </>
          )}
        </div>
      </div>

      {/* Slide list */}
      <div className="flex-1 overflow-y-auto panel-scroll py-2">
        {slides.length > 0 ? (
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={slides.map((s) => s.id)}
              strategy={verticalListSortingStrategy}
            >
              {slides.map((slide, i) => (
                <SortableSlideThumbnail
                  key={slide.id}
                  slide={slide}
                  index={i}
                  isActive={i === currentSlideIndex}
                  onClick={() => setCurrentSlideIndex(i)}
                  onContextMenu={(e) => handleContextMenu(e, i)}
                />
              ))}
            </SortableContext>
          </DndContext>
        ) : (
          <div className="text-center text-xs text-gray-400 mt-8">
            슬라이드가 없습니다
          </div>
        )}
      </div>

      {/* Context menu */}
      {contextMenu && (
        <ContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          onDuplicate={() => {
            const slide = slides[contextMenu.index];
            if (slide) {
              const dup = {
                ...JSON.parse(JSON.stringify(slide)),
                id: crypto.randomUUID(),
                order: contextMenu.index + 1,
              };
              addSlide(dup, contextMenu.index + 1);
            }
          }}
          onDelete={() => removeSlide(contextMenu.index)}
          onMoveUp={() => {
            if (contextMenu.index > 0) {
              reorderSlides(contextMenu.index, contextMenu.index - 1);
            }
          }}
          onMoveDown={() => {
            if (contextMenu.index < slides.length - 1) {
              reorderSlides(contextMenu.index, contextMenu.index + 1);
            }
          }}
          onClose={() => setContextMenu(null)}
        />
      )}
    </div>
  );
}
