'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  evidenceItems,
  missingEvidenceItems,
  evidenceTrendData,
} from '@/lib/assurance/mock-data';
import {
  getValidationStatusColor,
  getValidationStatusLabel,
  formatDateTime,
  truncateHash,
  getRiskLevelBg,
  getRiskLevelLabel,
  getScoreColor,
} from '@/lib/assurance/utils';
import { CHART_THEME, TOOLTIP_STYLE, AXIS_PROPS, GRID_PROPS } from '@/lib/assurance/chart-theme';
import type { Evidence, ValidationStatus, EvidenceType } from '@/lib/assurance/types';
import {
  exportToCSV,
  exportToJSON,
  timestampForFilename,
} from '@/lib/assurance/export-utils';
import { useToast } from '@/hooks/use-toast';
import { useRecentlyViewedStore } from '@/hooks/use-recently-viewed';
import { EvidenceDetailDrawer } from './EvidenceDetailDrawer';
import { TableSkeleton } from '@/components/assurance/shared/Skeletons';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  FileCheck,
  ShieldCheck,
  Clock,
  AlertOctagon,
  Search,
  Database,
  TrendingUp,
  Activity,
  GitBranch,
  AlertTriangle,
  Hash,
  User,
  CalendarClock,
  FileSearch,
  Download,
  FileJson,
  FileSpreadsheet,
  ChevronDown,
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
} from 'recharts';

// ---------- Evidence type label helper ----------
function getEvidenceTypeLabel(type: EvidenceType): string {
  const map: Record<EvidenceType, string> = {
    automated_scan: 'Auto Scan',
    manual_review: 'Manual Review',
    policy_document: 'Policy Doc',
    configuration: 'Config',
    log_evidence: 'Log',
    interview: 'Interview',
    observation: 'Observation',
  };
  return map[type];
}

function getEvidenceTypeBg(type: EvidenceType): string {
  const map: Record<EvidenceType, string> = {
    automated_scan: 'bg-cyber/15 text-cyber border-cyber/30',
    manual_review: 'bg-primary/15 text-primary border-primary/30',
    policy_document: 'bg-warning/15 text-warning border-warning/30',
    configuration: 'bg-success/15 text-success border-success/30',
    log_evidence: 'bg-muted text-muted-foreground border-muted-foreground/30',
    interview: 'bg-danger/15 text-danger border-danger/30',
    observation: 'bg-warning/15 text-warning border-warning/30',
  };
  return map[type];
}

// ---------- Audit trail status color ----------
function getAuditStatusColor(status: string): string {
  switch (status) {
    case 'generated':
      return 'bg-blue-500';
    case 'validated':
      return 'bg-success';
    case 'mapped':
      return 'bg-purple-500';
    case 'expired':
      return 'bg-danger';
    case 'rejected':
      return 'bg-danger';
    default:
      return 'bg-muted-foreground';
  }
}

function getAuditStatusBg(status: string): string {
  switch (status) {
    case 'generated':
      return 'bg-blue-500/15 text-blue-400 border-blue-500/30';
    case 'validated':
      return 'bg-success/15 text-success border-success/30';
    case 'mapped':
      return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
    case 'expired':
      return 'bg-danger/15 text-danger border-danger/30';
    case 'rejected':
      return 'bg-danger/15 text-danger border-danger/30';
    default:
      return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

function getIssueTypeBg(issue: string): string {
  switch (issue) {
    case 'missing':
      return 'bg-danger/15 text-danger border-danger/30';
    case 'expired':
      return 'bg-warning/15 text-warning border-warning/30';
    case 'weak':
      return 'bg-orange-500/15 text-orange-400 border-orange-500/30';
    case 'duplicate':
      return 'bg-purple-500/15 text-purple-400 border-purple-500/30';
    case 'invalid':
      return 'bg-danger/15 text-danger border-danger/30';
    default:
      return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

// ===================== TAB 1: Evidence Dashboard =====================
function EvidenceDashboard() {
  const total = evidenceItems.length;
  const validated = evidenceItems.filter((e) => e.validationStatus === 'validated').length;
  const pending = evidenceItems.filter((e) => e.validationStatus === 'pending').length;
  const expired = evidenceItems.filter((e) => e.validationStatus === 'expired').length;

  const kpis = [
    {
      label: 'Total Evidence',
      value: total,
      icon: Database,
      color: 'text-primary',
      bg: 'bg-primary/10',
    },
    {
      label: 'Validated Evidence',
      value: validated,
      icon: ShieldCheck,
      color: 'text-success',
      bg: 'bg-success/10',
    },
    {
      label: 'Pending Validation',
      value: pending,
      icon: Clock,
      color: 'text-warning',
      bg: 'bg-warning/10',
    },
    {
      label: 'Expired Evidence',
      value: expired,
      icon: AlertOctagon,
      color: 'text-danger',
      bg: 'bg-danger/10',
    },
  ];

  // Evidence by framework for bar chart
  const frameworkCounts = useMemo(() => {
    const map: Record<string, number> = {};
    evidenceItems.forEach((e) => {
      map[e.framework] = (map[e.framework] || 0) + 1;
    });
    return Object.entries(map).map(([framework, count]) => ({ framework, count }));
  }, []);

  return (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className="bg-card border border-border rounded-lg p-5 hover:border-primary/30 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground font-medium">{kpi.label}</p>
                <p className={`text-2xl font-bold ${kpi.color}`}>{kpi.value}</p>
              </div>
              <div className={`p-2.5 rounded-lg ${kpi.bg}`}>
                <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Evidence by Framework */}
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Evidence by Framework</h3>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={frameworkCounts} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid {...GRID_PROPS} />
                <XAxis {...AXIS_PROPS} dataKey="framework" />
                <YAxis {...AXIS_PROPS} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }} />
                <defs>
                  <linearGradient id="evidenceBarGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={CHART_THEME.primary} stopOpacity={1} />
                    <stop offset="100%" stopColor={CHART_THEME.primary} stopOpacity={0.55} />
                  </linearGradient>
                </defs>
                <Bar dataKey="count" fill="url(#evidenceBarGradient)" radius={[4, 4, 0, 0]} maxBarSize={48} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center gap-4 mt-3 justify-center">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: CHART_THEME.primary }} />
              <span className="text-[11px] text-muted-foreground">Evidence count per framework</span>
            </div>
          </div>
        </div>

        {/* Evidence Trend */}
        <div className="bg-card border border-border rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Evidence Trend</h3>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={evidenceTrendData} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid {...GRID_PROPS} />
                <XAxis {...AXIS_PROPS} dataKey="week" />
                <YAxis {...AXIS_PROPS} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ stroke: CHART_THEME.grid, strokeWidth: 1 }} />
                <Line type="monotone" dataKey="validated" name="Validated" stroke={CHART_THEME.success} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.success }} />
                <Line type="monotone" dataKey="pending" name="Pending" stroke={CHART_THEME.warning} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.warning }} />
                <Line type="monotone" dataKey="expired" name="Expired" stroke={CHART_THEME.danger} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.danger }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="flex items-center gap-4 mt-3 justify-center">
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-success" />
              <span className="text-[11px] text-muted-foreground">Validated</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-warning" />
              <span className="text-[11px] text-muted-foreground">Pending</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-danger" />
              <span className="text-[11px] text-muted-foreground">Expired</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ===================== TAB 2: Evidence Repository =====================
const EVIDENCE_EXPORT_HEADERS = [
  'id',
  'asset',
  'source',
  'framework',
  'controlRef',
  'evidenceType',
  'validationStatus',
  'timestamp',
  'confidenceScore',
  'owner',
  'immutableHash',
] as const;

function EvidenceRepository({ onSelect }: { onSelect: (evidence: Evidence) => void }) {
  const { toast } = useToast();
  const [search, setSearch] = useState('');
  const [frameworkFilter, setFrameworkFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  // Simulate initial data fetch for a premium perceived-loading experience.
  // The loading state only applies on initial mount — filter changes do not
  // re-trigger the skeleton.
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 500);
    return () => clearTimeout(timer);
  }, []);

  const uniqueFrameworks = useMemo(() => {
    const set = new Set(evidenceItems.map((e) => e.framework));
    return Array.from(set);
  }, []);

  const filtered = useMemo(() => {
    return evidenceItems.filter((e) => {
      const q = search.toLowerCase();
      const matchSearch =
        !q ||
        e.asset.toLowerCase().includes(q) ||
        e.framework.toLowerCase().includes(q) ||
        e.controlRef.toLowerCase().includes(q) ||
        e.id.toLowerCase().includes(q);
      const matchFramework = frameworkFilter === 'all' || e.framework === frameworkFilter;
      const matchStatus = statusFilter === 'all' || e.validationStatus === statusFilter;
      return matchSearch && matchFramework && matchStatus;
    });
  }, [search, frameworkFilter, statusFilter]);

  function handleExportCSV() {
    if (!filtered.length) {
      toast({
        title: 'Nothing to export',
        description: 'No evidence items match the current filters.',
      });
      return;
    }
    const filename = `cybreach_evidence_${timestampForFilename()}`;
    exportToCSV(
      filtered as unknown as Record<string, unknown>[],
      filename,
      [...EVIDENCE_EXPORT_HEADERS],
    );
    toast({
      title: 'Export successful',
      description: `Exported ${filtered.length} evidence item${filtered.length === 1 ? '' : 's'} to CSV.`,
    });
  }

  function handleExportJSON() {
    if (!filtered.length) {
      toast({
        title: 'Nothing to export',
        description: 'No evidence items match the current filters.',
      });
      return;
    }
    const filename = `cybreach_evidence_${timestampForFilename()}`;
    exportToJSON(filtered, filename);
    toast({
      title: 'Export successful',
      description: `Exported ${filtered.length} evidence item${filtered.length === 1 ? '' : 's'} to JSON.`,
    });
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search by asset, framework, control..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8 h-8 text-xs bg-surface border-border"
          />
        </div>
        <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
          <SelectTrigger className="w-[160px] h-8 text-xs" size="sm">
            <SelectValue placeholder="Framework" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Frameworks</SelectItem>
            {uniqueFrameworks.map((fw) => (
              <SelectItem key={fw} value={fw}>
                {fw}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-[160px] h-8 text-xs" size="sm">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="validated">Validated</SelectItem>
            <SelectItem value="pending">Pending</SelectItem>
            <SelectItem value="expired">Expired</SelectItem>
            <SelectItem value="rejected">Rejected</SelectItem>
          </SelectContent>
        </Select>
        {/* Export */}
        <div className="sm:ml-auto">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" className="h-8 text-xs gap-1.5">
                <Download className="h-3.5 w-3.5" />
                Export
                <ChevronDown className="h-3 w-3 opacity-70" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-48">
              <DropdownMenuLabel className="text-[11px] text-muted-foreground">
                Export {filtered.length} item{filtered.length === 1 ? '' : 's'}
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleExportCSV} className="text-xs gap-2 cursor-pointer">
                <FileSpreadsheet className="h-3.5 w-3.5 text-success" />
                Export as CSV
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleExportJSON} className="text-xs gap-2 cursor-pointer">
                <FileJson className="h-3.5 w-3.5 text-warning" />
                Export as JSON
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Table */}
      {loading ? (
        <TableSkeleton rows={6} columns={11} />
      ) : (
        <>
        <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="max-h-[520px] overflow-y-auto custom-scrollbar">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-[11px] text-muted-foreground">Evidence ID</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Asset</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Source</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Framework</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Control Ref</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Type</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Status</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Confidence</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Timestamp</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Owner</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Hash</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((item) => (
                <TableRow
                  key={item.id}
                  className="cursor-pointer hover:bg-primary/5 transition-colors"
                  onClick={() => onSelect(item)}
                >
                  <TableCell className="text-xs font-mono text-primary">{item.id}</TableCell>
                  <TableCell className="text-xs text-foreground max-w-[160px] truncate">{item.asset}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{item.source}</TableCell>
                  <TableCell className="text-xs text-foreground">{item.framework}</TableCell>
                  <TableCell className="text-xs font-mono text-foreground">{item.controlRef}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border ${getEvidenceTypeBg(item.evidenceType)}`}>
                      {getEvidenceTypeLabel(item.evidenceType)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border ${getValidationStatusColor(item.validationStatus)}`}>
                      {getValidationStatusLabel(item.validationStatus)}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${
                            item.confidenceScore >= 0.8
                              ? 'bg-success'
                              : item.confidenceScore >= 0.6
                              ? 'bg-warning'
                              : item.confidenceScore > 0
                              ? 'bg-danger'
                              : 'bg-muted-foreground'
                          }`}
                          style={{ width: `${item.confidenceScore * 100}%` }}
                        />
                      </div>
                      <span className={`text-[10px] font-mono ${getScoreColor(item.confidenceScore * 100)}`}>
                        {item.confidenceScore > 0 ? `${Math.round(item.confidenceScore * 100)}%` : '—'}
                      </span>
                    </div>
                  </TableCell>
                  <TableCell className="text-[11px] text-muted-foreground whitespace-nowrap">{formatDateTime(item.timestamp)}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{item.owner}</TableCell>
                  <TableCell className="text-[10px] font-mono text-muted-foreground">{truncateHash(item.immutableHash)}</TableCell>
                </TableRow>
              ))}
              {filtered.length === 0 && (
                <TableRow>
                  <TableCell colSpan={11} className="text-center py-8 text-muted-foreground text-xs">
                    No evidence items match the current filters.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </div>
      <p className="text-[11px] text-muted-foreground">
        Showing {filtered.length} of {evidenceItems.length} evidence items
      </p>
        </>
      )}
    </div>
  );
}

// ===================== TAB 3: Evidence Timeline =====================
function EvidenceTimeline() {
  return (
    <div className="space-y-6">
      {evidenceItems.map((item) => (
        <div key={item.id} className="bg-card border border-border rounded-lg p-4">
          {/* Evidence header */}
          <div className="flex items-center gap-3 mb-4">
            <div className="p-1.5 rounded-md bg-primary/10">
              <FileSearch className="h-3.5 w-3.5 text-primary" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-mono font-semibold text-primary">{item.id}</span>
                <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border ${getValidationStatusColor(item.validationStatus)}`}>
                  {getValidationStatusLabel(item.validationStatus)}
                </Badge>
              </div>
              <p className="text-[11px] text-muted-foreground mt-0.5">
                {item.asset} &middot; {item.framework} &middot; {item.controlRef}
              </p>
            </div>
          </div>

          {/* Audit trail timeline */}
          <div className="relative ml-2">
            {/* Vertical line */}
            <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />

            <div className="space-y-0">
              {item.auditTrail.map((event, idx) => (
                <div key={event.id} className="relative flex gap-3 pb-4 last:pb-0">
                  {/* Dot */}
                  <div className="relative z-10 mt-1.5 shrink-0">
                    <div className={`w-3.5 h-3.5 rounded-full border-2 border-card ${getAuditStatusColor(event.status)}`} />
                  </div>

                  {/* Event card */}
                  <div className="flex-1 bg-surface border border-border/50 rounded-md p-3 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1.5">
                      <span className="text-[11px] text-muted-foreground whitespace-nowrap">
                        {formatDateTime(event.timestamp)}
                      </span>
                      <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border ${getAuditStatusBg(event.status)}`}>
                        {event.status}
                      </Badge>
                      <Badge variant="outline" className="text-[10px] px-1.5 py-0 border bg-muted text-muted-foreground border-muted-foreground/30">
                        {event.module}
                      </Badge>
                    </div>
                    <p className="text-xs text-foreground mb-1.5">{event.description}</p>
                    <div className="flex items-center gap-4 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <User className="h-3 w-3" />
                        {event.actor}
                      </span>
                      <span className="flex items-center gap-1">
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
      ))}
    </div>
  );
}

// ===================== TAB 4: Missing Evidence =====================
function MissingEvidenceTab() {
  const missing = missingEvidenceItems.filter((m) => m.issue === 'missing').length;
  const expired = missingEvidenceItems.filter((m) => m.issue === 'expired').length;
  const weak = missingEvidenceItems.filter((m) => m.issue === 'weak').length;
  const duplicate = missingEvidenceItems.filter((m) => m.issue === 'duplicate').length;

  const summaryCards = [
    { label: 'Missing', value: missing, icon: AlertTriangle, color: 'text-danger', bg: 'bg-danger/10' },
    { label: 'Expired', value: expired, icon: Clock, color: 'text-warning', bg: 'bg-warning/10' },
    { label: 'Weak', value: weak, icon: ShieldCheck, color: 'text-orange-400', bg: 'bg-orange-500/10' },
    { label: 'Duplicate', value: duplicate, icon: GitBranch, color: 'text-purple-400', bg: 'bg-purple-500/10' },
  ];

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {summaryCards.map((card) => (
          <div
            key={card.label}
            className="bg-card border border-border rounded-lg p-5 hover:border-primary/30 transition-colors"
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground font-medium">{card.label}</p>
                <p className={`text-2xl font-bold ${card.color}`}>{card.value}</p>
              </div>
              <div className={`p-2.5 rounded-lg ${card.bg}`}>
                <card.icon className={`h-4 w-4 ${card.color}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Missing Evidence Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <div className="max-h-[420px] overflow-y-auto custom-scrollbar">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-[11px] text-muted-foreground">Control Ref</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Control Title</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Framework</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Issue Type</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Severity</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Remediation</TableHead>
                <TableHead className="text-[11px] text-muted-foreground">Due Date</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {missingEvidenceItems.map((item) => (
                <TableRow
                  key={`${item.controlId}-${item.issue}`}
                  className="cursor-pointer hover:bg-primary/5 transition-colors"
                >
                  <TableCell className="text-xs font-mono text-foreground">{item.controlRef}</TableCell>
                  <TableCell className="text-xs text-foreground max-w-[180px] truncate">{item.controlTitle}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">{item.framework}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border capitalize ${getIssueTypeBg(item.issue)}`}>
                      {item.issue}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-[10px] px-1.5 py-0 border ${getRiskLevelBg(item.severity)}`}>
                      {getRiskLevelLabel(item.severity)}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground max-w-[240px] truncate">{item.remediation}</TableCell>
                  <TableCell className="text-[11px] text-muted-foreground whitespace-nowrap">
                    <span className="flex items-center gap-1">
                      <CalendarClock className="h-3 w-3" />
                      {item.dueDate}
                    </span>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}

// ===================== MAIN COMPONENT =====================
export function EvidenceSection() {
  const [selectedEvidence, setSelectedEvidenceState] = useState<Evidence | null>(null);
  const addRecent = useRecentlyViewedStore((s) => s.addRecent);

  const setSelectedEvidence = (evidence: Evidence | null) => {
    setSelectedEvidenceState(evidence);
    if (evidence) {
      addRecent({
        id: evidence.id,
        type: 'evidence',
        title: evidence.id,
        subtitle: evidence.asset,
        section: 'evidence',
      });
    }
  };

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">Evidence Aggregator</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Manage, validate, and audit compliance evidence across frameworks
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="bg-muted/50">
          <TabsTrigger value="dashboard" className="text-xs gap-1.5">
            <Activity className="h-3.5 w-3.5" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="repository" className="text-xs gap-1.5">
            <Database className="h-3.5 w-3.5" />
            Repository
          </TabsTrigger>
          <TabsTrigger value="timeline" className="text-xs gap-1.5">
            <GitBranch className="h-3.5 w-3.5" />
            Timeline
          </TabsTrigger>
          <TabsTrigger value="missing" className="text-xs gap-1.5">
            <AlertOctagon className="h-3.5 w-3.5" />
            Missing Evidence
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <EvidenceDashboard />
        </TabsContent>
        <TabsContent value="repository">
          <EvidenceRepository onSelect={setSelectedEvidence} />
        </TabsContent>
        <TabsContent value="timeline">
          <EvidenceTimeline />
        </TabsContent>
        <TabsContent value="missing">
          <MissingEvidenceTab />
        </TabsContent>
      </Tabs>

      <EvidenceDetailDrawer
        evidence={selectedEvidence}
        open={!!selectedEvidence}
        onOpenChange={(open) => !open && setSelectedEvidence(null)}
      />
    </div>
  );
}
