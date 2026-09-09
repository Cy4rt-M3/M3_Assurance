'use client';

import React, { useState } from 'react';
import { Bell, CheckCircle2, AlertTriangle, AlertCircle, Info, Check, CheckCheck, Settings as SettingsIcon } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
} from '@/components/ui/dropdown-menu';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useNavigationStore } from '@/hooks/use-navigation';
import { notifications as notifData } from '@/lib/assurance/mock-data';
import { timeAgo } from '@/lib/assurance/utils';
import type { Notification } from '@/lib/assurance/types';

const typeIcons: Record<Notification['type'], React.ComponentType<{ className?: string }>> = {
  evidence_missing: AlertTriangle,
  validation_failed: AlertCircle,
  framework_updated: Info,
  risk_increased: AlertTriangle,
  report_generated: CheckCircle2,
  approval_required: Info,
};

const severityColors: Record<Notification['severity'], { dot: string; bg: string; text: string }> = {
  info: { dot: 'bg-primary', bg: 'bg-primary/10', text: 'text-primary' },
  warning: { dot: 'bg-warning', bg: 'bg-warning/10', text: 'text-warning' },
  error: { dot: 'bg-danger', bg: 'bg-danger/10', text: 'text-danger' },
  success: { dot: 'bg-success', bg: 'bg-success/10', text: 'text-success' },
};

interface NotificationsDropdownProps {
  notificationCount: number;
}

export function NotificationsDropdown({ notificationCount }: NotificationsDropdownProps) {
  const { setActiveSection } = useNavigationStore();
  const [notifs, setNotifs] = useState(notifData);
  const unreadCount = notifs.filter((n) => !n.read).length;

  const markRead = (id: string) => {
    setNotifs((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const viewAll = () => {
    setActiveSection('notifications');
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative h-8 w-8 hover:bg-accent/50"
        >
          <Bell className="h-[18px] w-[18px] text-muted-foreground" />
          {notificationCount > 0 && (
            <Badge
              variant="destructive"
              className="absolute -top-0.5 -right-0.5 h-4 min-w-4 px-1 text-[9px] font-bold flex items-center justify-center"
            >
              {notificationCount}
            </Badge>
          )}
          <span className="sr-only">Notifications</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-96 p-0">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-border">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-semibold text-foreground">Notifications</span>
            {unreadCount > 0 && (
              <Badge variant="outline" className="text-[10px] bg-primary/10 text-primary border-primary/20">
                {unreadCount} new
              </Badge>
            )}
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={markAllRead}
            disabled={unreadCount === 0}
          >
            <CheckCheck className="h-3 w-3" />
            Mark all read
          </Button>
        </div>

        {/* Notifications List */}
        <ScrollArea className="h-[360px]">
          <div className="space-y-1 p-2">
            {notifs.slice(0, 8).map((notif) => {
              const Icon = typeIcons[notif.type];
              const colors = severityColors[notif.severity];
              return (
                <div
                  key={notif.id}
                  className={`p-2.5 rounded-lg border transition-colors cursor-pointer group ${
                    notif.read
                      ? 'bg-transparent border-transparent'
                      : `${colors.bg} border-transparent hover:border-border/50`
                  }`}
                  onClick={() => markRead(notif.id)}
                >
                  <div className="flex items-start gap-2.5">
                    <div className={`p-1.5 rounded-md ${colors.bg} shrink-0 mt-0.5`}>
                      <Icon className={`h-3.5 w-3.5 ${colors.text}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-2 mb-0.5">
                        <p className={`text-xs ${notif.read ? 'text-muted-foreground' : 'font-medium text-foreground'} truncate`}>
                          {notif.title}
                        </p>
                        {!notif.read && (
                          <div className={`h-2 w-2 rounded-full ${colors.dot} shrink-0 mt-1`} />
                        )}
                      </div>
                      <p className="text-[11px] text-muted-foreground line-clamp-2 leading-snug">
                        {notif.message}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-muted-foreground">{timeAgo(notif.timestamp)}</span>
                        <span className="text-[10px] text-muted-foreground">·</span>
                        <span className="text-[10px] text-muted-foreground">{notif.source}</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>

        {/* Footer */}
        <DropdownMenuSeparator className="m-0" />
        <div className="flex items-center gap-2 p-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 text-xs gap-1.5"
            onClick={viewAll}
          >
            <Bell className="h-3.5 w-3.5" />
            View All Notifications
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs gap-1.5"
            onClick={() => setActiveSection('settings')}
          >
            <SettingsIcon className="h-3.5 w-3.5" />
          </Button>
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
