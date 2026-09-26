import { create } from 'zustand';
import type { SectionId } from '@/lib/assurance/types';

interface NavigationState {
  activeSection: SectionId;
  setActiveSection: (section: SectionId) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  showNotifications: boolean;
  setShowNotifications: (show: boolean) => void;
  showSearch: boolean;
  setShowSearch: (show: boolean) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  activeSection: 'dashboard',
  setActiveSection: (section) => set({ activeSection: section }),
  searchQuery: '',
  setSearchQuery: (query) => set({ searchQuery: query }),
  showNotifications: false,
  setShowNotifications: (show) => set({ showNotifications: show }),
  showSearch: false,
  setShowSearch: (show) => set({ showSearch: show }),
}));
