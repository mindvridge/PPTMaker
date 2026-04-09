import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import type { Presentation, Slide, SlideElement } from "@/lib/slide-model";

interface HistoryEntry {
  presentation: Presentation;
}

interface PresentationState {
  presentation: Presentation | null;
  currentSlideIndex: number;
  // undo/redo
  history: HistoryEntry[];
  historyIndex: number;
}

interface PresentationActions {
  setPresentation: (p: Presentation) => void;
  updateSlide: (index: number, slide: Slide) => void;
  updateElement: (slideIndex: number, elementId: string, updates: Partial<SlideElement>) => void;
  addSlide: (slide: Slide, atIndex?: number) => void;
  removeSlide: (index: number) => void;
  reorderSlides: (fromIndex: number, toIndex: number) => void;
  setCurrentSlideIndex: (index: number) => void;
  setTitle: (title: string) => void;
  // undo/redo
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
}

const MAX_HISTORY = 50;

function pushHistory(state: PresentationState) {
  if (!state.presentation) return;
  const entry: HistoryEntry = {
    presentation: JSON.parse(JSON.stringify(state.presentation)),
  };
  // 현재 위치 이후의 히스토리 삭제 (새 분기)
  const newHistory = state.history.slice(0, state.historyIndex + 1);
  newHistory.push(entry);
  if (newHistory.length > MAX_HISTORY) {
    newHistory.shift();
  }
  state.history = newHistory;
  state.historyIndex = newHistory.length - 1;
}

export const usePresentationStore = create<PresentationState & PresentationActions>()(
  immer((set, get) => ({
    presentation: null,
    currentSlideIndex: 0,
    history: [],
    historyIndex: -1,

    setPresentation: (p) =>
      set((state) => {
        state.presentation = p;
        state.currentSlideIndex = 0;
        state.history = [{ presentation: JSON.parse(JSON.stringify(p)) }];
        state.historyIndex = 0;
      }),

    updateSlide: (index, slide) =>
      set((state) => {
        if (!state.presentation) return;
        pushHistory(state);
        state.presentation.slides[index] = slide;
      }),

    updateElement: (slideIndex, elementId, updates) =>
      set((state) => {
        if (!state.presentation) return;
        pushHistory(state);
        const slide = state.presentation.slides[slideIndex];
        if (!slide) return;
        const elemIdx = slide.elements.findIndex((e) => e.id === elementId);
        if (elemIdx === -1) return;
        Object.assign(slide.elements[elemIdx], updates);
      }),

    addSlide: (slide, atIndex) =>
      set((state) => {
        if (!state.presentation) return;
        pushHistory(state);
        const idx = atIndex ?? state.presentation.slides.length;
        state.presentation.slides.splice(idx, 0, slide);
        // order 재계산
        state.presentation.slides.forEach((s, i) => {
          s.order = i;
        });
        state.currentSlideIndex = idx;
      }),

    removeSlide: (index) =>
      set((state) => {
        if (!state.presentation || state.presentation.slides.length <= 1) return;
        pushHistory(state);
        state.presentation.slides.splice(index, 1);
        state.presentation.slides.forEach((s, i) => {
          s.order = i;
        });
        if (state.currentSlideIndex >= state.presentation.slides.length) {
          state.currentSlideIndex = state.presentation.slides.length - 1;
        }
      }),

    reorderSlides: (fromIndex, toIndex) =>
      set((state) => {
        if (!state.presentation) return;
        pushHistory(state);
        const [moved] = state.presentation.slides.splice(fromIndex, 1);
        state.presentation.slides.splice(toIndex, 0, moved);
        state.presentation.slides.forEach((s, i) => {
          s.order = i;
        });
      }),

    setCurrentSlideIndex: (index) =>
      set((state) => {
        state.currentSlideIndex = index;
      }),

    setTitle: (title) =>
      set((state) => {
        if (!state.presentation) return;
        pushHistory(state);
        state.presentation.title = title;
      }),

    undo: () =>
      set((state) => {
        if (state.historyIndex <= 0) return;
        state.historyIndex -= 1;
        const entry = state.history[state.historyIndex];
        state.presentation = JSON.parse(JSON.stringify(entry.presentation));
      }),

    redo: () =>
      set((state) => {
        if (state.historyIndex >= state.history.length - 1) return;
        state.historyIndex += 1;
        const entry = state.history[state.historyIndex];
        state.presentation = JSON.parse(JSON.stringify(entry.presentation));
      }),

    canUndo: () => get().historyIndex > 0,
    canRedo: () => get().historyIndex < get().history.length - 1,
  }))
);
