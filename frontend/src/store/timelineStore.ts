import { create } from "zustand";

export type RiskLevel = "low" | "medium" | "high" | "critical";

interface TimelineState {
  selectedDate: string;
  isPlaying: boolean;
  riskLevels: RiskLevel[];
  setSelectedDate: (date: string) => void;
  togglePlayback: () => void;
  toggleRiskLevel: (level: RiskLevel) => void;
}

const today = new Date().toISOString().slice(0, 10);

export const useTimelineStore = create<TimelineState>((set) => ({
  selectedDate: today,
  isPlaying: false,
  riskLevels: ["low", "medium", "high", "critical"],
  setSelectedDate: (selectedDate) => set({ selectedDate }),
  togglePlayback: () => set((state) => ({ isPlaying: !state.isPlaying })),
  toggleRiskLevel: (level) =>
    set((state) => ({
      riskLevels: state.riskLevels.includes(level)
        ? state.riskLevels.filter((entry) => entry !== level)
        : [...state.riskLevels, level]
    }))
}));
