import { create } from 'zustand';
import type { Report } from '@/lib/assurance/types';
import { reports as initialReports } from '@/lib/assurance/mock-data';

interface ReportsState {
  reports: Report[];
  setReports: (reports: Report[]) => void;
  addReport: (report: Report) => void;
  updateReport: (id: string, updates: Partial<Report>) => void;
  deleteReport: (id: string) => void;
}

export const useReportsStore = create<ReportsState>((set) => ({
  reports: initialReports,
  setReports: (reports) => set({ reports }),
  addReport: (report) =>
    set((state) => ({ reports: [report, ...state.reports] })),
  updateReport: (id, updates) =>
    set((state) => ({
      reports: state.reports.map((r) =>
        r.id === id ? { ...r, ...updates } : r
      ),
    })),
  deleteReport: (id) =>
    set((state) => ({
      reports: state.reports.filter((r) => r.id !== id),
    })),
}));
