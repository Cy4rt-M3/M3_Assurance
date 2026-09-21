'use client';

import React from 'react';
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
  FileText, Download, Share2, FileSpreadsheet, FileJson,
  Calendar, User, Building2, Shield, CheckCircle2, Clock,
  AlertCircle, XCircle, TrendingUp, Database, Target, AlertTriangle,
} from 'lucide-react';
import type { Report } from '@/lib/assurance/types';
import {
  getReportStatusColor, getScoreColor, formatDate,
} from '@/lib/assurance/utils';
import {
  exportToCSV,
  exportToJSON,
  timestampForFilename,
  sanitizeFilenameSegment,
} from '@/lib/assurance/export-utils';
import { useToast } from '@/hooks/use-toast';

interface ReportDetailDrawerProps {
  report: Report | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ReportDetailDrawer({ report, open, onOpenChange }: ReportDetailDrawerProps) {
  const { toast } = useToast();

  if (!report) return null;

  const baseFilename = `cybreach_report_${sanitizeFilenameSegment(report.title)}_${timestampForFilename()}`;

  const handleExportCSV = () => {
    exportToCSV([report as unknown as Record<string, unknown>], baseFilename);
    toast({
      title: 'Report exported',
      description: `${report.title} exported as CSV.`,
    });
  };

  const handleExportJSON = () => {
    exportToJSON(report, baseFilename);
    toast({
      title: 'Report exported',
      description: `${report.title} exported as JSON.`,
    });
  };

  const handleExportPDF = () => {
    // No PDF library available — fall back to the browser print dialog which
    // the user can save as PDF. Toast first so the action is acknowledged.
    toast({
      title: 'Preparing PDF',
      description: 'Opening print dialog. Choose "Save as PDF" to export.',
    });
    if (typeof window !== 'undefined') {
      window.setTimeout(() => window.print(), 350);
    }
  };

  const handleExportExcel = () => {
    // Excel (xlsx) requires a binary library we don't ship. Inform the user
    // and offer the CSV alternative which opens natively in Excel.
    toast({
      title: 'Excel export coming soon',
      description: 'Use the CSV option — it opens directly in Microsoft Excel.',
    });
  };

  const statusIcon = report.status === 'generated' ? <CheckCircle2 className="h-4 w-4 text-success" /> :
    report.status === 'scheduled' ? <Clock className="h-4 w-4 text-cyber" /> :
    report.status === 'pending' ? <AlertCircle className="h-4 w-4 text-warning" /> :
    <XCircle className="h-4 w-4 text-muted-foreground" />;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-2xl p-0 bg-card border-l border-border overflow-y-auto">
        {/* Sticky Header */}
        <div className="sticky top-0 z-10 bg-card/95 backdrop-blur border-b border-border p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-primary/15">
                <FileText className="h-4 w-4 text-primary" />
              </div>
              <div className="min-w-0">
                <SheetHeader className="p-0">
                  <SheetTitle className="text-sm font-semibold text-foreground truncate">{report.title}</SheetTitle>
                  <SheetDescription className="sr-only">Report detail with scores, preview, and export options</SheetDescription>
                </SheetHeader>
                <div className="flex items-center gap-2 mt-0.5">
                  <Badge variant="outline" className="text-[10px]">{report.type}</Badge>
                  <span className="text-[10px] font-mono text-muted-foreground">{report.id}</span>
                </div>
              </div>
            </div>
            <Badge variant="outline" className={`text-[10px] capitalize flex items-center gap-1 ${getReportStatusColor(report.status)}`}>
              {statusIcon}
              {report.status}
            </Badge>
          </div>
        </div>

        <div className="p-4 space-y-5">
          {/* Metadata Grid */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Report Details</h3>
            <div className="grid grid-cols-2 gap-2">
              <MetaItem icon={Shield} label="Framework" value={report.framework} />
              <MetaItem icon={Building2} label="Business Unit" value={report.businessUnit} />
              <MetaItem icon={User} label="Author" value={report.author} />
              <MetaItem icon={Calendar} label="Date Range" value={`${formatDate(report.dateRange.start)} - ${formatDate(report.dateRange.end)}`} />
              <MetaItem icon={Clock} label="Generated" value={report.generatedAt ? formatDate(report.generatedAt) : report.scheduledAt ? `Scheduled: ${formatDate(report.scheduledAt)}` : '—'} />
              <MetaItem icon={FileText} label="Report ID" value={report.id} mono />
            </div>
          </div>

          {/* Score Cards Grid */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Compliance Metrics</h3>
            {/* Primary scores - larger */}
            <div className="grid grid-cols-2 gap-2">
              <div className={`rounded-lg p-3 border ${report.complianceScore >= 80 ? 'bg-success/10 border-success/30' : report.complianceScore >= 60 ? 'bg-warning/10 border-warning/30' : 'bg-danger/10 border-danger/30'}`}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    <Shield className={`h-3.5 w-3.5 ${getScoreColor(report.complianceScore)}`} />
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Compliance</span>
                  </div>
                </div>
                <p className={`text-2xl font-bold ${getScoreColor(report.complianceScore)} leading-none`}>{report.complianceScore}%</p>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden mt-2">
                  <div className={`h-full rounded-full ${report.complianceScore >= 80 ? 'bg-success' : report.complianceScore >= 60 ? 'bg-warning' : 'bg-danger'}`} style={{ width: `${report.complianceScore}%` }} />
                </div>
              </div>
              <div className={`rounded-lg p-3 border ${report.resilienceScore >= 80 ? 'bg-success/10 border-success/30' : report.resilienceScore >= 60 ? 'bg-warning/10 border-warning/30' : 'bg-danger/10 border-danger/30'}`}>
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5">
                    <TrendingUp className={`h-3.5 w-3.5 ${getScoreColor(report.resilienceScore)}`} />
                    <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Resilience</span>
                  </div>
                </div>
                <p className={`text-2xl font-bold ${getScoreColor(report.resilienceScore)} leading-none`}>{report.resilienceScore}%</p>
                <div className="h-1.5 bg-muted rounded-full overflow-hidden mt-2">
                  <div className={`h-full rounded-full ${report.resilienceScore >= 80 ? 'bg-success' : report.resilienceScore >= 60 ? 'bg-warning' : 'bg-danger'}`} style={{ width: `${report.resilienceScore}%` }} />
                </div>
              </div>
            </div>
            {/* Secondary metrics - smaller */}
            <div className="grid grid-cols-3 gap-2">
              <ScoreCard icon={Target} label="Controls" value={report.controlsCovered} />
              <ScoreCard icon={Database} label="Evidence" value={report.evidenceLinked} />
              <ScoreCard icon={AlertTriangle} label="Risks" value={report.risksIdentified} />
            </div>
          </div>

          {/* Report Preview */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Report Preview</h3>
            <div className="bg-surface/30 border border-border/50 rounded-lg p-4 space-y-4">
              {/* Mock document header */}
              <div className="border-b border-border/50 pb-3">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <p className="text-sm font-bold text-foreground">{report.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{report.framework} Compliance Assessment</p>
                  </div>
                  <div className="text-right">
                    <p className="text-[10px] text-muted-foreground">Confidential</p>
                    <p className="text-[10px] text-muted-foreground">{report.businessUnit}</p>
                  </div>
                </div>
              </div>

              {/* Executive Summary */}
              <div className="space-y-1.5">
                <p className="text-[11px] font-semibold text-foreground flex items-center gap-1.5">
                  <span className="h-3 w-0.5 bg-primary rounded-full" />
                  Executive Summary
                </p>
                <p className="text-[10px] text-muted-foreground leading-relaxed">
                  This report presents the compliance assessment for {report.framework} across {report.businessUnit}. 
                  The overall compliance score is {report.complianceScore}% with a resilience score of {report.resilienceScore}%. 
                  {report.risksIdentified} risks were identified, with {report.controlsCovered} controls assessed and {report.evidenceLinked} evidence items validated.
                </p>
              </div>

              <Separator className="bg-border/50" />

              {/* Compliance Overview */}
              <div className="space-y-1.5">
                <p className="text-[11px] font-semibold text-foreground flex items-center gap-1.5">
                  <span className="h-3 w-0.5 bg-success rounded-full" />
                  Compliance Overview
                </p>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground">Overall Compliance</span>
                    <span className={`font-bold ${getScoreColor(report.complianceScore)}`}>{report.complianceScore}%</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${report.complianceScore >= 80 ? 'bg-success' : report.complianceScore >= 60 ? 'bg-warning' : 'bg-danger'}`}
                      style={{ width: `${report.complianceScore}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-muted-foreground">Resilience Score</span>
                    <span className={`font-bold ${getScoreColor(report.resilienceScore)}`}>{report.resilienceScore}%</span>
                  </div>
                  <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${report.resilienceScore >= 80 ? 'bg-success' : report.resilienceScore >= 60 ? 'bg-warning' : 'bg-danger'}`}
                      style={{ width: `${report.resilienceScore}%` }}
                    />
                  </div>
                </div>
              </div>

              <Separator className="bg-border/50" />

              {/* Risk Findings */}
              <div className="space-y-1.5">
                <p className="text-[11px] font-semibold text-foreground flex items-center gap-1.5">
                  <span className="h-3 w-0.5 bg-danger rounded-full" />
                  Key Risk Findings
                </p>
                <div className="space-y-1">
                  <div className="flex items-start gap-2 text-[10px]">
                    <span className="text-danger font-bold mt-0.5">•</span>
                    <span className="text-muted-foreground">{report.risksIdentified} risks identified requiring attention</span>
                  </div>
                  <div className="flex items-start gap-2 text-[10px]">
                    <span className="text-warning font-bold mt-0.5">•</span>
                    <span className="text-muted-foreground">Evidence coverage gaps detected in select controls</span>
                  </div>
                  <div className="flex items-start gap-2 text-[10px]">
                    <span className="text-success font-bold mt-0.5">•</span>
                    <span className="text-muted-foreground">{report.controlsCovered} controls successfully assessed</span>
                  </div>
                </div>
              </div>

              <Separator className="bg-border/50" />

              {/* Audit Trail Note */}
              <div className="flex items-center gap-2 pt-1">
                <Shield className="h-3 w-3 text-primary shrink-0" />
                <p className="text-[10px] text-muted-foreground italic">
                  This report is backed by validated evidence with full audit trail traceability.
                </p>
              </div>
            </div>
          </div>

          {/* Export Options */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Export Options</h3>
            <div className="grid grid-cols-4 gap-2">
              <ExportButton icon={FileText} label="PDF" color="text-danger" onClick={handleExportPDF} />
              <ExportButton icon={FileSpreadsheet} label="Excel" color="text-success" onClick={handleExportExcel} />
              <ExportButton icon={FileJson} label="CSV" color="text-cyber" onClick={handleExportCSV} />
              <ExportButton icon={FileJson} label="JSON" color="text-warning" onClick={handleExportJSON} />
            </div>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur border-t border-border p-4 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5" onClick={handleExportJSON}>
            <Download className="h-3.5 w-3.5" />
            Download
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <Share2 className="h-3.5 w-3.5" />
            Share
          </Button>
          <Button variant="default" size="sm" className="flex-1 text-xs gap-1.5" onClick={handleExportPDF}>
            <FileText className="h-3.5 w-3.5" />
            Full Report
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function MetaItem({ icon: Icon, label, value, mono }: { icon: React.ComponentType<{ className?: string }>, label: string, value: string, mono?: boolean }) {
  return (
    <div className="bg-surface rounded-lg p-2.5 border border-border/50">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="h-3 w-3 text-muted-foreground" />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <p className={`text-xs font-medium text-foreground truncate ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}

function ScoreCard({ icon: Icon, label, value, score, small }: { icon: React.ComponentType<{ className?: string }>, label: string, value: string | number, score?: number, small?: boolean }) {
  const colorClass = score !== undefined ? getScoreColor(score) : 'text-foreground';
  return (
    <div className="bg-surface rounded-lg p-3 border border-border/50 text-center">
      <Icon className={`h-4 w-4 mx-auto mb-1 ${colorClass}`} />
      <p className={`${small ? 'text-xs' : 'text-lg'} font-bold ${colorClass} leading-none`}>{value}</p>
      <p className="text-[9px] text-muted-foreground uppercase tracking-wide mt-1">{label}</p>
    </div>
  );
}

function ExportButton({ icon: Icon, label, color, onClick }: { icon: React.ComponentType<{ className?: string }>, label: string, color: string, onClick?: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col items-center gap-1.5 p-3 rounded-lg bg-surface border border-border/50 hover:border-primary/30 hover:bg-surface/70 transition-colors group"
    >
      <Icon className={`h-5 w-5 ${color} group-hover:scale-110 transition-transform`} />
      <span className="text-[10px] text-muted-foreground font-medium">{label}</span>
    </button>
  );
}
