"use client";

import { useState, useRef, useCallback } from "react";
import {
  Settings2,
  Sparkles,
  Type,
  Image,
  Square,
  AlignLeft,
  AlignCenter,
  AlignRight,
  Bold,
  Italic,
  Send,
} from "lucide-react";
import { useUIStore } from "@/stores/uiStore";
import { useEditorStore } from "@/stores/editorStore";
import { usePresentationStore } from "@/stores/presentationStore";
import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/cn";
import type { SlideElement, TextProps } from "@/lib/slide-model";

// ─── Property Panel ──────────────────────────────────────────────────

function PropertyPanel() {
  const selectedElementId = useEditorStore((s) => s.selectedElementId);
  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);
  const updateElement = usePresentationStore((s) => s.updateElement);

  const slide = presentation?.slides[currentSlideIndex];
  const element = slide?.elements.find((e) => e.id === selectedElementId);

  if (!element) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-400 text-sm">
        <Settings2 size={32} className="mb-2 opacity-50" />
        <p>요소를 선택하세요</p>
      </div>
    );
  }

  const updateField = (updates: Partial<SlideElement>) => {
    updateElement(currentSlideIndex, element.id, updates);
  };

  const updateTextProps = (updates: Partial<TextProps>) => {
    if (!element.text_props) return;
    updateField({
      text_props: { ...element.text_props, ...updates },
    });
  };

  return (
    <div className="p-3 space-y-4 text-sm">
      {/* Position */}
      <fieldset>
        <legend className="text-xs font-medium text-gray-500 mb-2">위치 / 크기</legend>
        <div className="grid grid-cols-2 gap-2">
          {(["x", "y", "width", "height"] as const).map((key) => (
            <label key={key} className="flex flex-col">
              <span className="text-[10px] text-gray-400 uppercase">{key}</span>
              <input
                type="number"
                step="0.1"
                value={element.position[key].toFixed(1)}
                onChange={(e) =>
                  updateField({
                    position: {
                      ...element.position,
                      [key]: parseFloat(e.target.value) || 0,
                    },
                  })
                }
                className="w-full border border-gray-200 rounded px-2 py-1 text-xs"
              />
            </label>
          ))}
        </div>
      </fieldset>

      {/* Common: rotation, opacity */}
      <div className="grid grid-cols-2 gap-2">
        <label className="flex flex-col">
          <span className="text-[10px] text-gray-400">회전</span>
          <input
            type="number"
            value={element.rotation ?? 0}
            onChange={(e) =>
              updateField({ rotation: parseFloat(e.target.value) || 0 })
            }
            className="border border-gray-200 rounded px-2 py-1 text-xs"
          />
        </label>
        <label className="flex flex-col">
          <span className="text-[10px] text-gray-400">투명도</span>
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={element.opacity ?? 1}
            onChange={(e) =>
              updateField({ opacity: parseFloat(e.target.value) })
            }
            className="mt-1"
          />
        </label>
      </div>

      {/* Text-specific */}
      {element.type === "text" && element.text_props && (
        <fieldset>
          <legend className="text-xs font-medium text-gray-500 mb-2">텍스트</legend>
          <div className="space-y-2">
            {/* Font family */}
            <select
              value={element.text_props.font_family}
              onChange={(e) => updateTextProps({ font_family: e.target.value })}
              className="w-full border border-gray-200 rounded px-2 py-1 text-xs"
            >
              <option value="Pretendard">Pretendard</option>
              <option value="Pretendard Bold">Pretendard Bold</option>
              <option value="Noto Sans KR">Noto Sans KR</option>
              <option value="NanumSquare Neo">나눔스퀘어 네오</option>
            </select>

            {/* Font size */}
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="1"
                max="200"
                value={element.text_props.font_size}
                onChange={(e) =>
                  updateTextProps({
                    font_size: parseInt(e.target.value) || 16,
                  })
                }
                className="w-16 border border-gray-200 rounded px-2 py-1 text-xs"
              />
              <input
                type="range"
                min="8"
                max="72"
                value={element.text_props.font_size}
                onChange={(e) =>
                  updateTextProps({ font_size: parseInt(e.target.value) })
                }
                className="flex-1"
              />
            </div>

            {/* Bold, Italic, Align */}
            <div className="flex items-center gap-1">
              <button
                onClick={() =>
                  updateTextProps({
                    font_weight:
                      element.text_props!.font_weight === "bold"
                        ? "normal"
                        : "bold",
                  })
                }
                className={cn(
                  "p-1.5 rounded",
                  element.text_props.font_weight === "bold"
                    ? "bg-blue-100 text-blue-600"
                    : "hover:bg-gray-100"
                )}
              >
                <Bold size={14} />
              </button>

              <div className="w-px h-5 bg-gray-200 mx-1" />

              {(["left", "center", "right"] as const).map((align) => {
                const Icon =
                  align === "left"
                    ? AlignLeft
                    : align === "center"
                      ? AlignCenter
                      : AlignRight;
                return (
                  <button
                    key={align}
                    onClick={() => updateTextProps({ align })}
                    className={cn(
                      "p-1.5 rounded",
                      element.text_props!.align === align
                        ? "bg-blue-100 text-blue-600"
                        : "hover:bg-gray-100"
                    )}
                  >
                    <Icon size={14} />
                  </button>
                );
              })}
            </div>

            {/* Color */}
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400">색상</span>
              <input
                type="color"
                value={
                  element.text_props.color.startsWith("#")
                    ? element.text_props.color
                    : "#1e293b"
                }
                onChange={(e) => updateTextProps({ color: e.target.value })}
                className="w-8 h-6 rounded border border-gray-200 cursor-pointer"
              />
              <input
                type="text"
                value={element.text_props.color}
                onChange={(e) => updateTextProps({ color: e.target.value })}
                className="flex-1 border border-gray-200 rounded px-2 py-1 text-xs"
              />
            </div>
          </div>
        </fieldset>
      )}

      {/* Image-specific */}
      {element.type === "image" && element.image_props && (
        <fieldset>
          <legend className="text-xs font-medium text-gray-500 mb-2">이미지</legend>
          <div className="space-y-2">
            <select
              value={element.image_props.fit}
              onChange={(e) =>
                updateField({
                  image_props: {
                    ...element.image_props!,
                    fit: e.target.value as "cover" | "contain" | "fill",
                  },
                })
              }
              className="w-full border border-gray-200 rounded px-2 py-1 text-xs"
            >
              <option value="cover">Cover</option>
              <option value="contain">Contain</option>
              <option value="fill">Fill</option>
            </select>

            <label className="flex items-center gap-2 text-xs">
              <span className="text-gray-400">모서리</span>
              <input
                type="number"
                min="0"
                value={element.image_props.border_radius ?? 0}
                onChange={(e) =>
                  updateField({
                    image_props: {
                      ...element.image_props!,
                      border_radius: parseInt(e.target.value) || 0,
                    },
                  })
                }
                className="w-16 border border-gray-200 rounded px-2 py-1"
              />
            </label>
          </div>
        </fieldset>
      )}

      {/* Shape-specific */}
      {element.type === "shape" && element.shape_props && (
        <fieldset>
          <legend className="text-xs font-medium text-gray-500 mb-2">도형</legend>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400">채우기</span>
              <input
                type="color"
                value={
                  element.shape_props.fill.startsWith("#")
                    ? element.shape_props.fill
                    : "#94a3b8"
                }
                onChange={(e) =>
                  updateField({
                    shape_props: {
                      ...element.shape_props!,
                      fill: e.target.value,
                    },
                  })
                }
                className="w-8 h-6 rounded border border-gray-200 cursor-pointer"
              />
            </div>

            <div className="flex items-center gap-2">
              <span className="text-[10px] text-gray-400">테두리</span>
              <input
                type="color"
                value={element.shape_props.stroke ?? "#000000"}
                onChange={(e) =>
                  updateField({
                    shape_props: {
                      ...element.shape_props!,
                      stroke: e.target.value,
                    },
                  })
                }
                className="w-8 h-6 rounded border border-gray-200 cursor-pointer"
              />
              <input
                type="number"
                min="0"
                max="20"
                value={element.shape_props.stroke_width ?? 0}
                onChange={(e) =>
                  updateField({
                    shape_props: {
                      ...element.shape_props!,
                      stroke_width: parseInt(e.target.value) || 0,
                    },
                  })
                }
                className="w-14 border border-gray-200 rounded px-2 py-1 text-xs"
              />
            </div>
          </div>
        </fieldset>
      )}
    </div>
  );
}

// ─── AI Assistant Panel ──────────────────────────────────────────────

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

function AIAssistantPanel() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);
  const updateSlide = usePresentationStore((s) => s.updateSlide);

  const handleSend = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;

    const slide = presentation?.slides[currentSlideIndex];
    if (!slide) return;

    const userMsg: ChatMessage = { role: "user", content: trimmed };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const result = await apiFetch<any>("/api/edit/refine-slide", {
        method: "POST",
        body: JSON.stringify({
          slide,
          instruction: trimmed,
        }),
      });

      updateSlide(currentSlideIndex, result);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "슬라이드를 수정했습니다.",
        },
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `오류: ${err.message}`,
        },
      ]);
    } finally {
      setIsLoading(false);
      setTimeout(() => {
        scrollRef.current?.scrollTo({
          top: scrollRef.current.scrollHeight,
          behavior: "smooth",
        });
      }, 50);
    }
  }, [input, isLoading, presentation, currentSlideIndex, updateSlide]);

  const suggestions = [
    "제목을 더 간결하게",
    "배경색을 더 밝게",
    "불릿 포인트 5개로 줄여줘",
    "톤을 격식체로 바꿔줘",
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto panel-scroll p-3 space-y-3">
        {messages.length === 0 && (
          <div className="text-center text-xs text-gray-400 mt-8 space-y-3">
            <Sparkles size={24} className="mx-auto opacity-40" />
            <p>AI에게 슬라이드 수정을 요청하세요</p>
            <div className="space-y-1.5">
              {suggestions.map((s) => (
                <button
                  key={s}
                  onClick={() => setInput(s)}
                  className="block w-full text-left px-3 py-1.5 text-xs bg-gray-50 rounded-lg hover:bg-gray-100 text-gray-600"
                >
                  &ldquo;{s}&rdquo;
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={cn(
              "text-xs rounded-lg px-3 py-2 max-w-[90%]",
              msg.role === "user"
                ? "ml-auto bg-blue-500 text-white"
                : "mr-auto bg-gray-100 text-gray-800"
            )}
          >
            {msg.content}
          </div>
        ))}

        {isLoading && (
          <div className="mr-auto bg-gray-100 text-gray-500 text-xs rounded-lg px-3 py-2 animate-pulse">
            수정 중...
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-2">
        <div className="flex items-center gap-1.5">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSend()}
            placeholder="수정 명령 입력..."
            className="flex-1 border border-gray-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-blue-400"
            disabled={isLoading}
          />
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="p-1.5 rounded-lg bg-blue-500 text-white disabled:opacity-40 hover:bg-blue-600"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Right Panel (tabs) ──────────────────────────────────────────────

export function RightPanel() {
  const tab = useUIStore((s) => s.rightPanelTab);
  const setTab = useUIStore((s) => s.setRightPanelTab);

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex border-b border-gray-200 flex-shrink-0">
        <button
          onClick={() => setTab("properties")}
          className={cn(
            "flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors",
            tab === "properties"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500 hover:text-gray-700"
          )}
        >
          <Settings2 size={14} />
          속성
        </button>
        <button
          onClick={() => setTab("ai")}
          className={cn(
            "flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-medium transition-colors",
            tab === "ai"
              ? "text-blue-600 border-b-2 border-blue-600"
              : "text-gray-500 hover:text-gray-700"
          )}
        >
          <Sparkles size={14} />
          AI 어시스턴트
        </button>
      </div>

      {/* Tab content */}
      <div className="flex-1 min-h-0 overflow-y-auto panel-scroll">
        {tab === "properties" ? <PropertyPanel /> : <AIAssistantPanel />}
      </div>
    </div>
  );
}
