"use client";

import { useCallback, useEffect, useRef } from "react";
import { Canvas, FabricText, Rect, Circle, Triangle, FabricImage, Textbox } from "fabric";
import { usePresentationStore } from "@/stores/presentationStore";
import { useEditorStore } from "@/stores/editorStore";
import type { Slide, SlideElement, Background } from "@/lib/slide-model";

// ─── Constants ───────────────────────────────────────────────────────

const BASE_WIDTH = 1280;
const BASE_HEIGHT = 720;

// ─── Helpers: percent → pixel ────────────────────────────────────────

function pctToPx(pct: number, base: number) {
  return (pct / 100) * base;
}

// ─── Background ──────────────────────────────────────────────────────

function applyBackground(canvas: Canvas, bg: Background) {
  if (bg.type === "solid" && bg.color) {
    canvas.backgroundColor = bg.color;
  } else if (bg.type === "gradient" && bg.gradient) {
    const { from, to, direction } = bg.gradient;
    const rad = ((direction ?? 0) * Math.PI) / 180;
    const cos = Math.cos(rad);
    const sin = Math.sin(rad);
    canvas.backgroundColor = {
      type: "linear",
      coords: {
        x1: 0.5 - cos * 0.5,
        y1: 0.5 - sin * 0.5,
        x2: 0.5 + cos * 0.5,
        y2: 0.5 + sin * 0.5,
      },
      colorStops: [
        { offset: 0, color: from },
        { offset: 1, color: to },
      ],
      gradientUnits: "percentage",
    } as any;
  } else {
    canvas.backgroundColor = "#ffffff";
  }
}

// ─── Element → Fabric object ─────────────────────────────────────────

function elementToFabric(el: SlideElement): any {
  const left = pctToPx(el.position.x, BASE_WIDTH);
  const top = pctToPx(el.position.y, BASE_HEIGHT);
  const width = pctToPx(el.position.width, BASE_WIDTH);
  const height = pctToPx(el.position.height, BASE_HEIGHT);

  const common = {
    left,
    top,
    angle: el.rotation ?? 0,
    opacity: el.opacity ?? 1,
    data: { elementId: el.id, elementType: el.type },
  };

  if (el.type === "text" && el.text_props) {
    const tp = el.text_props;
    return new Textbox(tp.content, {
      ...common,
      width,
      fontSize: tp.font_size * 1.33, // pt → px approximate
      fontFamily: tp.font_family || "Pretendard",
      fontWeight: tp.font_weight === "bold" ? "bold" : "normal",
      fill: tp.color?.startsWith("#") ? tp.color : "#1e293b",
      textAlign: tp.align || "left",
      lineHeight: tp.line_height ?? 1.4,
      splitByGrapheme: true,
    });
  }

  if (el.type === "shape" && el.shape_props) {
    const sp = el.shape_props;
    const fill = sp.fill?.startsWith("#") ? sp.fill : "#94a3b8";
    const strokeColor = sp.stroke?.startsWith("#") ? sp.stroke : undefined;

    if (sp.shape_type === "circle") {
      return new Circle({
        ...common,
        radius: Math.min(width, height) / 2,
        fill,
        stroke: strokeColor,
        strokeWidth: sp.stroke_width ?? 0,
      });
    }
    if (sp.shape_type === "triangle") {
      return new Triangle({
        ...common,
        width,
        height,
        fill,
        stroke: strokeColor,
        strokeWidth: sp.stroke_width ?? 0,
      });
    }
    // default: rectangle
    return new Rect({
      ...common,
      width,
      height,
      fill,
      stroke: strokeColor,
      strokeWidth: sp.stroke_width ?? 0,
      rx: sp.border_radius ?? 0,
      ry: sp.border_radius ?? 0,
    });
  }

  if (el.type === "image" && el.image_props) {
    // Placeholder rect — actual image loading is async
    const placeholder = new Rect({
      ...common,
      width,
      height,
      fill: "#e2e8f0",
      stroke: "#cbd5e1",
      strokeWidth: 1,
      rx: el.image_props.border_radius ?? 0,
      ry: el.image_props.border_radius ?? 0,
    });

    if (el.image_props.src) {
      FabricImage.fromURL(el.image_props.src).then((img) => {
        if (img) {
          img.set({ ...common, scaleX: width / (img.width || 1), scaleY: height / (img.height || 1) });
          img.set("data", { elementId: el.id, elementType: "image" });
          const canvas = placeholder.canvas;
          if (canvas) {
            canvas.remove(placeholder);
            canvas.add(img);
            canvas.renderAll();
          }
        }
      }).catch(() => {});
    }
    return placeholder;
  }

  // Fallback: rect placeholder for chart/table/icon
  return new Rect({
    ...common,
    width,
    height,
    fill: "#f1f5f9",
    stroke: "#cbd5e1",
    strokeWidth: 1,
    rx: 4,
    ry: 4,
  });
}

// ─── Fabric → JSON (export) ──────────────────────────────────────────

function fabricToPosition(obj: any) {
  return {
    x: (obj.left / BASE_WIDTH) * 100,
    y: (obj.top / BASE_HEIGHT) * 100,
    width: ((obj.width * (obj.scaleX || 1)) / BASE_WIDTH) * 100,
    height: ((obj.height * (obj.scaleY || 1)) / BASE_HEIGHT) * 100,
  };
}

// ─── Component ───────────────────────────────────────────────────────

export function SlideCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const fabricRef = useRef<Canvas | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const syncingRef = useRef(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const presentation = usePresentationStore((s) => s.presentation);
  const currentSlideIndex = usePresentationStore((s) => s.currentSlideIndex);
  const updateSlide = usePresentationStore((s) => s.updateSlide);
  const zoom = useEditorStore((s) => s.zoom);
  const selectElement = useEditorStore((s) => s.selectElement);
  const setCanvasReady = useEditorStore((s) => s.setCanvasReady);
  const setZoom = useEditorStore((s) => s.setZoom);

  const currentSlide = presentation?.slides[currentSlideIndex] ?? null;

  // ── Init canvas ─────────────────────────────────────────────────

  useEffect(() => {
    if (!canvasRef.current || fabricRef.current) return;

    const canvas = new Canvas(canvasRef.current, {
      width: BASE_WIDTH,
      height: BASE_HEIGHT,
      selection: true,
      preserveObjectStacking: true,
      backgroundColor: "#ffffff",
    });

    fabricRef.current = canvas;
    setCanvasReady(true);

    return () => {
      canvas.dispose();
      fabricRef.current = null;
      setCanvasReady(false);
    };
  }, [setCanvasReady]);

  // ── Render slide when it changes ────────────────────────────────

  const renderSlide = useCallback(
    (slide: Slide) => {
      const canvas = fabricRef.current;
      if (!canvas) return;

      syncingRef.current = true;
      canvas.clear();
      applyBackground(canvas, slide.background);

      const sorted = [...slide.elements].sort((a, b) => a.z_index - b.z_index);
      for (const el of sorted) {
        const obj = elementToFabric(el);
        canvas.add(obj);
      }

      canvas.renderAll();
      syncingRef.current = false;
    },
    []
  );

  useEffect(() => {
    if (currentSlide) {
      renderSlide(currentSlide);
    }
  }, [currentSlide, renderSlide]);

  // ── Zoom ────────────────────────────────────────────────────────

  useEffect(() => {
    const container = containerRef.current;
    const el = canvasRef.current?.parentElement?.parentElement; // .canvas-container wrapper from fabric
    if (!container) return;

    const scale = zoom / 100;
    const wrapper = container.querySelector(".canvas-container") as HTMLElement;
    if (wrapper) {
      wrapper.style.transform = `scale(${scale})`;
      wrapper.style.transformOrigin = "center center";
    }
  }, [zoom]);

  // ── Ctrl+Wheel zoom ─────────────────────────────────────────────

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -10 : 10;
        setZoom(zoom + delta);
      }
    };

    container.addEventListener("wheel", handleWheel, { passive: false });
    return () => container.removeEventListener("wheel", handleWheel);
  }, [zoom, setZoom]);

  // ── Canvas events → sync back to store ──────────────────────────

  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    const debouncedSync = () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        if (syncingRef.current || !presentation) return;

        const slide = presentation.slides[currentSlideIndex];
        if (!slide) return;

        const updatedElements = slide.elements.map((el) => {
          const obj = canvas.getObjects().find(
            (o: any) => o.data?.elementId === el.id
          );
          if (!obj) return el;

          const pos = fabricToPosition(obj);
          const updates: any = {
            ...el,
            position: pos,
            rotation: obj.angle ?? 0,
            opacity: obj.opacity ?? 1,
          };

          if (el.type === "text" && el.text_props && obj instanceof Textbox) {
            updates.text_props = {
              ...el.text_props,
              content: obj.text || el.text_props.content,
            };
          }

          return updates;
        });

        updateSlide(currentSlideIndex, { ...slide, elements: updatedElements });
      }, 300);
    };

    const handleSelection = (e: any) => {
      const obj = canvas.getActiveObject();
      if (obj?.data?.elementId) {
        selectElement(obj.data.elementId);
      }
    };

    const handleDeselect = () => selectElement(null);

    canvas.on("object:modified", debouncedSync);
    canvas.on("text:changed", debouncedSync);
    canvas.on("selection:created", handleSelection);
    canvas.on("selection:updated", handleSelection);
    canvas.on("selection:cleared", handleDeselect);

    return () => {
      canvas.off("object:modified", debouncedSync);
      canvas.off("text:changed", debouncedSync);
      canvas.off("selection:created", handleSelection);
      canvas.off("selection:updated", handleSelection);
      canvas.off("selection:cleared", handleDeselect);
    };
  }, [presentation, currentSlideIndex, selectElement, updateSlide]);

  // ── Keyboard shortcuts ──────────────────────────────────────────

  useEffect(() => {
    const canvas = fabricRef.current;
    if (!canvas) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Delete selected element
      if (e.key === "Delete" || e.key === "Backspace") {
        if (document.activeElement?.tagName === "INPUT" || document.activeElement?.tagName === "TEXTAREA") return;
        const active = canvas.getActiveObject();
        if (active && !(active instanceof Textbox && (active as any).isEditing)) {
          canvas.remove(active);
          canvas.renderAll();
          selectElement(null);
        }
      }

      // Ctrl+Z / Ctrl+Y
      if ((e.ctrlKey || e.metaKey) && e.key === "z") {
        e.preventDefault();
        usePresentationStore.getState().undo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === "y") {
        e.preventDefault();
        usePresentationStore.getState().redo();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [selectElement]);

  return (
    <div
      ref={containerRef}
      className="flex-1 flex items-center justify-center bg-slate-200 overflow-hidden p-4"
    >
      <div
        className="shadow-xl"
        style={{
          transform: `scale(${zoom / 100})`,
          transformOrigin: "center center",
        }}
      >
        <canvas ref={canvasRef} />
      </div>
    </div>
  );
}
