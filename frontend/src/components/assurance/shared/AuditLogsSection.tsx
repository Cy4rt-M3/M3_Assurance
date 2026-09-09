'use client';

import React, { useState } from 'react';
import { ScrollText, Search, Filter, Download, ExternalLink } from 'lucide-react';
import { evidenceItems, frameworks } from '@/lib/assurance/mock-data';
import { formatDateTime, truncateHash, getValidationStatusColor, getComplianceStatusBg, getComplianceStatusLabel } from '@/lib/assurance/utils';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import type { AuditEvent } from '@/lib/assurance/types';

interface AuditLogEntry extends AuditEvent {
  evidenceId: string;
  framework: string;
}

export function AuditLogsSection() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filterModule, setFilterModule] = useState('all');

  // Flatten all audit events from evidence items
  const allEvents: AuditLogEntry[] = evidenceItems.flatMap((ev) =>
    ev.auditTrail.map((ae) => ({
      ...ae,
      evidenceId: ev.id,
      framework: ev.framework,
    }))
  ).sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());

  const modules = ['all', ...new Set(allEvents.map((e) => e.module))];

  const filteredEvents = allEvents.filter((event) => {
    const matchesSearch = searchQuery === '' ||
      event.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.evidenceId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.actor.toLowerCase().includes(searchQuery.toLowerCase()) ||
      event.hash.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesModule = filterModule === 'all' || event.module === filterModule;
    return matchesSearch && matchesModule;
  });

  const statusColors: Record<string, string> = {
    generated: 'bg-primary/15 text-primary border-primary/30',
    validated: 'bg-success/15 text-success border-success/30',
    mapped: 'bg-purple-500/15 text-purple-400 border-purple-500/30',
    expired: 'bg-danger/15 text-danger border-danger/30',
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Audit Logs</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Immutable audit trail for all compliance activities
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-xs border-primary/30 text-primary">
            {filteredEvents.length} events
          </Badge>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search events..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-xs bg-card border-border"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <Filter className="h-3.5 w-3.5 text-muted-foreground" />
          {modules.map((mod) => (
            <button
              key={mod}
              onClick={() => setFilterModule(mod)}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-colors ${
                filterModule === mod
                  ? 'bg-primary/15 text-primary border border-primary/30'
                  : 'bg-surface text-muted-foreground border border-border hover:text-foreground'
              }`}
            >
              {mod === 'all' ? 'All Modules' : mod}
            </button>
          ))}
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="bg-card border border-border rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Timestamp</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Evidence ID</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Module</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Actor</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Status</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Description</th>
                <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-3">Hash</th>
              </tr>
            </thead>
            <tbody>
              {filteredEvents.map((event, idx) => (
                <tr
                  key={`${event.id}-${idx}`}
                  className="border-b border-border/50 hover:bg-surface/50 transition-colors"
                >
                  <td className="px-4 py-2.5 text-xs text-muted-foreground whitespace-nowrap">
                    {formatDateTime(event.timestamp)}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-xs font-mono text-primary">{event.evidenceId}</span>
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant="outline" className="text-[10px] bg-surface border-border">
                      {event.module}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-foreground">{event.actor}</td>
                  <td className="px-4 py-2.5">
                    <Badge variant="outline" className={`text-[10px] ${statusColors[event.status] || 'bg-muted text-muted-foreground'}`}>
                      {event.status}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-muted-foreground max-w-xs truncate">
                    {event.description}
                  </td>
                  <td className="px-4 py-2.5">
                    <span className="text-[10px] font-mono text-muted-foreground" title={event.hash}>
                      {truncateHash(event.hash)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Info Banner */}
      <div className="bg-primary/5 border border-primary/20 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <ScrollText className="h-5 w-5 text-primary shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-semibold text-foreground">Immutable Audit Trail</h3>
            <p className="text-xs text-muted-foreground mt-1">
              Every event in this audit log is cryptographically hashed and immutable. The audit trail
              captures the complete evidence lifecycle from Strike Engine generation through Validator
              approval to Assurance mapping and reporting.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
