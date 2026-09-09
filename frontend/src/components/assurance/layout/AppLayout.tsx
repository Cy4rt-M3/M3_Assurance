'use client';

import React from 'react';
import { useNavigationStore } from '@/hooks/use-navigation';
import { AppSidebar } from './AppSidebar';
import { AppHeader } from './AppHeader';
import { CommandPalette } from './CommandPalette';
import { SidebarInset, SidebarProvider } from '@/components/ui/sidebar';

interface AppLayoutProps {
  children: React.ReactNode;
}

export function AppLayout({ children }: AppLayoutProps) {
  const {
    activeSection,
    setActiveSection,
  } = useNavigationStore();

  return (
    <SidebarProvider>
      <AppSidebar
        activeSection={activeSection}
        onNavigate={setActiveSection}
        notificationCount={5}
      />
      <SidebarInset>
        <AppHeader
          activeSection={activeSection}
          notificationCount={5}
        />
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </SidebarInset>
      <CommandPalette />
    </SidebarProvider>
  );
}
