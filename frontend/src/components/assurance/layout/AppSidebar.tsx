'use client';

import React from 'react';
import { motion } from 'framer-motion';
import {
  LayoutDashboard,
  Shield,
  FileCheck,
  AlertTriangle,
  FileText,
  Bell,
  ScrollText,
  Settings,
  CheckSquare,
} from 'lucide-react';
import type { SectionId } from '@/lib/assurance/types';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuBadge,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
  SidebarSeparator,
  useSidebar,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface NavItem {
  id: SectionId;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: number;
}

const mainNavItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'frameworks', label: 'Framework Setup', icon: Shield },
  { id: 'evidence', label: 'Evidence Aggregator', icon: FileCheck },
  { id: 'risk', label: 'Risk & Resilience', icon: AlertTriangle },
  { id: 'reports', label: 'Report Generation', icon: FileText },
  { id: 'tasks', label: 'Task Management', icon: CheckSquare, badge: 7 },
];

const secondaryNavItems: NavItem[] = [
  { id: 'notifications', label: 'Notifications', icon: Bell, badge: 5 },
  { id: 'audit-logs', label: 'Audit Logs', icon: ScrollText },
  { id: 'settings', label: 'Settings', icon: Settings },
];

interface AppSidebarProps {
  activeSection: SectionId;
  onNavigate: (section: SectionId) => void;
  notificationCount?: number;
}

export function AppSidebar({ activeSection, onNavigate, notificationCount = 5 }: AppSidebarProps) {
  const { state } = useSidebar();
  const isCollapsed = state === 'collapsed';

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      {/* Logo Header */}
      <SidebarHeader className="px-3 pt-4 pb-3">
        <div className="flex items-center gap-2.5 px-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-primary/20 border border-primary/30">
            <Shield className="h-4 w-4 text-primary" />
          </div>
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col"
            >
              <span className="text-sm font-bold tracking-tight text-foreground">
                Cy<span className="cyber-gradient-text">Breach</span>
              </span>
              <span className="text-[10px] font-semibold tracking-[0.2em] text-primary/80 uppercase">
                Assurance
              </span>
            </motion.div>
          )}
        </div>
      </SidebarHeader>

      <SidebarSeparator />

      {/* Navigation */}
      <SidebarContent className="px-2 py-2">
        {/* Main Navigation */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {mainNavItems.map((item) => {
                const isActive = activeSection === item.id;
                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.label}
                      onClick={() => onNavigate(item.id)}
                      className={`
                        relative h-9 px-3 transition-all duration-200
                        ${isActive
                          ? 'bg-primary/15 text-primary font-medium border-l-2 border-primary pl-[10px]'
                          : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                        }
                      `}
                    >
                      <item.icon className={`h-[18px] w-[18px] ${isActive ? 'text-primary' : ''}`} />
                      <span>{item.label}</span>
                      {isActive && (
                        <motion.div
                          layoutId="activeNavIndicator"
                          className="absolute left-0 top-0 h-full w-0.5 bg-primary"
                          transition={{ type: 'spring', bounce: 0.2, duration: 0.4 }}
                        />
                      )}
                    </SidebarMenuButton>
                    {item.badge !== undefined && item.badge > 0 && (
                      <SidebarMenuBadge className="bg-primary text-primary-foreground text-[10px] min-w-[18px] h-[18px] px-1">
                        {item.badge}
                      </SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>

        <SidebarSeparator className="mx-3" />

        {/* Secondary Navigation */}
        <SidebarGroup>
          <SidebarGroupContent>
            <SidebarMenu>
              {secondaryNavItems.map((item) => {
                const isActive = activeSection === item.id;
                const badge = item.id === 'notifications' ? notificationCount : undefined;
                return (
                  <SidebarMenuItem key={item.id}>
                    <SidebarMenuButton
                      isActive={isActive}
                      tooltip={item.label}
                      onClick={() => onNavigate(item.id)}
                      className={`
                        relative h-9 px-3 transition-all duration-200
                        ${isActive
                          ? 'bg-primary/15 text-primary font-medium border-l-2 border-primary pl-[10px]'
                          : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                        }
                      `}
                    >
                      <item.icon className={`h-[18px] w-[18px] ${isActive ? 'text-primary' : ''}`} />
                      <span>{item.label}</span>
                    </SidebarMenuButton>
                    {badge !== undefined && badge > 0 && (
                      <SidebarMenuBadge className="bg-primary text-primary-foreground text-[10px] min-w-[18px] h-[18px] px-1">
                        {badge}
                      </SidebarMenuBadge>
                    )}
                  </SidebarMenuItem>
                );
              })}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      {/* Footer with User Info */}
      <SidebarFooter className="px-2 pb-3">
        <SidebarSeparator className="mx-1 mb-2" />
        {/* System Health Status */}
        {!isCollapsed && (
          <div className="mx-1 mb-2 p-2.5 rounded-lg bg-surface border border-border/50">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">System Health</span>
              <span className="text-[9px] font-medium text-success flex items-center gap-0.5">
                <span className="h-1.5 w-1.5 rounded-full bg-success cyber-pulse" />
                Operational
              </span>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-success" />
                  <span className="text-muted-foreground">Strike Engine</span>
                </div>
                <span className="text-success font-medium">Online</span>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-success" />
                  <span className="text-muted-foreground">Validator</span>
                </div>
                <span className="text-success font-medium">Online</span>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-success" />
                  <span className="text-muted-foreground">Evidence DB</span>
                </div>
                <span className="text-success font-medium">Synced</span>
              </div>
              <div className="flex items-center justify-between text-[10px]">
                <div className="flex items-center gap-1.5">
                  <div className="h-1.5 w-1.5 rounded-full bg-warning" />
                  <span className="text-muted-foreground">Report Engine</span>
                </div>
                <span className="text-warning font-medium">Degraded</span>
              </div>
            </div>
          </div>
        )}
        {/* Compliance Score Badge */}
        {!isCollapsed && (
          <div className="mx-1 mb-2 p-2.5 rounded-lg bg-gradient-to-r from-primary/10 to-transparent border border-primary/20">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Compliance</span>
              <span className="text-sm font-bold text-success">73%</span>
            </div>
            <div className="h-1.5 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-success rounded-full" style={{ width: '73%' }} />
            </div>
            <div className="flex items-center justify-between mt-1.5">
              <span className="text-[9px] text-muted-foreground">5 frameworks</span>
              <span className="text-[9px] text-success flex items-center gap-0.5">
                <span className="h-1 w-1 rounded-full bg-success cyber-pulse" />
                Live
              </span>
            </div>
          </div>
        )}
        <div className="flex items-center gap-2.5 px-2 py-1.5">
          <Avatar className="h-8 w-8 border border-border">
            <AvatarFallback className="bg-primary/20 text-primary text-xs font-semibold">
              AK
            </AvatarFallback>
          </Avatar>
          {!isCollapsed && (
            <motion.div
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col min-w-0"
            >
              <span className="text-xs font-medium text-foreground truncate">Alex Kowalski</span>
              <span className="text-[10px] text-muted-foreground truncate">GRC Analyst</span>
            </motion.div>
          )}
        </div>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
}
