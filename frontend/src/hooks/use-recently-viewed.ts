import { create } from 'zustand';

export interface RecentItem {
  id: string;
  type: 'evidence' | 'risk' | 'report' | 'control' | 'framework';
  title: string;
  subtitle: string;
  section: string; // navigation section to go to
  timestamp: number;
}

interface RecentlyViewedState {
  items: RecentItem[];
  addRecent: (item: Omit<RecentItem, 'timestamp'>) => void;
  clearRecent: () => void;
}

const MAX_ITEMS = 8;

export const useRecentlyViewedStore = create<RecentlyViewedState>((set) => ({
  items: [],
  addRecent: (item) =>
    set((state) => {
      // Remove duplicates (same id+type), then prepend, then cap at MAX_ITEMS
      const filtered = state.items.filter(
        (i) => !(i.id === item.id && i.type === item.type),
      );
      return {
        items: [{ ...item, timestamp: Date.now() }, ...filtered].slice(
          0,
          MAX_ITEMS,
        ),
      };
    }),
  clearRecent: () => set({ items: [] }),
}));
