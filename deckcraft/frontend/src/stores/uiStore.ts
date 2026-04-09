import { create } from "zustand";

interface UIState {
  leftPanelOpen: boolean;
  rightPanelOpen: boolean;
  rightPanelTab: "properties" | "ai";
  isGenerating: boolean;
  exportLoading: boolean;
}

interface UIActions {
  toggleLeftPanel: () => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: "properties" | "ai") => void;
  toggleAIPanel: () => void;
  setIsGenerating: (v: boolean) => void;
  setExportLoading: (v: boolean) => void;
}

export const useUIStore = create<UIState & UIActions>()((set) => ({
  leftPanelOpen: true,
  rightPanelOpen: true,
  rightPanelTab: "properties",
  isGenerating: false,
  exportLoading: false,

  toggleLeftPanel: () => set((s) => ({ leftPanelOpen: !s.leftPanelOpen })),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab, rightPanelOpen: true }),
  toggleAIPanel: () =>
    set((s) => ({
      rightPanelOpen: s.rightPanelTab === "ai" ? !s.rightPanelOpen : true,
      rightPanelTab: "ai",
    })),
  setIsGenerating: (v) => set({ isGenerating: v }),
  setExportLoading: (v) => set({ exportLoading: v }),
}));
