'use client';

import React, { useState, useMemo } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import {
  Shield,
  AlertTriangle,
  TrendingUp,
  ArrowUp,
  ArrowRight,
  ArrowDown,
  Search,
  Activity,
  Target,
  BarChart3,
  FileWarning,
  GitBranch,
  Eye,
  Clock,
} from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  risks,
  resilienceScore,
  gapAnalysis,
  riskDistributionData,
  frameworkCoverageData,
  departmentResilienceData,
} from '@/lib/assurance/mock-data';
import { getRiskLevelBg, getRiskLevelLabel, getScoreColor } from '@/lib/assurance/utils';
import { CHART_THEME, AXIS_PROPS, GRID_PROPS } from '@/lib/assurance/chart-theme';
import type { RiskLevel, Risk } from '@/lib/assurance/types';
import { useRecentlyViewedStore } from '@/hooks/use-recently-viewed';
import { RiskDetailDrawer } from './RiskDetailDrawer';

// ─── Brighter color overrides for risk distribution segments ────────────
// Replaces the muted gray "Negligible" segment that blends with the dark background.
const riskSegmentColors: Record<string, string> = {
  Critical: CHART_THEME.danger,
  High: CHART_THEME.warning,
  Medium: CHART_THEME.primary,
  Low: CHART_THEME.success,
  Negligible: CHART_THEME.cyan,
};

// ─── Circular Gauge ─────────────────────────────────────────────────────
function CircularGauge({ score, size = 120 }: { score: number; size?: number }) {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;
  const color =
    score >= 80 ? CHART_THEME.success : score >= 60 ? CHART_THEME.warning : CHART_THEME.danger;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg viewBox="0 0 100 100" className="transform -rotate-90 w-full h-full">
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-muted/30"
        />
        <circle
          cx="50"
          cy="50"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="8"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          className="transition-all duration-700"
        />
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-2xl font-bold"
        style={{ color }}
      >
        {score}
      </span>
    </div>
  );
}

// ─── Likelihood/Impact Dots ─────────────────────────────────────────────
function ScaleDots({ value, max = 5 }: { value: number; max?: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={`w-2 h-2 rounded-full ${
            i < value ? 'bg-primary' : 'bg-muted/40'
          }`}
        />
      ))}
    </div>
  );
}

// ─── Mini Progress Bar ──────────────────────────────────────────────────
function MiniProgress({ value, max = 100 }: { value: number; max?: number }) {
  const pct = Math.min((value / max) * 100, 100);
  const color =
    pct >= 80 ? 'bg-success' : pct >= 50 ? 'bg-warning' : 'bg-danger';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-[10px] text-muted-foreground w-8 text-right">{value}%</span>
    </div>
  );
}

// ─── Recharts custom tooltip ────────────────────────────────────────────
function ChartTooltip({ active, payload, label }: { active?: boolean; payload?: Array<{ name: string; value: number; color: string }>; label?: string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-card border border-border rounded-lg px-3 py-2 shadow-lg text-xs">
      {label && <p className="text-muted-foreground mb-1">{label}</p>}
      {payload.map((p, i) => (
        <p key={i} className="flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="text-foreground font-medium">{p.name}:</span>
          <span className="text-foreground">{p.value}</span>
        </p>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 1: Risk Dashboard
// ═══════════════════════════════════════════════════════════════════════

// Compliance Heatmap data — Department × Framework (deterministic mock)
const heatmapFrameworks = ['ISO 27001', 'GDPR', 'NIST CSF', 'DPDP', 'PCI-DSS'] as const;
const heatmapData: { department: string; scores: Record<string, number> }[] = [
  { department: 'Engineering', scores: { 'ISO 27001': 85, GDPR: 88, 'NIST CSF': 82, DPDP: 70, 'PCI-DSS': 75 } },
  { department: 'Finance', scores: { 'ISO 27001': 78, GDPR: 82, 'NIST CSF': 72, DPDP: 60, 'PCI-DSS': 68 } },
  { department: 'Operations', scores: { 'ISO 27001': 72, GDPR: 76, 'NIST CSF': 68, DPDP: 55, 'PCI-DSS': 62 } },
  { department: 'Legal', scores: { 'ISO 27001': 82, GDPR: 90, 'NIST CSF': 75, DPDP: 78, 'PCI-DSS': 65 } },
  { department: 'HR', scores: { 'ISO 27001': 70, GDPR: 85, 'NIST CSF': 65, DPDP: 58, 'PCI-DSS': 50 } },
  { department: 'Marketing', scores: { 'ISO 27001': 65, GDPR: 80, 'NIST CSF': 60, DPDP: 52, 'PCI-DSS': 45 } },
];

function RiskDashboard() {
  const kpis = [
    {
      label: 'Overall Resilience',
      value: resilienceScore.overall,
      sub: 'Composite score',
      icon: Shield,
      color: getScoreColor(resilienceScore.overall),
      bg: resilienceScore.overall >= 80 ? 'bg-success/10' : resilienceScore.overall >= 60 ? 'bg-warning/10' : 'bg-danger/10',
      gauge: true,
    },
    {
      label: 'Compliance Score',
      value: resilienceScore.compliance,
      sub: 'Framework compliance',
      icon: Target,
      color: getScoreColor(resilienceScore.compliance),
      bg: resilienceScore.compliance >= 80 ? 'bg-success/10' : resilienceScore.compliance >= 60 ? 'bg-warning/10' : 'bg-danger/10',
    },
    {
      label: 'Risk Score',
      value: resilienceScore.risk,
      sub: 'Risk posture',
      icon: AlertTriangle,
      color: getScoreColor(resilienceScore.risk),
      bg: resilienceScore.risk >= 80 ? 'bg-success/10' : resilienceScore.risk >= 60 ? 'bg-warning/10' : 'bg-danger/10',
    },
    {
      label: 'Open / Critical Risks',
      value: `${resilienceScore.openRisks} / ${resilienceScore.criticalRisks}`,
      sub: 'Active risk items',
      icon: Activity,
      color: resilienceScore.criticalRisks > 3 ? 'text-danger' : 'text-warning',
      bg: resilienceScore.criticalRisks > 3 ? 'bg-danger/10' : 'bg-warning/10',
    },
  ];

  return (
    <div className="space-y-4">
      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpis.map((kpi) => (
          <Card
            key={kpi.label}
            className="bg-card border-border hover:border-primary/30 transition-colors py-5"
          >
            <CardContent className="flex items-center gap-4 px-5">
              {kpi.gauge ? (
                <CircularGauge score={kpi.value as number} size={90} />
              ) : (
                <div className={`p-3 rounded-lg ${kpi.bg}`}>
                  <kpi.icon className={`h-5 w-5 ${kpi.color}`} />
                </div>
              )}
              <div className="space-y-0.5 min-w-0">
                <p className="text-[11px] text-muted-foreground font-medium">{kpi.label}</p>
                {!kpi.gauge && (
                  <p className={`text-xl font-bold ${kpi.color}`}>{kpi.value}</p>
                )}
                <p className="text-[10px] text-muted-foreground">{kpi.sub}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Row 2: Resilience Trend + Risk Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Resilience Trend */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Resilience Trend</CardTitle>
            <CardDescription className="text-[11px]">
              Historical resilience score over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={resilienceScore.history}>
                  <CartesianGrid {...GRID_PROPS} />
                  <XAxis {...AXIS_PROPS} dataKey="date" />
                  <YAxis {...AXIS_PROPS} domain={[0, 100]} />
                  <Tooltip content={<ChartTooltip />} cursor={{ stroke: CHART_THEME.grid, strokeWidth: 1 }} />
                  <Line
                    type="monotone"
                    dataKey="score"
                    name="Resilience"
                    stroke={CHART_THEME.primary}
                    strokeWidth={2}
                    dot={{ fill: CHART_THEME.primary, r: 3 }}
                    activeDot={{ r: 5 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Risk Distribution */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Risk Distribution</CardTitle>
            <CardDescription className="text-[11px]">
              Breakdown of risks by severity level
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                    nameKey="name"
                    stroke={CHART_THEME.tooltipBg}
                    strokeWidth={2}
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={riskSegmentColors[entry.name] || entry.color} />
                    ))}
                  </Pie>
                  <Tooltip content={<ChartTooltip />} />
                  <Legend
                    iconType="circle"
                    iconSize={8}
                    wrapperStyle={{ fontSize: 11, color: CHART_THEME.axis }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Row 3: Framework Coverage + Department Resilience */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Framework Coverage */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Framework Coverage</CardTitle>
            <CardDescription className="text-[11px]">
              Current coverage vs. target per framework
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={frameworkCoverageData} layout="vertical">
                  <CartesianGrid {...GRID_PROPS} horizontal={false} />
                  <XAxis {...AXIS_PROPS} type="number" domain={[0, 100]} />
                  <YAxis
                    {...AXIS_PROPS}
                    type="category"
                    dataKey="framework"
                    width={75}
                  />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: CHART_THEME.axis }} />
                  <Bar dataKey="coverage" name="Coverage" fill={CHART_THEME.primary} radius={[0, 4, 4, 0]} barSize={14} />
                  <Bar dataKey="target" name="Target" fill={CHART_THEME.muted} radius={[0, 4, 4, 0]} barSize={14} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Department Resilience */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Department Resilience</CardTitle>
            <CardDescription className="text-[11px]">
              Resilience score by department
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={departmentResilienceData}>
                  <CartesianGrid {...GRID_PROPS} />
                  <XAxis {...AXIS_PROPS} dataKey="department" />
                  <YAxis {...AXIS_PROPS} domain={[0, 100]} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }} />
                  <Bar dataKey="score" name="Score" radius={[4, 4, 0, 0]} barSize={28}>
                    {departmentResilienceData.map((entry, index) => (
                      <Cell
                        key={`dept-${index}`}
                        fill={
                          entry.score >= 80
                            ? CHART_THEME.success
                            : entry.score >= 60
                            ? CHART_THEME.warning
                            : CHART_THEME.danger
                        }
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Compliance Heatmap by Department × Framework */}
      <div className="bg-card border border-border rounded-xl p-5">
        <div className="flex items-center justify-between mb-4 gap-3 flex-wrap">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Compliance Heatmap</h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">Department × Framework compliance matrix</p>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-success/40" /> ≥80%</span>
            <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-warning/40" /> 60-79%</span>
            <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-danger/40" /> &lt;60%</span>
          </div>
        </div>
        <div className="overflow-x-auto">
          <div className="min-w-[560px] max-w-4xl">
            {/* Header row */}
            <div className="grid grid-cols-[120px_repeat(5,1fr)] gap-1.5 mb-1.5">
              <div />
              {heatmapFrameworks.map((fw) => (
                <div key={fw} className="text-[10px] text-muted-foreground text-center font-medium truncate" title={fw}>
                  {fw}
                </div>
              ))}
            </div>
            {/* Department rows */}
            {heatmapData.map((row) => (
              <div key={row.department} className="grid grid-cols-[120px_repeat(5,1fr)] gap-1.5 mb-1.5">
                <div className="text-xs font-medium text-foreground flex items-center justify-end pr-2">
                  {row.department}
                </div>
                {heatmapFrameworks.map((fw) => {
                  const score = row.scores[fw];
                  const cellClass =
                    score >= 80
                      ? 'bg-success/30 text-success'
                      : score >= 60
                      ? 'bg-warning/30 text-warning'
                      : 'bg-danger/30 text-danger';
                  return (
                    <div
                      key={fw}
                      className={`min-h-[48px] rounded-md flex items-center justify-center text-xs font-bold cursor-default transition-transform hover:scale-105 hover:ring-2 hover:ring-foreground/20 ${cellClass}`}
                      title={`${row.department} · ${fw}: ${score}%`}
                    >
                      {score}%
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 2: Risk Explorer
// ═══════════════════════════════════════════════════════════════════════
function RiskExplorer({ onSelect }: { onSelect: (risk: Risk) => void }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [frameworkFilter, setFrameworkFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const uniqueFrameworks = useMemo(
    () => Array.from(new Set(risks.map((r) => r.framework))),
    []
  );

  const filteredRisks = useMemo(() => {
    return risks.filter((r) => {
      if (searchQuery && !r.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
      if (severityFilter !== 'all' && r.severity !== severityFilter) return false;
      if (frameworkFilter !== 'all' && r.framework !== frameworkFilter) return false;
      if (statusFilter !== 'all' && r.status !== statusFilter) return false;
      return true;
    });
  }, [searchQuery, severityFilter, frameworkFilter, statusFilter]);

  function TrendIcon({ trend }: { trend: Risk['trend'] }) {
    switch (trend) {
      case 'increasing':
        return <ArrowUp className="h-3.5 w-3.5 text-danger" />;
      case 'decreasing':
        return <ArrowDown className="h-3.5 w-3.5 text-success" />;
      default:
        return <ArrowRight className="h-3.5 w-3.5 text-muted-foreground" />;
    }
  }

  function StatusBadge({ status }: { status: Risk['status'] }) {
    const styles: Record<string, string> = {
      open: 'bg-danger/15 text-danger border-danger/30',
      mitigated: 'bg-success/15 text-success border-success/30',
      accepted: 'bg-warning/15 text-warning border-warning/30',
      closed: 'bg-muted text-muted-foreground border-muted-foreground/30',
    };
    return (
      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${styles[status] || ''}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <Card className="bg-card border-border">
        <CardContent className="py-3">
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Search risks by title..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-8 h-8 text-xs"
              />
            </div>
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger size="sm" className="w-[130px] text-xs">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="negligible">Negligible</SelectItem>
              </SelectContent>
            </Select>
            <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
              <SelectTrigger size="sm" className="w-[140px] text-xs">
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
              <SelectTrigger size="sm" className="w-[120px] text-xs">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="open">Open</SelectItem>
                <SelectItem value="mitigated">Mitigated</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
            <span className="text-[11px] text-muted-foreground">
              {filteredRisks.length} risk{filteredRisks.length !== 1 ? 's' : ''}
            </span>
          </div>
        </CardContent>
      </Card>

      {/* Table */}
      <Card className="bg-card border-border overflow-hidden">
        <CardContent className="p-0">
          <div className="max-h-[520px] overflow-y-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="text-[11px] h-9">Risk ID</TableHead>
                  <TableHead className="text-[11px]">Title</TableHead>
                  <TableHead className="text-[11px]">Severity</TableHead>
                  <TableHead className="text-[11px]">Likelihood</TableHead>
                  <TableHead className="text-[11px]">Impact</TableHead>
                  <TableHead className="text-[11px]">Framework</TableHead>
                  <TableHead className="text-[11px] text-center">Evidence</TableHead>
                  <TableHead className="text-[11px] min-w-[120px]">Residual Risk</TableHead>
                  <TableHead className="text-[11px] text-center">Trend</TableHead>
                  <TableHead className="text-[11px]">Status</TableHead>
                  <TableHead className="text-[11px]">Owner</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredRisks.map((risk) => (
                  <TableRow key={risk.id} className="cursor-pointer hover:bg-primary/5" onClick={() => onSelect(risk)}>
                    <TableCell className="text-[11px] font-mono text-muted-foreground">
                      {risk.id}
                    </TableCell>
                    <TableCell className="text-xs font-medium max-w-[200px] truncate">
                      {risk.title}
                    </TableCell>
                    <TableCell>
                      <span
                        className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${getRiskLevelBg(
                          risk.severity as RiskLevel
                        )}`}
                      >
                        {getRiskLevelLabel(risk.severity as RiskLevel)}
                      </span>
                    </TableCell>
                    <TableCell>
                      <ScaleDots value={risk.likelihood} />
                    </TableCell>
                    <TableCell>
                      <ScaleDots value={risk.impact} />
                    </TableCell>
                    <TableCell className="text-[11px] text-muted-foreground">
                      {risk.framework}
                    </TableCell>
                    <TableCell className="text-[11px] text-center text-muted-foreground">
                      {risk.evidenceCount}
                    </TableCell>
                    <TableCell>
                      <MiniProgress value={risk.residualRisk} />
                    </TableCell>
                    <TableCell className="text-center">
                      <TrendIcon trend={risk.trend} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={risk.status} />
                    </TableCell>
                    <TableCell className="text-[11px] text-muted-foreground">
                      {risk.owner}
                    </TableCell>
                  </TableRow>
                ))}
                {filteredRisks.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={11} className="text-center text-xs text-muted-foreground py-8">
                      No risks found matching filters
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 3: Resilience Calculator
// ═══════════════════════════════════════════════════════════════════════
function ResilienceCalculator() {
  const formula = resilienceScore.formula;

  const factors = [
    { key: 'evidenceConfidence', label: 'Evidence Confidence', value: formula.evidenceConfidence, weight: 0.30, color: CHART_THEME.primary },
    { key: 'controlWeight', label: 'Control Weight', value: formula.controlWeight, weight: 0.25, color: CHART_THEME.success },
    { key: 'frameworkWeight', label: 'Framework Weight', value: formula.frameworkWeight, weight: 0.25, color: CHART_THEME.warning },
    { key: 'riskWeight', label: 'Risk Weight', value: formula.riskWeight, weight: 0.25, color: CHART_THEME.danger },
    { key: 'businessImpact', label: 'Business Impact', value: formula.businessImpact, weight: 0.20, color: CHART_THEME.purple },
  ];

  return (
    <div className="space-y-4">
      {/* Overall Score + Formula */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Score Display */}
        <Card className="bg-card border-border flex flex-col items-center justify-center py-6">
          <CardContent className="flex flex-col items-center">
            <CircularGauge score={resilienceScore.overall} size={140} />
            <p className="text-sm font-semibold text-foreground mt-3">Overall Resilience Score</p>
            <p className="text-[11px] text-muted-foreground mt-1">
              Weighted composite across all factors
            </p>
          </CardContent>
        </Card>

        {/* Formula Breakdown */}
        <Card className="bg-card border-border lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <GitBranch className="h-4 w-4 text-primary" />
              Score Formula
            </CardTitle>
            <CardDescription className="text-[11px]">
              Score = (Evidence Confidence &times; 0.30) + (Control Weight &times; 0.25) + (Framework
              Weight &times; 0.25) + (Risk Weight &times; 0.25) + (Business Impact &times; 0.20)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {factors.map((f) => {
                const contribution = Math.round(f.value * f.weight * 100);
                return (
                  <div key={f.key} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span
                          className="w-2.5 h-2.5 rounded-full"
                          style={{ background: f.color }}
                        />
                        <span className="text-xs font-medium text-foreground">{f.label}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[10px] text-muted-foreground">
                          Value: {f.value.toFixed(2)}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          Weight: {(f.weight * 100).toFixed(0)}%
                        </span>
                        <span
                          className="text-xs font-semibold"
                          style={{ color: f.color }}
                        >
                          +{contribution}
                        </span>
                      </div>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${f.value * 100}%`,
                          background: f.color,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Historical Trend */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-primary" />
            Resilience Trend History
          </CardTitle>
          <CardDescription className="text-[11px]">
            Monthly resilience score progression
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={resilienceScore.history}>
                <CartesianGrid {...GRID_PROPS} />
                <XAxis {...AXIS_PROPS} dataKey="date" />
                <YAxis {...AXIS_PROPS} domain={[0, 100]} />
                <Tooltip content={<ChartTooltip />} cursor={{ stroke: CHART_THEME.grid, strokeWidth: 1 }} />
                <Line
                  type="monotone"
                  dataKey="score"
                  name="Resilience"
                  stroke={CHART_THEME.primary}
                  strokeWidth={2}
                  dot={{ fill: CHART_THEME.primary, r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Sub-scores */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: 'Compliance', value: resilienceScore.compliance, icon: Target },
          { label: 'Control Coverage', value: resilienceScore.controlCoverage, icon: Shield },
          { label: 'Evidence Coverage', value: resilienceScore.evidenceCoverage, icon: Eye },
          { label: 'Risk Posture', value: resilienceScore.risk, icon: AlertTriangle },
        ].map((s) => (
          <Card key={s.label} className="bg-card border-border hover:border-primary/30 transition-colors py-5">
            <CardContent className="flex items-center gap-3 px-5">
              <div className={`p-2.5 rounded-lg ${s.value >= 80 ? 'bg-success/10' : s.value >= 60 ? 'bg-warning/10' : 'bg-danger/10'}`}>
                <s.icon className={`h-4 w-4 ${getScoreColor(s.value)}`} />
              </div>
              <div>
                <p className="text-[11px] text-muted-foreground">{s.label}</p>
                <p className={`text-lg font-bold ${getScoreColor(s.value)}`}>{s.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 4: Gap Analysis
// ═══════════════════════════════════════════════════════════════════════
function GapAnalysisTab() {
  const summaryCards = [
    {
      label: 'Missing Controls',
      value: gapAnalysis.missingControls.length,
      icon: FileWarning,
      color: 'text-danger',
      bg: 'bg-danger/10',
      sub: 'No evidence linked',
    },
    {
      label: 'Weak Controls',
      value: gapAnalysis.weakControls.length,
      icon: AlertTriangle,
      color: 'text-warning',
      bg: 'bg-warning/10',
      sub: 'Insufficient evidence',
    },
    {
      label: 'High Risk Areas',
      value: gapAnalysis.highRiskAreas.length,
      icon: Target,
      color: 'text-cyber',
      bg: 'bg-cyber/10',
      sub: 'Concentration of risks',
    },
  ];

  const evidenceGapChartData = gapAnalysis.evidenceGaps.map((eg) => ({
    framework: eg.framework,
    present: eg.total - eg.missing,
    missing: eg.missing,
  }));

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {summaryCards.map((sc) => (
          <Card key={sc.label} className="bg-card border-border hover:border-primary/30 transition-colors py-5">
            <CardContent className="flex items-center gap-3 px-5">
              <div className={`p-2.5 rounded-lg ${sc.bg}`}>
                <sc.icon className={`h-5 w-5 ${sc.color}`} />
              </div>
              <div>
                <p className="text-[11px] text-muted-foreground">{sc.label}</p>
                <p className={`text-xl font-bold ${sc.color}`}>{sc.value}</p>
                <p className="text-[10px] text-muted-foreground">{sc.sub}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Framework Gaps + Evidence Gaps */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Framework Gaps */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-primary" />
              Framework Gaps
            </CardTitle>
            <CardDescription className="text-[11px]">
              Gap percentage and description per framework
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {gapAnalysis.frameworkGaps.map((fg) => {
                const color =
                  fg.gap >= 30
                    ? CHART_THEME.danger
                    : fg.gap >= 20
                    ? CHART_THEME.warning
                    : CHART_THEME.success;
                return (
                  <div key={fg.framework} className="space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-medium text-foreground">
                        {fg.framework}
                      </span>
                      <span
                        className="text-xs font-bold"
                        style={{ color }}
                      >
                        {fg.gap}% gap
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${fg.gap}%`,
                          background: color,
                        }}
                      />
                    </div>
                    <p className="text-[10px] text-muted-foreground leading-tight">
                      {fg.description}
                    </p>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Evidence Gaps Chart */}
        <Card className="bg-card border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              Evidence Gaps
            </CardTitle>
            <CardDescription className="text-[11px]">
              Missing vs. present evidence per framework
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-56">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={evidenceGapChartData}>
                  <CartesianGrid {...GRID_PROPS} />
                  <XAxis {...AXIS_PROPS} dataKey="framework" />
                  <YAxis {...AXIS_PROPS} />
                  <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 11, color: CHART_THEME.axis }} />
                  <Bar dataKey="present" name="Present" stackId="a" fill={CHART_THEME.success} radius={[0, 0, 0, 0]} barSize={24} />
                  <Bar dataKey="missing" name="Missing" stackId="a" fill={CHART_THEME.danger} radius={[4, 4, 0, 0]} barSize={24} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* High Risk Areas */}
      <Card className="bg-card border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 text-warning" />
            High Risk Areas
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {gapAnalysis.highRiskAreas.map((hra, i) => (
              <div
                key={i}
                className="p-3 rounded-md bg-surface border border-border/50 hover:border-primary/30 transition-colors"
              >
                <p className="text-xs font-medium text-foreground">{hra.name}</p>
                <p className="text-[11px] text-muted-foreground mt-1">
                  {hra.riskCount} risks &middot; {hra.framework}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Recommendations Table */}
      <Card className="bg-card border-border overflow-hidden">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm flex items-center gap-2">
            <Clock className="h-4 w-4 text-primary" />
            Recommendations
          </CardTitle>
          <CardDescription className="text-[11px]">
            Prioritized remediation actions
          </CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-[11px] h-9">Priority</TableHead>
                <TableHead className="text-[11px]">Title</TableHead>
                <TableHead className="text-[11px]">Impact</TableHead>
                <TableHead className="text-[11px]">Effort</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {gapAnalysis.recommendations.map((rec, i) => (
                <TableRow key={i} className="hover:bg-muted/30">
                  <TableCell>
                    <span
                      className={`text-[10px] font-semibold px-1.5 py-0.5 rounded border ${getRiskLevelBg(
                        rec.priority as RiskLevel
                      )}`}
                    >
                      {getRiskLevelLabel(rec.priority as RiskLevel)}
                    </span>
                  </TableCell>
                  <TableCell className="text-xs font-medium">{rec.title}</TableCell>
                  <TableCell className="text-[11px] text-muted-foreground max-w-[220px]">
                    {rec.impact}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={`text-[10px] ${
                        rec.effort === 'Low'
                          ? 'border-success/30 text-success'
                          : rec.effort === 'Medium'
                          ? 'border-warning/30 text-warning'
                          : 'border-danger/30 text-danger'
                      }`}
                    >
                      {rec.effort}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Main RiskSection Component
// ═══════════════════════════════════════════════════════════════════════
export function RiskSection() {
  const [selectedRisk, setSelectedRiskState] = useState<Risk | null>(null);
  const addRecent = useRecentlyViewedStore((s) => s.addRecent);

  const setSelectedRisk = (risk: Risk | null) => {
    setSelectedRiskState(risk);
    if (risk) {
      addRecent({
        id: risk.id,
        type: 'risk',
        title: risk.title,
        subtitle: risk.id,
        section: 'risk',
      });
    }
  };

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">Risk & Resilience</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Monitor risks, assess resilience, and identify compliance gaps
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="bg-muted/60">
          <TabsTrigger value="dashboard" className="text-xs">
            <Activity className="h-3.5 w-3.5 mr-1.5" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="explorer" className="text-xs">
            <Search className="h-3.5 w-3.5 mr-1.5" />
            Risk Explorer
          </TabsTrigger>
          <TabsTrigger value="calculator" className="text-xs">
            <GitBranch className="h-3.5 w-3.5 mr-1.5" />
            Calculator
          </TabsTrigger>
          <TabsTrigger value="gaps" className="text-xs">
            <FileWarning className="h-3.5 w-3.5 mr-1.5" />
            Gap Analysis
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <RiskDashboard />
        </TabsContent>
        <TabsContent value="explorer">
          <RiskExplorer onSelect={setSelectedRisk} />
        </TabsContent>
        <TabsContent value="calculator">
          <ResilienceCalculator />
        </TabsContent>
        <TabsContent value="gaps">
          <GapAnalysisTab />
        </TabsContent>
      </Tabs>

      <RiskDetailDrawer
        risk={selectedRisk}
        open={!!selectedRisk}
        onOpenChange={(open) => !open && setSelectedRisk(null)}
      />
    </div>
  );
}
