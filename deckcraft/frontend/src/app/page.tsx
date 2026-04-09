"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles,
  Upload,
  FileText,
  Link2,
  ChevronDown,
  Loader2,
} from "lucide-react";
import { GenerationProgress } from "@/components/GenerationProgress";
import { usePresentationStore } from "@/stores/presentationStore";
import { apiStream } from "@/lib/api";
import { cn } from "@/lib/cn";

const STYLE_OPTIONS = [
  { value: "modern_minimal", label: "모던", emoji: "✨" },
  { value: "corporate", label: "기업용", emoji: "💼" },
  { value: "creative", label: "크리에이티브", emoji: "🎨" },
  { value: "academic", label: "학술", emoji: "📚" },
];

const SLIDE_COUNTS = [5, 8, 10, 12, 15, 20];

export default function Home() {
  const router = useRouter();
  const setPresentation = usePresentationStore((s) => s.setPresentation);

  const [topic, setTopic] = useState("");
  const [style, setStyle] = useState("modern_minimal");
  const [slideCount, setSlideCount] = useState(10);
  const [language, setLanguage] = useState<"ko" | "en">("ko");

  // Generation state
  const [phase, setPhase] = useState<"idle" | "planning" | "review">("idle");
  const [planTokens, setPlanTokens] = useState("");
  const [plan, setPlan] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Generate plan via SSE ─────────────────────────────────────

  const handleGenerate = async () => {
    if (!topic.trim()) return;
    setPhase("planning");
    setError(null);
    setPlanTokens("");

    try {
      await apiStream(
        "/api/generate/plan",
        {
          topic: topic.trim(),
          style,
          slide_count: slideCount,
          language,
        },
        (event, data) => {
          if (event === "token") {
            setPlanTokens((prev) => prev + data.content);
          } else if (event === "complete") {
            setPlan(data.plan);
            setPhase("review");
          } else if (event === "error") {
            setError(data.message);
            setPhase("idle");
          }
        },
        () => {
          // If no complete event was received, try parsing collected tokens
          if (phase === "planning") {
            setPhase("idle");
          }
        }
      );
    } catch (err: any) {
      setError(err.message);
      setPhase("idle");
    }
  };

  // ── File upload ───────────────────────────────────────────────

  const handleFileUpload = async (file: File) => {
    setPhase("planning");
    setError(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("language", language);
    formData.append("style", style);
    formData.append("slide_count", String(slideCount));

    try {
      const API_BASE =
        process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res = await fetch(`${API_BASE}/api/generate/from-document`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
      const data = await res.json();
      setPlan(data);
      setPhase("review");
    } catch (err: any) {
      setError(err.message);
      setPhase("idle");
    }
  };

  // ── Review → redirect ─────────────────────────────────────────

  if (phase === "review" && plan) {
    router.push("/generate/review");
    // Store plan in sessionStorage for the review page
    if (typeof window !== "undefined") {
      sessionStorage.setItem("deckcraft_plan", JSON.stringify(plan));
    }
  }

  // ── Planning phase: show progress ─────────────────────────────

  if (phase === "planning") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-blue-50 p-8">
        <div className="max-w-lg w-full text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-500 mx-auto mb-6" />
          <h2 className="text-xl font-semibold text-gray-800 mb-2">
            프레젠테이션 계획 생성 중...
          </h2>
          <p className="text-sm text-gray-500 mb-6">
            AI가 주제를 분석하고 슬라이드 구조를 설계하고 있습니다
          </p>

          {planTokens && (
            <div className="bg-white rounded-xl border border-gray-200 p-4 text-left text-xs text-gray-600 font-mono max-h-64 overflow-y-auto">
              {planTokens.slice(0, 500)}
              {planTokens.length > 500 && "..."}
            </div>
          )}
        </div>
      </div>
    );
  }

  // ── Idle: landing page ────────────────────────────────────────

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex flex-col">
      {/* Main content */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 py-12">
        {/* Logo */}
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            <span className="text-blue-600">Deck</span>Craft
          </h1>
          <p className="text-lg text-gray-500">
            AI가 만드는 프로페셔널 프레젠테이션
          </p>
        </div>

        {/* Input area */}
        <div className="w-full max-w-2xl">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6 space-y-5">
            {/* Topic textarea */}
            <div>
              <textarea
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                placeholder='어떤 프레젠테이션을 만들까요?&#10;&#10;예: "AI 스타트업 투자 유치 피칭 덱, 모던하고 깔끔한 디자인으로 만들어줘"'
                rows={4}
                className="w-full resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent placeholder:text-gray-400"
              />
            </div>

            {/* Options row */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Style */}
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-gray-500">스타일:</span>
                <div className="flex gap-1">
                  {STYLE_OPTIONS.map((opt) => (
                    <button
                      key={opt.value}
                      onClick={() => setStyle(opt.value)}
                      className={cn(
                        "px-2.5 py-1 text-xs rounded-full border transition-all",
                        style === opt.value
                          ? "border-blue-400 bg-blue-50 text-blue-700"
                          : "border-gray-200 text-gray-600 hover:border-gray-300"
                      )}
                    >
                      {opt.emoji} {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div className="w-px h-5 bg-gray-200" />

              {/* Slide count */}
              <label className="flex items-center gap-1.5 text-xs text-gray-500">
                슬라이드:
                <select
                  value={slideCount}
                  onChange={(e) => setSlideCount(Number(e.target.value))}
                  className="border border-gray-200 rounded-lg px-2 py-1 text-xs"
                >
                  {SLIDE_COUNTS.map((n) => (
                    <option key={n} value={n}>
                      {n}장
                    </option>
                  ))}
                </select>
              </label>

              {/* Language */}
              <label className="flex items-center gap-1.5 text-xs text-gray-500">
                언어:
                <select
                  value={language}
                  onChange={(e) =>
                    setLanguage(e.target.value as "ko" | "en")
                  }
                  className="border border-gray-200 rounded-lg px-2 py-1 text-xs"
                >
                  <option value="ko">한국어</option>
                  <option value="en">English</option>
                </select>
              </label>
            </div>

            {/* Generate button */}
            <button
              onClick={handleGenerate}
              disabled={!topic.trim()}
              className="w-full py-3 bg-blue-600 text-white rounded-xl font-medium text-sm hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              <Sparkles size={18} />
              PPT 생성하기
            </button>

            {error && (
              <p className="text-xs text-red-500 text-center">{error}</p>
            )}
          </div>

          {/* File upload */}
          <div className="mt-4 flex items-center justify-center gap-3">
            <span className="text-xs text-gray-400">또는 파일 업로드:</span>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt,.md"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFileUpload(file);
              }}
              className="hidden"
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs border border-gray-200 rounded-lg hover:bg-white transition-colors text-gray-600"
            >
              <Upload size={14} />
              PDF / DOCX / TXT
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center py-4 text-xs text-gray-400">
        DeckCraft &mdash; AI 프레젠테이션 생성 서비스
      </footer>
    </div>
  );
}
