import { create } from "zustand";

interface EditorState {
  selectedElementId: string | null;
  zoom: number;
  isPanning: boolean;
  canvasReady: boolean;
}

interface EditorActions {
  selectElement: (id: string | null) => void;
  setZoom: (zoom: number) => void;
  zoomIn: () => void;
  zoomOut: () => void;
  setIsPanning: (v: boolean) => void;
  setCanvasReady: (v: boolean) => void;
}

export const useEditorStore = create<EditorState & EditorActions>()((set) => ({
  selectedElementId: null,
  zoom: 100,
  isPanning: false,
  canvasReady: false,

  selectElement: (id) => set({ selectedElementId: id }),
  setZoom: (zoom) => set({ zoom: Math.min(400, Math.max(25, zoom)) }),
  zoomIn: () => set((s) => ({ zoom: Math.min(400, s.zoom + 25) })),
  zoomOut: () => set((s) => ({ zoom: Math.max(25, s.zoom - 25) })),
  setIsPanning: (v) => set({ isPanning: v }),
  setCanvasReady: (v) => set({ canvasReady: v }),
}));
