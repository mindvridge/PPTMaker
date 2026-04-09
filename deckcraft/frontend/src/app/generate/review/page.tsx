"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  GripVertical,
  Plus,
  Trash2,
  Edit3,
  Check,
  ChevronRight,
  Layout,
  Palette,
  Type,
  Sparkles,
} from "lucide-react";
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
import { GenerationProgress } from "@/components/GenerationProgress";
import { usePresentationStore } from "@/stores/presentationStore";
import { cn } from "@/lib/cn";

// ─── Layout type labels ─────────────────────────────────────────────

const LAYOUT_LABELS: Record<string, string> = {
  title_hero: "타이틀 히어로",
  title_image: "타이틀 + 이미지",
  content_bullets: "불릿 리스트",
  two_column: "2컬럼",
  three_column: "3컬럼",
  image_text_left: "이미지(좌) + 텍스트",
  image_text_right: "텍스트 + 이미지(우)",
  full_image: "풀 이미지",
  chart_with_text: "차트 + 텍스트",
  comparison: "비교",
  timeline: "타임라인",
  stats_kpi: "KPI 카드",
  quote: "인용",
  section_header: "섹션 헤더",
  table: "테이블",
  ending: "엔딩",
  blank: "빈 슬라이드",
};

const LAYOUT_OPTIONS = Object.entries(LAYOUT_LABELS).map(([value, label]) => ({
  value,
  label,
}));

// ─── Types ───────────────────────────────────────────────────────────

interface SlideOutline {
  order: number;
  layout_type: string;
  title: string;
  key_points: string[];
  speaker_notes: string;
  needs_image: boolean;
  image_description: string | null;
}

interface PresentationPlan {
  title: string;
  design_system: any;
  slides: SlideOutline[];
  metadata: any;
}

// ─── Sortable slide item ─────────────────────────────────────────────

function SortableSlideItem({
  slide,
  index,
  isSelected,
  onClick,
  onUpdate,
  onDelete,
}: {
  slide: SlideOutline;
  index: number;
  isSelected: boolean;
  onClick: () => void;
  onUpdate: (s: SlideOutline) => void;
  onDelete: () => void;
}) {
  const [editingTitle, setEditingTitle] = useState(false);
  const { attributes, listeners, setNodeRef, transform, transition } =
    useSortable({ id: `slide-${index}` });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      onClick={onClick}
      className={cn(
        "group flex items-start gap-2 px-3 py-2.5 rounded-lg border cursor-pointer transition-all",
        isSelected
          ? "border-blue-400 bg-blue-50"
          : "border-transparent hover:bg-gray-50"
      )}
    >
      {/* Drag handle */}
      <div
        {...attributes}
        {...listeners}
        className="mt-1 cursor-grab active:cursor-grabbing text-gray-300 hover:text-gray-500"
      >
        <GripVertical size={14} />
      </div>

      {/* Number */}
      <div className="w-5 h-5 rounded-full bg-gray-200 text-[10px] flex items-center justify-center font-medium text-gray-600 flex-shrink-0 mt-0.5">
        {index + 1}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        {editingTitle ? (
          <input
            autoFocus
            defaultValue={slide.title}
            onBlur={(e) => {
              onUpdate({ ...slide, title: e.target.value });
              setEditingTitle(false);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                onUpdate({
                  ...slide,
                  title: (e.target as HTMLInputElement).value,
                });
                setEditingTitle(false);
              }
            }}
            onClick={(e) => e.stopPropagation()}
            className="w-full text-sm font-medium border border-blue-300 rounded px-1.5 py-0.5 focus:outline-none"
          />
        ) : (
          <div
            className="text-sm font-medium text-gray-800 truncate"
            onDoubleClick={(e) => {
              e.stopPropagation();
              setEditingTitle(true);
            }}
          >
            {slide.title || "제목 없음"}
          </div>
        )}

        <div className="flex items-center gap-2 mt-1">
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-500">
            {LAYOUT_LABELS[slide.layout_type] ?? slide.layout_type}
          </span>
          {slide.needs_image && (
            <span className="text-[10px] text-blue-500">IMG</span>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => {
            e.stopPropagation();
            setEditingTitle(true);
          }}
          className="p-1 rounded hover:bg-gray-200"
          title="편집"
        >
          <Edit3 size={12} />
        </button>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 rounded hover:bg-red-100 text-red-500"
          title="삭제"
        >
          <Trash2 size={12} />
        </button>
      </div>
    </div>
  );
}

// ─── Design system preview ───────────────────────────────────────────

function DesignPreview({ designSystem }: { designSystem: any }) {
  if (!designSystem) return null;
  const palette = designSystem.color_palette;
  const fonts = designSystem.fonts;

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-4 space-y-3">
      <h3 className="text-xs font-medium text-gray-500 flex items-center gap-1.5">
        <Palette size={14} />
        디자인 시스템
      </h3>

      {/* Color palette */}
      {palette && (
        <div className="flex gap-1.5">
          {Object.entries(palette).map(([key, color]) => (
            <div key={key} className="text-center">
              <div
                className="w-8 h-8 rounded-lg border border-gray-200"
                style={{ backgroundColor: color as string }}
                title={key}
              />
              <span className="text-[8px] text-gray-400 mt-0.5 block">
                {key.replace("text_", "T.").replace("_", "")}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Fonts preview */}
      {fonts && (
        <div className="space-y-1">
          <div className="text-xs text-gray-400 flex items-center gap-1">
            <Type size={12} />
            폰트
          </div>
          <div className="text-sm font-bold" style={{ fontFamily: fonts.title }}>
            {fonts.title}
          </div>
          <div className="text-xs text-gray-600" style={{ fontFamily: fonts.body }}>
            {fonts.body}
          </div>
        </div>
      )}

      {/* Style preset */}
      {designSystem.style_preset && (
        <div className="text-xs text-gray-500">
          프리셋: <span className="font-medium">{designSystem.style_preset}</span>
        </div>
      )}
    </div>
  );
}

// ─── Main review page ────────────────────────────────────────────────

export default function ReviewPage() {
  const router = useRouter();
  const setPresentation = usePresentationStore((s) => s.setPresentation);

  const [plan, setPlan] = useState<PresentationPlan | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [genProgress, setGenProgress] = useState(0);
  const [genSteps, setGenSteps] = useState<
    { label: string; status: "done" | "active" | "pending" }[]
  >([]);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } })
  );

  // Load plan from sessionStorage
  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = sessionStorage.getItem("deckcraft_plan");
    if (raw) {
      try {
        setPlan(JSON.parse(raw));
      } catch {
        router.push("/");
      }
    } else {
      router.push("/");
    }
  }, [router]);

  const updateSlide = (index: number, slide: SlideOutline) => {
    if (!plan) return;
    const updated = [...plan.slides];
    updated[index] = slide;
    setPlan({ ...plan, slides: updated });
  };

  const deleteSlide = (index: number) => {
    if (!plan || plan.slides.length <= 1) return;
    const updated = plan.slides.filter((_, i) => i !== index);
    updated.forEach((s, i) => (s.order = i));
    setPlan({ ...plan, slides: updated });
    if (selectedIndex >= updated.length) {
      setSelectedIndex(updated.length - 1);
    }
  };

  const addSlide = () => {
    if (!plan) return;
    const newSlide: SlideOutline = {
      order: plan.slides.length,
      layout_type: "content_bullets",
      title: "새 슬라이드",
      key_points: [],
      speaker_notes: "",
      needs_image: false,
      image_description: null,
    };
    setPlan({ ...plan, slides: [...plan.slides, newSlide] });
  };

  const handleDragEnd = (event: DragEndEvent) => {
    if (!plan) return;
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const fromIdx = plan.slides.findIndex(
      (_, i) => `slide-${i}` === active.id
    );
    const toIdx = plan.slides.findIndex(
      (_, i) => `slide-${i}` === over.id
    );
    if (fromIdx === -1 || toIdx === -1) return;

    const updated = [...plan.slides];
    const [moved] = updated.splice(fromIdx, 1);
    updated.splice(toIdx, 0, moved);
    updated.forEach((s, i) => (s.order = i));
    setPlan({ ...plan, slides: updated });
  };

  // ── Generate full presentation ────────────────────────────────

  const handleGenerateFull = async () => {
    if (!plan) return;
    setGenerating(true);
    setGenProgress(0);

    const steps = [
      { label: "디자인 시스템 설정", status: "active" as const },
      ...plan.slides.map((s, i) => ({
        label: `슬라이드 ${i + 1}: ${s.title}`,
        status: "pending" as const,
      })),
      { label: "이미지 프롬프트 생성", status: "pending" as const },
    ];
    setGenSteps(steps);

    try {
      const { apiStream: stream } = await import("@/lib/api");
      await stream(
        "/api/generate/full",
        { plan },
        (event, data) => {
          if (event === "status" || event === "slide_complete") {
            setGenProgress(data.progress ?? 0);
          }

          if (event === "slide_complete" && typeof data.slide_index === "number") {
            setGenSteps((prev) =>
              prev.map((s, i) => {
                if (i === 0 && s.status === "active")
                  return { ...s, status: "done" };
                // +1 because index 0 is "design system"
                if (i === data.slide_index + 1)
                  return { ...s, status: "done" };
                if (i === data.slide_index + 2 && s.status === "pending")
                  return { ...s, status: "active" };
                return s;
              })
            );
          }

          if (event === "image_prompts") {
            setGenSteps((prev) =>
              prev.map((s, i) =>
                i === prev.length - 1 ? { ...s, status: "done" } : s
              )
            );
          }

          if (event === "complete" && data.presentation) {
            setPresentation(data.presentation);
            setGenProgress(1);
            // Mark all done
            setGenSteps((prev) =>
              prev.map((s) => ({ ...s, status: "done" as const }))
            );
            setTimeout(() => {
              router.push(`/editor/${data.presentation.id}`);
            }, 2000);
          }
        }
      );
    } catch (err: any) {
      console.error("Generation failed:", err);
      setGenerating(false);
    }
  };

  // ── Generating: show progress ─────────────────────────────────

  if (generating) {
    return (
      <GenerationProgress
        progress={genProgress}
        steps={genSteps}
        title={plan?.title ?? "프레젠테이션"}
      />
    );
  }

  // ── Not loaded yet ────────────────────────────────────────────

  if (!plan) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
      </div>
    );
  }

  const selectedSlide = plan.slides[selectedIndex];

  // ── Review UI ─────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between flex-shrink-0">
        <div>
          <button
            onClick={() => router.push("/")}
            className="text-xs text-gray-400 hover:text-gray-600"
          >
            &larr; 새로 만들기
          </button>
          <h1 className="text-lg font-semibold text-gray-800">
            {plan.title}
          </h1>
        </div>

        <button
          onClick={handleGenerateFull}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 transition-colors"
        >
          <Sparkles size={16} />
          이대로 생성하기
          <ChevronRight size={16} />
        </button>
      </header>

      {/* Body */}
      <div className="flex flex-1 min-h-0">
        {/* Left: slide outline list */}
        <div className="w-[360px] border-r border-gray-200 bg-white flex flex-col flex-shrink-0">
          <div className="flex items-center justify-between px-4 py-2.5 border-b border-gray-100">
            <span className="text-xs font-medium text-gray-500">
              슬라이드 아웃라인 ({plan.slides.length}장)
            </span>
            <button
              onClick={addSlide}
              className="p-1 hover:bg-gray-100 rounded text-gray-500"
              title="슬라이드 추가"
            >
              <Plus size={16} />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto panel-scroll p-2">
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={plan.slides.map((_, i) => `slide-${i}`)}
                strategy={verticalListSortingStrategy}
              >
                {plan.slides.map((slide, i) => (
                  <SortableSlideItem
                    key={`slide-${i}`}
                    slide={slide}
                    index={i}
                    isSelected={i === selectedIndex}
                    onClick={() => setSelectedIndex(i)}
                    onUpdate={(s) => updateSlide(i, s)}
                    onDelete={() => deleteSlide(i)}
                  />
                ))}
              </SortableContext>
            </DndContext>
          </div>
        </div>

        {/* Right: slide detail + design preview */}
        <div className="flex-1 p-6 overflow-y-auto space-y-5">
          {selectedSlide && (
            <>
              {/* Slide detail card */}
              <div className="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-semibold text-gray-800">
                    {selectedIndex + 1}. {selectedSlide.title}
                  </h2>
                  <select
                    value={selectedSlide.layout_type}
                    onChange={(e) =>
                      updateSlide(selectedIndex, {
                        ...selectedSlide,
                        layout_type: e.target.value,
                      })
                    }
                    className="text-xs border border-gray-200 rounded-lg px-2 py-1"
                  >
                    {LAYOUT_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Key points */}
                <div>
                  <h3 className="text-xs font-medium text-gray-500 mb-2">
                    핵심 포인트
                  </h3>
                  {selectedSlide.key_points.length > 0 ? (
                    <ul className="space-y-1.5">
                      {selectedSlide.key_points.map((point, pi) => (
                        <li key={pi} className="flex items-start gap-2">
                          <span className="text-blue-400 mt-0.5">•</span>
                          <input
                            value={point}
                            onChange={(e) => {
                              const updated = [...selectedSlide.key_points];
                              updated[pi] = e.target.value;
                              updateSlide(selectedIndex, {
                                ...selectedSlide,
                                key_points: updated,
                              });
                            }}
                            className="flex-1 text-sm text-gray-700 border-b border-transparent hover:border-gray-200 focus:border-blue-300 focus:outline-none py-0.5"
                          />
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-xs text-gray-400">포인트 없음</p>
                  )}

                  <button
                    onClick={() =>
                      updateSlide(selectedIndex, {
                        ...selectedSlide,
                        key_points: [
                          ...selectedSlide.key_points,
                          "",
                        ],
                      })
                    }
                    className="mt-2 text-xs text-blue-500 hover:text-blue-600"
                  >
                    + 포인트 추가
                  </button>
                </div>

                {/* Speaker notes */}
                <div>
                  <h3 className="text-xs font-medium text-gray-500 mb-1.5">
                    발표자 노트
                  </h3>
                  <textarea
                    value={selectedSlide.speaker_notes}
                    onChange={(e) =>
                      updateSlide(selectedIndex, {
                        ...selectedSlide,
                        speaker_notes: e.target.value,
                      })
                    }
                    rows={2}
                    placeholder="발표 시 참고할 메모..."
                    className="w-full text-xs border border-gray-200 rounded-lg px-3 py-2 focus:outline-none focus:border-blue-300 resize-none"
                  />
                </div>

                {/* Image */}
                {selectedSlide.needs_image && (
                  <div className="bg-blue-50 rounded-lg p-3">
                    <div className="flex items-center gap-1.5 text-xs text-blue-600 font-medium mb-1">
                      <Layout size={12} />
                      이미지 필요
                    </div>
                    <p className="text-xs text-blue-500">
                      {selectedSlide.image_description ?? "설명 없음"}
                    </p>
                  </div>
                )}
              </div>

              {/* Layout preview placeholder */}
              <div className="bg-white rounded-xl border border-gray-200 p-5">
                <h3 className="text-xs font-medium text-gray-500 mb-3 flex items-center gap-1.5">
                  <Layout size={14} />
                  레이아웃 미리보기
                </h3>
                <div className="aspect-video bg-gray-100 rounded-lg flex items-center justify-center text-gray-400 text-sm">
                  {LAYOUT_LABELS[selectedSlide.layout_type] ??
                    selectedSlide.layout_type}
                </div>
              </div>
            </>
          )}

          {/* Design system preview */}
          <DesignPreview designSystem={plan.design_system} />
        </div>
      </div>
    </div>
  );
}
