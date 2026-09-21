import { create } from 'zustand';

export const DEFAULT_ENGAGEMENT_ID =
  process.env.NEXT_PUBLIC_M3_ENGAGEMENT_ID ?? 'ENG-2026-003';

interface EngagementState {
  engagementId: string;
  setEngagementId: (id: string) => void;
}

/**
 * Currently selected engagement. Persisted across section switches so the
 * whole dashboard reflects one engagement at a time.
 */
export const useEngagementStore = create<EngagementState>((set) => ({
  engagementId: DEFAULT_ENGAGEMENT_ID,
  setEngagementId: (engagementId) => set({ engagementId }),
}));