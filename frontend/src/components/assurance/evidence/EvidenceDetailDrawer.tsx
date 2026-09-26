'use client';

import React, { useState } from 'react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from '@/components/ui/sheet';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Separator } from '@/components/ui/separator';
import {
  Copy, Check, Download, ShieldCheck, History, Link2, AlertTriangle,
  FileText, Database, User, Clock, Hash, Activity, Shield, ChevronRight,
} from 'lucide-react';
import type { Evidence } from '@/lib/assurance/types';
import {
  getValidationStatusColor, getValidationStatusLabel,
  formatDateTime, truncateHash, getScoreColor,
} from '@/lib/assurance/utils';
import {
  exportToJSON,
  timestampForFilename,
  sanitizeFilenameSegment,
} from '@/lib/assurance/export-utils';
import { useToast } from '@/hooks/use-toast';

interface EvidenceDetailDrawerProps {
  evidence: Evidence | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function getAuditStatusBg(status: string): string {
  switch (status) {
    case 'generated': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'validated': return 'bg-success/15 text-success border-success/30';
    case 'mapped': return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
    case 'expired': return 'bg-danger/15 text-danger border-danger/30';
    case 'rejected': return 'bg-danger/15 text-danger border-danger/30';
    default: return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

function getAuditDotColor(status: string): string {
  switch (status) {
    case 'generated': return 'bg-cyber';
    case 'validated': return 'bg-success';
    case 'mapped': return 'bg-purple-500';
    case 'expired': return 'bg-danger';
    case 'rejected': return 'bg-danger';
    default: return 'bg-muted-foreground';
  }
}

export function EvidenceDetailDrawer({ evidence, open, onOpenChange }: EvidenceDetailDrawerProps) {
  const [copied, setCopied] = useState(false);
  const { toast } = useToast();

  if (!evidence) return null;

  const handleCopyHash = () => {
    navigator.clipboard.writeText(evidence.immutableHash);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const filename = `cybreach_evidence_${sanitizeFilenameSegment(evidence.id)}_${timestampForFilename()}`;
    exportToJSON(evidence, filename);
    toast({
      title: 'Evidence exported',
      description: `${evidence.id} downloaded as JSON.`,
    });
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 bg-card border-l border-border overflow-y-auto">
        {/* Sticky Header */}
        <div className="sticky top-0 z-10 bg-card/95 backdrop-blur border-b border-border p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary/15">
                <Database className="h-4 w-4 text-primary" />
              </div>
              <div>
                <SheetHeader className="p-0">
                  <SheetTitle className="text-sm font-mono text-foreground">{evidence.id}</SheetTitle>
                  <SheetDescription className="sr-only">Evidence detail view with metadata, audit trail, and linked items</SheetDescription>
                </SheetHeader>
                <p className="text-[11px] text-muted-foreground mt-0.5">Evidence Detail</p>
              </div>
            </div>
            <Badge variant="outline" className={`text-[10px] ${getValidationStatusColor(evidence.validationStatus)}`}>
              {getValidationStatusLabel(evidence.validationStatus)}
            </Badge>
          </div>
        </div>

        <div className="p-4 space-y-5">
          {/* Description */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Description</h3>
            <p className="text-xs text-foreground leading-relaxed bg-surface rounded-lg p-3 border border-border/50">
              {evidence.description}
            </p>
          </div>

          {/* Metadata Grid */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Metadata</h3>
            <div className="grid grid-cols-2 gap-2">
              <MetadataItem icon={Database} label="Asset" value={evidence.asset} />
              <MetadataItem icon={Activity} label="Source" value={evidence.source} />
              <MetadataItem icon={Shield} label="Framework" value={evidence.framework} />
              <MetadataItem icon={FileText} label="Control" value={evidence.controlRef} />
              <MetadataItem icon={User} label="Owner" value={evidence.owner} />
              <MetadataItem icon={Clock} label="Timestamp" value={formatDateTime(evidence.timestamp)} />
            </div>
            {/* Extra metadata fields */}
            <div className="mt-2 space-y-1.5">
              {Object.entries(evidence.metadata).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground capitalize">{key.replace(/([A-Z])/g, ' $1').trim()}:</span>
                  <span className="text-foreground font-medium">{value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Confidence Score */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Confidence Score</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">Validation Confidence</span>
                <span className={`text-lg font-bold ${getScoreColor(evidence.confidenceScore * 100)}`}>
                  {Math.round(evidence.confidenceScore * 100)}%
                </span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    evidence.confidenceScore >= 0.8 ? 'bg-success' :
                    evidence.confidenceScore >= 0.6 ? 'bg-warning' : 'bg-danger'
                  }`}
                  style={{ width: `${evidence.confidenceScore * 100}%` }}
                />
              </div>
            </div>
          </div>

          {/* Immutable Hash */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Immutable Hash</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              <div className="flex items-center justify-between gap-2">
                <code className="text-[10px] font-mono text-foreground break-all flex-1">
                  {evidence.immutableHash}
                </code>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCopyHash}
                  className="shrink-0 h-7 px-2 text-xs"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                </Button>
              </div>
            </div>
          </div>

          {/* Linked Items */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Linked Items</h3>
            <div className="space-y-2">
              <LinkedSection icon={Link2} label="Linked Controls" items={evidence.linkedControls} color="text-primary" />
              <LinkedSection icon={AlertTriangle} label="Linked Risks" items={evidence.linkedRisks} color="text-warning" />
              <LinkedSection icon={FileText} label="Linked Reports" items={evidence.linkedReports} color="text-success" />
            </div>
          </div>

          {/* Audit Trail */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Audit Trail</h3>
              <span className="text-[10px] text-muted-foreground">{evidence.auditTrail.length} events</span>
            </div>
            <div className="relative pl-6">
              {/* Vertical line */}
              <div className="absolute left-2 top-2 bottom-2 w-px bg-border" />
              {evidence.auditTrail.map((event, idx) => (
                <div key={event.id} className="relative mb-4 last:mb-0">
                  {/* Dot */}
                  <div className={`absolute -left-[18px] top-1 h-3 w-3 rounded-full ${getAuditDotColor(event.status)} ring-4 ring-card`} />
                  {/* Event card */}
                  <div className="bg-surface rounded-lg p-3 border border-border/50">
                    <div className="flex items-center justify-between mb-1.5">
                      <Badge variant="outline" className={`text-[10px] ${getAuditStatusBg(event.status)}`}>
                        {event.status}
                      </Badge>
                      <span className="text-[10px] text-muted-foreground">{formatDateTime(event.timestamp)}</span>
                    </div>
                    <p className="text-xs text-foreground mb-1.5">{event.description}</p>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Activity className="h-3 w-3" />
                        {event.module}
                      </span>
                      <span className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {event.actor}
                      </span>
                      <span className="flex items-center gap-1 font-mono">
                        <Hash className="h-3 w-3" />
                        {truncateHash(event.hash)}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur border-t border-border p-4 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5" onClick={handleDownload}>
            <Download className="h-3.5 w-3.5" />
            Download
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <ShieldCheck className="h-3.5 w-3.5" />
            Verify
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <History className="h-3.5 w-3.5" />
            History
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function MetadataItem({ icon: Icon, label, value }: { icon: React.ComponentType<{ className?: string }>, label: string, value: string }) {
  return (
    <div className="bg-surface rounded-lg p-2.5 border border-border/50">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="h-3 w-3 text-muted-foreground" />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-xs font-medium text-foreground truncate">{value}</p>
    </div>
  );
}

function LinkedSection({ icon: Icon, label, items, color }: { icon: React.ComponentType<{ className?: string }>, label: string, items: string[], color: string }) {
  return (
    <div className="bg-surface rounded-lg p-2.5 border border-border/50">
      <div className="flex items-center gap-1.5 mb-2">
        <Icon className={`h-3 w-3 ${color}`} />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
        <span className="text-[10px] text-muted-foreground ml-auto">{items.length}</span>
      </div>
      {items.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {items.map((item) => (
            <Badge key={item} variant="outline" className="text-[10px] font-mono bg-card border-border">
              {item}
            </Badge>
          ))}
        </div>
      ) : (
        <p className="text-[10px] text-muted-foreground italic">No items linked</p>
      )}
    </div>
  );
}
