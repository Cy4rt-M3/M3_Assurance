'use client';

import React, { useState } from 'react';
import { Bell, Shield, AlertTriangle, FileCheck, FileText, Settings, Check, CheckCheck, Filter } from 'lucide-react';
import { notifications as notifData } from '@/lib/assurance/mock-data';
import { timeAgo } from '@/lib/assurance/utils';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import type { Notification } from '@/lib/assurance/types';

const typeIcons: Record<Notification['type'], React.ComponentType<{ className?: string }>> = {
  evidence_missing: FileCheck,
  validation_failed: AlertTriangle,
  framework_updated: Shield,
  risk_increased: AlertTriangle,
  report_generated: FileText,
  approval_required: Settings,
};

const severityColors: Record<Notification['severity'], string> = {
  info: 'bg-primary/15 text-primary border-primary/30',
  warning: 'bg-warning/15 text-warning border-warning/30',
  error: 'bg-danger/15 text-danger border-danger/30',
  success: 'bg-success/15 text-success border-success/30',
};

const severityDot: Record<Notification['severity'], string> = {
  info: 'bg-primary',
  warning: 'bg-warning',
  error: 'bg-danger',
  success: 'bg-success',
};

export function NotificationsSection() {
  const [filter, setFilter] = useState<'all' | 'unread' | 'error' | 'warning'>('all');
  const [notifs, setNotifs] = useState(notifData);

  const filteredNotifs = notifs.filter((n) => {
    if (filter === 'unread') return !n.read;
    if (filter === 'error') return n.severity === 'error';
    if (filter === 'warning') return n.severity === 'warning';
    return true;
  });

  const unreadCount = notifs.filter((n) => !n.read).length;

  const markRead = (id: string) => {
    setNotifs((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllRead = () => {
    setNotifs((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Notifications</h1>
          <p className="text-sm text-muted-foreground mt-1">
            System alerts and compliance notifications
          </p>
        </div>
        <div className="flex items-center gap-2">
          {unreadCount > 0 && (
            <Button variant="outline" size="sm" onClick={markAllRead} className="gap-1.5 text-xs">
              <CheckCheck className="h-3.5 w-3.5" />
              Mark all read
            </Button>
          )}
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2">
        {(['all', 'unread', 'error', 'warning'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              filter === f
                ? 'bg-primary/15 text-primary border border-primary/30'
                : 'bg-surface text-muted-foreground border border-border hover:text-foreground hover:border-primary/20'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
            {f === 'unread' && unreadCount > 0 && (
              <span className="ml-1.5 text-[10px] bg-primary text-primary-foreground px-1.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-2">
        {filteredNotifs.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">No notifications found</p>
          </div>
        ) : (
          filteredNotifs.map((notif) => {
            const Icon = typeIcons[notif.type];
            return (
              <div
                key={notif.id}
                className={`p-4 rounded-xl border transition-all ${
                  notif.read
                    ? 'bg-card/50 border-border/50'
                    : 'bg-card border-border hover:border-primary/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className={`p-2 rounded-lg shrink-0 ${severityColors[notif.severity]}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {!notif.read && (
                        <div className={`h-2 w-2 rounded-full shrink-0 ${severityDot[notif.severity]}`} />
                      )}
                      <h3 className="text-sm font-medium text-foreground">{notif.title}</h3>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed">{notif.message}</p>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-[10px] text-muted-foreground">{timeAgo(notif.timestamp)}</span>
                      <span className="text-[10px] text-muted-foreground">·</span>
                      <span className="text-[10px] text-muted-foreground">{notif.source}</span>
                      <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${severityColors[notif.severity]}`}>
                        {notif.severity}
                      </Badge>
                    </div>
                  </div>
                  {!notif.read && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => markRead(notif.id)}
                      className="shrink-0 text-xs text-muted-foreground hover:text-foreground"
                    >
                      <Check className="h-3.5 w-3.5" />
                    </Button>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
