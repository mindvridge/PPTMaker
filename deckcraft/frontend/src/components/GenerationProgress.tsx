"use client";

import { cn } from "@/lib/cn";
import { Sparkles, Check, Loader2, Clock } from "lucide-react";

interface Step {
  label: string;
  status: "done" | "active" | "pending";
}

interface GenerationProgressProps {
  progress: number; // 0-1
  steps: Step[];
  title: string;
}

export function GenerationProgress({
  progress,
  steps,
  title,
}: GenerationProgressProps) {
  const pct = Math.round(progress * 100);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-8">
      <div className="max-w-lg w-full">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-blue-100 mb-4">
            <Sparkles size={28} className="text-blue-600 animate-pulse" />
          </div>
          <h2 className="text-xl font-semibold text-gray-800">
            프레젠테이션 생성 중...
          </h2>
          <p className="text-sm text-gray-500 mt-1">{title}</p>
        </div>

        {/* Progress bar */}
        <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-500">진행률</span>
            <span className="text-sm font-semibold text-blue-600">{pct}%</span>
          </div>
          <div className="h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        {/* Steps */}
        {steps.length > 0 && (
          <div className="mt-4 bg-white rounded-2xl border border-gray-200 p-4 shadow-sm max-h-[360px] overflow-y-auto panel-scroll">
            <div className="space-y-1">
              {steps.map((step, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-300",
                    step.status === "active" && "bg-blue-50",
                    step.status === "done" && "opacity-70"
                  )}
                >
                  {/* Icon */}
                  {step.status === "done" && (
                    <div className="w-5 h-5 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
                      <Check size={12} className="text-green-600" />
                    </div>
                  )}
                  {step.status === "active" && (
                    <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                      <Loader2
                        size={14}
                        className="text-blue-500 animate-spin"
                      />
                    </div>
                  )}
                  {step.status === "pending" && (
                    <div className="w-5 h-5 flex items-center justify-center flex-shrink-0">
                      <Clock size={12} className="text-gray-300" />
                    </div>
                  )}

                  {/* Label */}
                  <span
                    className={cn(
                      "text-sm",
                      step.status === "done" && "text-gray-500 line-through",
                      step.status === "active" &&
                        "text-blue-700 font-medium",
                      step.status === "pending" && "text-gray-400"
                    )}
                  >
                    {step.label}
                  </span>

                  {step.status === "active" && (
                    <span className="text-[10px] text-blue-400 ml-auto">
                      생성 중...
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Complete message */}
        {pct >= 100 && (
          <div className="mt-4 text-center text-sm text-green-600 font-medium animate-pulse">
            완료! 에디터로 이동합니다...
          </div>
        )}
      </div>
    </div>
  );
}
