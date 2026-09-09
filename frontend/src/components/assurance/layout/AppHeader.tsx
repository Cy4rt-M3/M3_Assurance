'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Search, Sun, Moon, LogOut, User, Settings } from 'lucide-react';
import { useTheme } from 'next-themes';
import type { SectionId } from '@/lib/assurance/types';
import { useNavigationStore } from '@/hooks/use-navigation';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Separator } from '@/components/ui/separator';
import { RoleSwitcher } from './RoleSwitcher';
import { NotificationsDropdown } from './NotificationsDropdown';

const sectionLabels: Record<SectionId, string> = {
  dashboard: 'Dashboard',
  frameworks: 'Framework Setup',
  evidence: 'Evidence Aggregator',
  risk: 'Risk & Resilience',
  reports: 'Report Generation',
  tasks: 'Task Management',
  notifications: 'Notifications',
  'audit-logs': 'Audit Logs',
  settings: 'Settings',
};

const sectionParents: Partial<Record<SectionId, string>> = {
  frameworks: 'Compliance',
  evidence: 'Compliance',
  risk: 'Compliance',
  reports: 'Compliance',
  tasks: 'Compliance',
  notifications: 'System',
  'audit-logs': 'System',
  settings: 'System',
};

interface AppHeaderProps {
  activeSection: SectionId;
  notificationCount: number;
}

export function AppHeader({
  activeSection,
  notificationCount,
}: AppHeaderProps) {
  const { theme, setTheme } = useTheme();
  const { setShowSearch } = useNavigationStore();
  const mountedRef = useRef(false);
  const [mounted, setMounted] = useState(false);

  // Use requestAnimationFrame to avoid synchronous setState in effect
  useEffect(() => {
    if (!mountedRef.current) {
      mountedRef.current = true;
      requestAnimationFrame(() => {
        setMounted(true);
      });
    }
  }, []);

  // Note: Cmd+K / Ctrl+K shortcut is handled by the CommandPalette component
  // to avoid double-firing. The header only opens via click.

  const openSearch = () => setShowSearch(true);

  return (
    <header className="flex h-14 shrink-0 items-center gap-3 border-b border-border bg-background/80 backdrop-blur-sm px-4">
      {/* Left: Sidebar trigger + Breadcrumb */}
      <div className="flex items-center gap-3">
        <SidebarTrigger className="-ml-1 hover:bg-accent/50" />
        <Separator orientation="vertical" className="h-5" />
        <Breadcrumb>
          <BreadcrumbList>
            <BreadcrumbItem>
              <span className="text-xs text-muted-foreground font-medium">CyBreach</span>
            </BreadcrumbItem>
            {sectionParents[activeSection] && (
              <>
                <BreadcrumbSeparator />
                <BreadcrumbItem>
                  <span className="text-xs text-muted-foreground">
                    {sectionParents[activeSection]}
                  </span>
                </BreadcrumbItem>
              </>
            )}
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className="text-xs font-medium text-foreground">
                {sectionLabels[activeSection]}
              </BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      {/* Center: Global Search Trigger */}
      <div className="flex-1 flex justify-center max-w-md mx-auto">
        <button
          type="button"
          onClick={openSearch}
          aria-label="Open command palette"
          className="group relative flex h-8 w-full items-center gap-2 rounded-md border border-border bg-card px-2.5 text-xs text-muted-foreground/70 transition-colors hover:border-primary/40 hover:bg-accent/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
        >
          <Search className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
          <span className="truncate">Search or jump to...</span>
          <kbd className="pointer-events-none ml-auto inline-flex h-5 select-none items-center gap-0.5 rounded border border-border bg-muted px-1.5 font-mono text-[10px] font-medium text-muted-foreground">
            <span className="text-[9px]">⌘</span>K
          </kbd>
        </button>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-1.5">
        {/* Notifications Dropdown */}
        <NotificationsDropdown notificationCount={notificationCount} />

        {/* Theme Toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8 hover:bg-accent/50"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          {mounted && theme === 'dark' ? (
            <Sun className="h-[18px] w-[18px] text-muted-foreground" />
          ) : (
            <Moon className="h-[18px] w-[18px] text-muted-foreground" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>

        {/* Role Switcher */}
        <RoleSwitcher />

        {/* User Avatar Dropdown */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 rounded-full p-0 hover:bg-accent/50">
              <Avatar className="h-7 w-7 border border-border">
                <AvatarFallback className="bg-primary/20 text-primary text-[10px] font-semibold">
                  AK
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-48">
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium">Alex Kowalski</p>
                <p className="text-xs text-muted-foreground">alex@cybreach.io</p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem variant="destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
