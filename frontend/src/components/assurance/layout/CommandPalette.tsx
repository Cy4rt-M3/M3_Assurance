'use client';

import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search,
  X,
  CornerDownLeft,
  ArrowUp,
  ArrowDown,
  LayoutDashboard,
  Shield,
  FileCheck,
  AlertTriangle,
  FileText,
  Bell,
  ScrollText,
  Settings,
  FilePlus2,
  AlertCircle,
  Download,
  Database,
  Clock,
  Target,
  CheckSquare,
} from 'lucide-react';
import { useNavigationStore } from '@/hooks/use-navigation';
import { useRecentlyViewedStore, type RecentItem } from '@/hooks/use-recently-viewed';
import { frameworks, evidenceItems, risks, reports } from '@/lib/assurance/mock-data';
import type { SectionId } from '@/lib/assurance/types';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

type CategoryKey =
  | 'recent'
  | 'navigation'
  | 'actions'
  | 'frameworks'
  | 'evidence'
  | 'risks'
  | 'reports';

interface CommandItem {
  id: string;
  title: string;
  subtitle?: string;
  icon: React.ComponentType<{ className?: string }>;
  category: CategoryKey;
  section: SectionId;
  keywords?: string;
  recentType?: RecentItem['type'];
  timestamp?: number;
}

const categoryLabels: Record<CategoryKey, string> = {
  recent: 'Recently Viewed',
  navigation: 'Navigation',
  actions: 'Quick Actions',
  frameworks: 'Frameworks',
  evidence: 'Evidence',
  risks: 'Risks',
  reports: 'Reports',
};

const categoryOrder: CategoryKey[] = [
  'recent',
  'navigation',
  'actions',
  'frameworks',
  'evidence',
  'risks',
  'reports',
];

// Limit per category for evidence/risks/reports
const categoryLimits: Partial<Record<CategoryKey, number>> = {
  evidence: 5,
  risks: 5,
  reports: 5,
};

// ---------- Static items ----------
const navigationItems: CommandItem[] = [
  {
    id: 'nav-dashboard',
    title: 'Dashboard',
    subtitle: 'Compliance overview & KPIs',
    icon: LayoutDashboard,
    category: 'navigation',
    section: 'dashboard',
  },
  {
    id: 'nav-frameworks',
    title: 'Framework Setup',
    subtitle: 'Manage compliance frameworks & controls',
    icon: Shield,
    category: 'navigation',
    section: 'frameworks',
  },
  {
    id: 'nav-evidence',
    title: 'Evidence Aggregator',
    subtitle: 'Collect, validate & map evidence',
    icon: FileCheck,
    category: 'navigation',
    section: 'evidence',
  },
  {
    id: 'nav-risk',
    title: 'Risk & Resilience',
    subtitle: 'Risk scoring, resilience & gap analysis',
    icon: AlertTriangle,
    category: 'navigation',
    section: 'risk',
  },
  {
    id: 'nav-reports',
    title: 'Report Generation',
    subtitle: 'Build, schedule & export compliance reports',
    icon: FileText,
    category: 'navigation',
    section: 'reports',
  },
  {
    id: 'nav-tasks',
    title: 'Task Management',
    subtitle: 'Assign & track GRC tasks, remediation & approvals',
    icon: CheckSquare,
    category: 'navigation',
    section: 'tasks',
  },
  {
    id: 'nav-notifications',
    title: 'Notifications',
    subtitle: 'Alerts & system messages',
    icon: Bell,
    category: 'navigation',
    section: 'notifications',
  },
  {
    id: 'nav-audit-logs',
    title: 'Audit Logs',
    subtitle: 'Immutable audit trail & hash chain',
    icon: ScrollText,
    category: 'navigation',
    section: 'audit-logs',
  },
  {
    id: 'nav-settings',
    title: 'Settings',
    subtitle: 'Workspace, integrations & security',
    icon: Settings,
    category: 'navigation',
    section: 'settings',
  },
];

const quickActions: CommandItem[] = [
  {
    id: 'action-new-report',
    title: 'Generate New Report',
    subtitle: 'Open the 8-step report builder wizard',
    icon: FilePlus2,
    category: 'actions',
    section: 'reports',
  },
  {
    id: 'action-missing-evidence',
    title: 'View Missing Evidence',
    subtitle: 'See evidence requiring remediation',
    icon: AlertCircle,
    category: 'actions',
    section: 'evidence',
  },
  {
    id: 'action-export-audit',
    title: 'Export Audit Log',
    subtitle: 'Download the immutable audit trail',
    icon: Download,
    category: 'actions',
    section: 'audit-logs',
  },
];

// ---------- Dynamic items from mock data ----------
const frameworkItems: CommandItem[] = frameworks.map((f) => ({
  id: `fw-${f.id}`,
  title: `${f.name} ${f.version}`,
  subtitle: `${f.description} • ${f.compliance}% compliant`,
  icon: Shield,
  category: 'frameworks',
  section: 'frameworks',
  keywords: `${f.name} ${f.version} ${f.description}`,
}));

const evidenceCommandItems: CommandItem[] = evidenceItems.map((e) => ({
  id: `evd-${e.id}`,
  title: e.id,
  subtitle: `${e.asset} • ${e.controlRef} • ${e.framework}`,
  icon: Database,
  category: 'evidence',
  section: 'evidence',
  keywords: `${e.id} ${e.asset} ${e.controlRef} ${e.framework} ${e.description}`,
}));

const riskCommandItems: CommandItem[] = risks.map((r) => ({
  id: `risk-${r.id}`,
  title: `${r.id} — ${r.title}`,
  subtitle: `${r.framework} • ${r.severity} severity • ${r.status}`,
  icon: AlertTriangle,
  category: 'risks',
  section: 'risk',
  keywords: `${r.id} ${r.title} ${r.framework} ${r.description}`,
}));

const reportCommandItems: CommandItem[] = reports.map((r) => ({
  id: `rpt-${r.id}`,
  title: r.title,
  subtitle: `${r.id} • ${r.framework} • ${r.type}`,
  icon: FileText,
  category: 'reports',
  section: 'reports',
  keywords: `${r.id} ${r.title} ${r.framework} ${r.type}`,
}));

const allItems: CommandItem[] = [
  ...navigationItems,
  ...quickActions,
  ...frameworkItems,
  ...evidenceCommandItems,
  ...riskCommandItems,
  ...reportCommandItems,
];

// ---------- Recently viewed helpers ----------
function getRecentIcon(
  type: RecentItem['type'],
): React.ComponentType<{ className?: string }> {
  switch (type) {
    case 'evidence':
      return FileCheck;
    case 'risk':
      return AlertTriangle;
    case 'report':
      return FileText;
    case 'control':
      return Target;
    case 'framework':
      return Shield;
  }
}

function getRecentBadgeClasses(type: RecentItem['type']): string {
  switch (type) {
    case 'evidence':
      return 'bg-success/15 text-success border-transparent';
    case 'risk':
      return 'bg-danger/15 text-danger border-transparent';
    case 'report':
      return 'bg-primary/15 text-primary border-transparent';
    case 'control':
      return 'bg-cyber/15 text-cyber border-transparent';
    case 'framework':
      return 'bg-purple-500/15 text-purple-400 border-transparent';
  }
}

function formatRelativeTime(ts: number): string {
  const seconds = Math.floor((Date.now() - ts) / 1000);
  if (seconds < 45) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `${weeks}w ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
}

function recentItemToCommandItem(item: RecentItem): CommandItem {
  return {
    id: `recent-${item.type}-${item.id}`,
    title: item.title,
    subtitle: item.subtitle,
    icon: getRecentIcon(item.type),
    category: 'recent',
    section: item.section as SectionId,
    recentType: item.type,
    timestamp: item.timestamp,
  };
}

/**
 * Top-level palette. Always mounted in the layout; listens for the global
 * Cmd+K / Ctrl+K shortcut to toggle visibility and renders the overlay via
 * AnimatePresence. The inner content is a separate component so that local
 * state (query, active index) is fresh on every open.
 */
export function CommandPalette() {
  const { showSearch, setShowSearch } = useNavigationStore();

  // Global Cmd+K / Ctrl+K toggle. This is the single source of truth for the
  // keyboard shortcut — AppHeader only opens via click to avoid double-firing.
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setShowSearch(!showSearch);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showSearch, setShowSearch]);

  const handleClose = useCallback(() => {
    setShowSearch(false);
  }, [setShowSearch]);

  return (
    <AnimatePresence>
      {showSearch && <CommandPaletteContent onClose={handleClose} />}
    </AnimatePresence>
  );
}

interface CommandPaletteContentProps {
  onClose: () => void;
}

function CommandPaletteContent({ onClose }: CommandPaletteContentProps) {
  const { setActiveSection, setSearchQuery } = useNavigationStore();
  const recentItems = useRecentlyViewedStore((s) => s.items);
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const itemRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Focus input + lock body scroll on mount; restore on unmount.
  useEffect(() => {
    const id = requestAnimationFrame(() => {
      inputRef.current?.focus();
      inputRef.current?.select();
    });
    const prevOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      cancelAnimationFrame(id);
      document.body.style.overflow = prevOverflow;
    };
  }, []);

  // Filter items by query
  const filteredItems = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return allItems;
    return allItems.filter((item) => {
      const haystack =
        `${item.title} ${item.subtitle ?? ''} ${item.keywords ?? ''}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [query]);

  // Convert recently viewed items to command items — only visible when not searching.
  const recentCommandItems = useMemo(
    () => (query.trim() ? [] : recentItems.map(recentItemToCommandItem)),
    [recentItems, query],
  );

  // Group + limit per category (preserving categoryOrder). The recent group is
  // prepended at the top when there are recent items and the user isn't searching.
  const groupedItems = useMemo(() => {
    const groups: { category: CategoryKey; items: CommandItem[] }[] = [];
    if (recentCommandItems.length > 0) {
      groups.push({ category: 'recent', items: recentCommandItems });
    }
    for (const cat of categoryOrder) {
      if (cat === 'recent') continue;
      const items = filteredItems.filter((i) => i.category === cat);
      if (items.length === 0) continue;
      const limit = categoryLimits[cat];
      groups.push({
        category: cat,
        items: limit ? items.slice(0, limit) : items,
      });
    }
    return groups;
  }, [filteredItems, recentCommandItems]);

  // Flat list of visible items (after grouping & limiting) — order matches DOM
  const flatItems = useMemo(
    () => groupedItems.flatMap((g) => g.items),
    [groupedItems],
  );

  // Clamp active index whenever the result set changes (no setState in effect —
  // we read the clamped value inline via safeActiveIndex).
  const safeActiveIndex =
    flatItems.length === 0 ? 0 : Math.min(activeIndex, flatItems.length - 1);

  // Keep active item in view during keyboard nav
  useEffect(() => {
    const el = itemRefs.current[safeActiveIndex];
    if (el) {
      el.scrollIntoView({ block: 'nearest' });
    }
  }, [safeActiveIndex]);

  const handleSelect = useCallback(
    (item: CommandItem) => {
      setActiveSection(item.section);
      setSearchQuery(query);
      onClose();
    },
    [setActiveSection, setSearchQuery, query, onClose],
  );

  // Reset active index whenever the user types. Done in the change handler
  // (not an effect) so it doesn't trigger cascading renders.
  const handleQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
    setActiveIndex(0);
  };

  // Keyboard navigation inside palette
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      e.preventDefault();
      onClose();
      return;
    }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (flatItems.length === 0) return;
      setActiveIndex((i) => (i + 1) % flatItems.length);
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (flatItems.length === 0) return;
      setActiveIndex((i) => (i - 1 + flatItems.length) % flatItems.length);
      return;
    }
    if (e.key === 'Enter') {
      e.preventDefault();
      const item = flatItems[safeActiveIndex];
      if (item) handleSelect(item);
      return;
    }
    if (e.key === 'Home') {
      e.preventDefault();
      setActiveIndex(0);
      return;
    }
    if (e.key === 'End') {
      e.preventDefault();
      setActiveIndex(Math.max(0, flatItems.length - 1));
      return;
    }
  };

  // Close when clicking the overlay backdrop (not the panel)
  const handleOverlayMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  // Helper to find flat index for an item id
  const flatIndexById = (id: string) =>
    flatItems.findIndex((fi) => fi.id === id);

  return (
    <motion.div
      className="fixed inset-0 z-[100] flex items-start justify-center px-4 pt-[10vh] sm:pt-[12vh]"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.15 }}
      onMouseDown={handleOverlayMouseDown}
      role="presentation"
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" aria-hidden />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, scale: 0.97, y: -8 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.97, y: -8 }}
        transition={{ duration: 0.18, ease: 'easeOut' }}
        className="relative flex max-h-[80vh] w-full max-w-[640px] flex-col overflow-hidden rounded-xl border border-border bg-card/95 shadow-2xl backdrop-blur-xl"
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
      >
        {/* Search input row */}
        <div className="flex items-center gap-3 border-b border-border px-4">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={handleQueryChange}
            onKeyDown={handleKeyDown}
            placeholder="Search or jump to..."
            className="flex-1 bg-transparent py-4 text-sm text-foreground outline-none placeholder:text-muted-foreground"
            autoComplete="off"
            spellCheck={false}
            aria-label="Search commands"
            aria-autocomplete="list"
            aria-controls="command-palette-list"
            aria-activedescendant={
              flatItems[safeActiveIndex]
                ? `cmd-item-${flatItems[safeActiveIndex].id}`
                : undefined
            }
          />
          <button
            type="button"
            onClick={onClose}
            className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-accent/50 hover:text-foreground"
            aria-label="Close command palette"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Results */}
        <div
          id="command-palette-list"
          role="listbox"
          className="min-h-0 flex-1 overflow-y-auto p-2"
        >
          {flatItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-2 px-4 py-12 text-center">
              <Search className="h-6 w-6 text-muted-foreground/40" />
              <p className="text-sm text-muted-foreground">
                No results found
                {query.trim() && (
                  <>
                    {' '}
                    for{' '}
                    <span className="font-medium text-foreground">
                      &ldquo;{query}&rdquo;
                    </span>
                  </>
                )}
              </p>
            </div>
          ) : (
            groupedItems.map((group) => {
              const isRecent = group.category === 'recent';
              return (
                <div key={group.category} className="mb-1 last:mb-0">
                  <div className="flex items-center gap-1.5 px-3 py-1.5 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/80">
                    {isRecent && <Clock className="h-3 w-3" />}
                    {categoryLabels[group.category]}
                  </div>
                  {group.items.map((item) => {
                    const flatIdx = flatIndexById(item.id);
                    const isActive = flatIdx === safeActiveIndex;
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.id}
                        id={`cmd-item-${item.id}`}
                        ref={(el) => {
                          itemRefs.current[flatIdx] = el;
                        }}
                        type="button"
                        role="option"
                        aria-selected={isActive}
                        onMouseEnter={() => setActiveIndex(flatIdx)}
                        onClick={() => handleSelect(item)}
                        className={cn(
                          'flex w-full items-center gap-3 rounded-lg border-l-2 px-3 py-2 text-left transition-colors',
                          isActive
                            ? 'border-primary bg-primary/15'
                            : 'border-transparent hover:bg-accent/40',
                        )}
                      >
                        <Icon
                          className={cn(
                            'h-4 w-4 shrink-0',
                            isActive ? 'text-primary' : 'text-muted-foreground',
                          )}
                        />
                        <div className="min-w-0 flex-1">
                          <div
                            className={cn(
                              'truncate text-sm',
                              isActive
                                ? 'font-medium text-foreground'
                                : 'text-foreground/90',
                            )}
                          >
                            {item.title}
                          </div>
                          {item.subtitle && (
                            <div className="truncate text-xs text-muted-foreground">
                              {item.subtitle}
                              {isRecent && item.timestamp && (
                                <>
                                  <span className="mx-1 text-muted-foreground/50">
                                    ·
                                  </span>
                                  <span className="text-muted-foreground/70">
                                    {formatRelativeTime(item.timestamp)}
                                  </span>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                        {isRecent && item.recentType ? (
                          <div className="flex shrink-0 items-center gap-1.5">
                            <Clock className="h-3 w-3 text-muted-foreground/60" />
                            <Badge
                              className={cn(
                                'shrink-0 text-[10px] font-medium uppercase tracking-wide',
                                getRecentBadgeClasses(item.recentType),
                              )}
                            >
                              {item.recentType}
                            </Badge>
                          </div>
                        ) : (
                          <Badge
                            variant="outline"
                            className="shrink-0 border-border bg-background/50 text-[10px] font-medium uppercase tracking-wide text-muted-foreground"
                          >
                            {categoryLabels[group.category]}
                          </Badge>
                        )}
                      </button>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* Footer keyboard hints */}
        <div className="flex items-center justify-between gap-2 border-t border-border bg-background/40 px-4 py-2.5 text-[11px] text-muted-foreground">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
            <span className="flex items-center gap-1.5">
              <kbd className="inline-flex h-5 items-center justify-center rounded border border-border bg-muted px-1 font-mono text-[10px]">
                <ArrowUp className="h-3 w-3" />
              </kbd>
              <kbd className="inline-flex h-5 items-center justify-center rounded border border-border bg-muted px-1 font-mono text-[10px]">
                <ArrowDown className="h-3 w-3" />
              </kbd>
              <span>navigate</span>
            </span>
            <span className="flex items-center gap-1.5">
              <kbd className="inline-flex h-5 items-center justify-center rounded border border-border bg-muted px-1 font-mono text-[10px]">
                <CornerDownLeft className="h-3 w-3" />
              </kbd>
              <span>select</span>
            </span>
            <span className="flex items-center gap-1.5">
              <kbd className="inline-flex h-5 items-center justify-center rounded border border-border bg-muted px-1.5 font-mono text-[10px]">
                esc
              </kbd>
              <span>close</span>
            </span>
          </div>
          <span className="hidden text-muted-foreground/60 sm:inline">
            CyBreach Assurance
          </span>
        </div>
      </motion.div>
    </motion.div>
  );
}

export default CommandPalette;
