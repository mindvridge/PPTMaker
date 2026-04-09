"use client";

import { useState, useRef } from "react";
import {
  Undo2,
  Redo2,
  Type,
  ImageIcon,
  SquareIcon,
  BarChart3,
  Sparkles,
  Palette,
  Play,
  Download,
  ChevronDown,
  Circle,
  Triangle,
  Minus,
  FileDown,
  FileImage,
  Loader2,
  PanelLeft,
  PanelRight,
} from "lucide-react";
import { usePresentationStore } from "@/stores/presentationStore";
import { useEditorStore } from "@/stores/editorStore";
import { useUIStore } from "@/stores/uiStore";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { SlideElement } from "@/lib/slide-model";

// ─── Helpers ─────────────────────────────────────────────────────────

function newElement(
  type: SlideElement["type"],
  overrides: Partial<SlideElement> = {}
): SlideElement {
  return {
    id: crypto.randomUUID(),
    type,
    position: { x: 25, y: 25, width: 50, height: 30 },
    rotation: 0,
    opacity: 1,
    z_index: 99,
    ...overrides,
  };
}

// ─── Dropdown wrapper ────────────────────────────────────────────────

function Dropdown({
  trigger,
  children,
  align = "left",
}: {
  trigger: React.ReactNode;
  children: React.ReactNode;
  align?: "left" | "right";
}) {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <div onClick={() => setOpen(!open)}>{trigger}</div>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div
            className={cn(
              "absolute top-full mt-1 z-50 bg-white rounded-lg shadow-lg border border-gray-200 py-1 min-w-[160px]",
              align === "right" ? "right-0" : "left-0"
            )}
            onClick={() => setOpen(false)}
          >
            {children}
          </div>
        </>
      )}
    </div>
  );
}

function DropdownItem({
  icon: Icon,
  label,
  onClick,
  disabled,
}: {
  icon?: any;
  label: string;
  onClick: () => void;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="flex items-center gap-2 w-full px-3 py-1.5 text-sm hover:bg-gray-100 text-left disabled:opacity-40"
    >
      {Icon && <Icon size={14} />}
      {label}
    </button>
  );
}

// ─── Toolbar button ──────────────────────────────────────────────────

function ToolBtn({
  icon: Icon,
  label,
  onClick,
  active,
  disabled,
}: {
  icon: any;
  label: string;
  onClick?: () => void;
  active?: boolean;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={label}
      className={cn(
        "p-1.5 rounded hover:bg-gray-200 transition-colors disabled:opacity-30",
        active && "bg-blue-100 text-blue-600"
      )}
    >
      <Icon size={18} />
    </button>
  );
}

// ─── Main Toolbar ────────────────────────────────────────────────────

export function Toolbar() {
  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);
  const updateSlide = usePresentationStore((s) => s.updateSlide);
  const setTitle = usePresentationStore((s) => s.setTitle);
  const undo = usePresentationStore((s) => s.undo);
  const redo = usePresentationStore((s) => s.redo);
  const canUndo = usePresentationStore((s) => s.canUndo);
  const canRedo = usePresentationStore((s) => s.canRedo);

  const toggleAIPanel = useUIStore((s) => s.toggleAIPanel);
  const toggleLeftPanel = useUIStore((s) => s.toggleLeftPanel);
  const toggleRightPanel = useUIStore((s) => s.toggleRightPanel);
  const exportLoading = useUIStore((s) => s.exportLoading);
  const setExportLoading = useUIStore((s) => s.setExportLoading);

  const [titleEditing, setTitleEditing] = useState(false);
  const titleRef = useRef<HTMLInputElement>(null);

  // ── Add element ────────────────────────────────────────────────

  const addElement = (el: SlideElement) => {
    if (!presentation) return;
    const slide = presentation.slides[currentSlideIndex];
    if (!slide) return;
    updateSlide(currentSlideIndex, {
      ...slide,
      elements: [...slide.elements, el],
    });
  };

  const addText = () => {
    addElement(
      newElement("text", {
        text_props: {
          content: "텍스트를 입력하세요",
          font_family: "Pretendard",
          font_size: 24,
          font_weight: "normal",
          color: "#1e293b",
          align: "left",
          vertical_align: "top",
        },
      })
    );
  };

  const addShape = (shapeType: "rectangle" | "circle" | "triangle" | "line") => {
    addElement(
      newElement("shape", {
        position: { x: 30, y: 30, width: 20, height: 20 },
        shape_props: {
          shape_type: shapeType,
          fill: "#94a3b8",
          stroke: undefined,
          stroke_width: 0,
        },
      })
    );
  };

  // ── Export ──────────────────────────────────────────────────────

  const handleExport = async (format: "pptx" | "pdf" | "png") => {
    if (!presentation || exportLoading) return;
    setExportLoading(true);

    try {
      let url: string;
      let filename: string;

      if (format === "png") {
        url = "/api/export/png";
        filename = `slide_${currentSlideIndex}.png`;
      } else {
        url = `/api/export/${format}`;
        filename = `${presentation.title || "presentation"}.${format}`;
      }

      const body =
        format === "png"
          ? JSON.stringify({
              presentation,
              slide_index: currentSlideIndex,
            })
          : JSON.stringify({ presentation });

      const API_BASE =
        process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${API_BASE}${url}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body,
      });

      if (!res.ok) throw new Error(`Export failed: ${res.status}`);

      const blob = await res.blob();
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = filename;
      a.click();
      URL.revokeObjectURL(a.href);
    } catch (err) {
      console.error("Export error:", err);
    } finally {
      setExportLoading(false);
    }
  };

  return (
    <div className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-3 flex-shrink-0">
      {/* ── Left: title + undo/redo ─────────────────────────────── */}
      <div className="flex items-center gap-2 min-w-0">
        <ToolBtn icon={PanelLeft} label="슬라이드 패널" onClick={toggleLeftPanel} />

        <div className="w-px h-5 bg-gray-200" />

        {titleEditing ? (
          <input
            ref={titleRef}
            autoFocus
            defaultValue={presentation?.title ?? ""}
            onBlur={(e) => {
              setTitle(e.target.value);
              setTitleEditing(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                setTitle((e.target as HTMLInputElement).value);
                setTitleEditing(false);
              }
            }}
            className="text-sm font-medium border border-blue-300 rounded px-2 py-0.5 w-48 focus:outline-none"
          />
        ) : (
          <button
            onClick={() => setTitleEditing(true)}
            className="text-sm font-medium text-gray-800 truncate max-w-[200px] hover:text-blue-600"
          >
            {presentation?.title || "제목 없음"}
          </button>
        )}

        <div className="w-px h-5 bg-gray-200" />

        <ToolBtn
          icon={Undo2}
          label="실행취소 (Ctrl+Z)"
          onClick={undo}
          disabled={!canUndo()}
        />
        <ToolBtn
          icon={Redo2}
          label="재실행 (Ctrl+Y)"
          onClick={redo}
          disabled={!canRedo()}
        />
      </div>

      {/* ── Center: add elements ────────────────────────────────── */}
      <div className="flex items-center gap-1">
        <ToolBtn icon={Type} label="텍스트 추가" onClick={addText} />

        <ToolBtn icon={ImageIcon} label="이미지 추가" onClick={() => {
          // 이미지 업로드 trigger
          const input = document.createElement("input");
          input.type = "file";
          input.accept = "image/*";
          input.onchange = () => {
            // TODO: upload + insert
          };
          input.click();
        }} />

        <Dropdown
          trigger={
            <div className="flex items-center p-1.5 rounded hover:bg-gray-200 cursor-pointer">
              <SquareIcon size={18} />
              <ChevronDown size={12} />
            </div>
          }
        >
          <DropdownItem icon={SquareIcon} label="사각형" onClick={() => addShape("rectangle")} />
          <DropdownItem icon={Circle} label="원" onClick={() => addShape("circle")} />
          <DropdownItem icon={Triangle} label="삼각형" onClick={() => addShape("triangle")} />
          <DropdownItem icon={Minus} label="선" onClick={() => addShape("line")} />
        </Dropdown>

        <ToolBtn icon={BarChart3} label="차트 추가" onClick={() => {
          addElement(
            newElement("chart", {
              position: { x: 15, y: 20, width: 50, height: 60 },
              chart_props: {
                chart_type: "bar",
                data: {
                  labels: ["A", "B", "C", "D"],
                  datasets: [{ label: "Series 1", values: [10, 20, 15, 25] }],
                },
                show_legend: true,
              },
            })
          );
        }} />
      </div>

      {/* ── Right: AI, theme, present, export ──────────────────── */}
      <div className="flex items-center gap-1">
        <button
          onClick={toggleAIPanel}
          className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100"
        >
          <Sparkles size={14} />
          AI 수정
        </button>

        <ToolBtn icon={Palette} label="테마 변경" />
        <ToolBtn icon={Play} label="프레젠테이션" />

        <Dropdown
          trigger={
            <div className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-lg bg-blue-500 text-white hover:bg-blue-600 cursor-pointer">
              {exportLoading ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Download size={14} />
              )}
              내보내기
              <ChevronDown size={12} />
            </div>
          }
          align="right"
        >
          <DropdownItem
            icon={FileDown}
            label="PPTX 다운로드"
            onClick={() => handleExport("pptx")}
            disabled={exportLoading}
          />
          <DropdownItem
            icon={FileDown}
            label="PDF 다운로드"
            onClick={() => handleExport("pdf")}
            disabled={exportLoading}
          />
          <DropdownItem
            icon={FileImage}
            label="PNG (현재 슬라이드)"
            onClick={() => handleExport("png")}
            disabled={exportLoading}
          />
        </Dropdown>

        <div className="w-px h-5 bg-gray-200 ml-1" />

        <ToolBtn icon={PanelRight} label="속성 패널" onClick={toggleRightPanel} />
      </div>
    </div>
  );
}
