'use client';

import React, { useState, useMemo } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Cell,
  Legend,
} from 'recharts';
import {
  GitCompare,
  Check,
  Shield,
  BarChart3,
  Radar as RadarIcon,
  Layers,
  AlertTriangle,
  Lock,
} from 'lucide-react';
import { frameworks } from '@/lib/assurance/mock-data';
import {
  getFrameworkStatusColor,
  getRiskLevelBg,
  getRiskLevelLabel,
  getScoreColor,
  formatDate,
} from '@/lib/assurance/utils';
import {
  CHART_THEME,
  TOOLTIP_STYLE,
  AXIS_PROPS,
  GRID_PROPS,
} from '@/lib/assurance/chart-theme';
import type { Framework, RiskLevel } from '@/lib/assurance/types';

// ─── Constants ───────────────────────────────────────────────

interface FrameworkComparisonDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const MAX_SELECTION = 3;
const EVIDENCE_BASELINE = 300;

const FRAMEWORK_COLORS: string[] = [
  CHART_THEME.primary,
  CHART_THEME.success,
  CHART_THEME.warning,
  CHART_THEME.danger,
  CHART_THEME.purple,
];

const RISK_SCORES: Record<RiskLevel, number> = {
  critical: 100,
  high: 75,
  medium: 50,
  low: 25,
  negligible: 10,
};

const RADAR_DIMENSIONS = [
  'Compliance',
  'Control Coverage',
  'Evidence Coverage',
  'Risk Inverse',
  'Maturity',
] as const;

// ─── Helpers ─────────────────────────────────────────────────

function riskInverse(level: RiskLevel): number {
  return 100 - RISK_SCORES[level];
}

function evidenceCoverage(linked: number): number {
  return Math.min(100, Math.round((linked / EVIDENCE_BASELINE) * 100));
}

function controlCoverage(fw: Framework): number {
  if (fw.controlsTotal <= 0) return 0;
  return Math.round((fw.controlsCovered / fw.controlsTotal) * 100);
}

function miniBarColor(value: number): string {
  if (value >= 80) return 'bg-success';
  if (value >= 60) return 'bg-warning';
  return 'bg-danger';
}

// ─── Chart Tooltip ───────────────────────────────────────────

function ComparisonTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name: string; value: number; color: string }>;
  label?: string;
}) {
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

// ─── Main Component ──────────────────────────────────────────

export function FrameworkComparisonDialog({
  open,
  onOpenChange,
}: FrameworkComparisonDialogProps) {
  // Default to first 3 frameworks so users see a comparison immediately.
  const [selectedIds, setSelectedIds] = useState<string[]>(
    frameworks.slice(0, 3).map((fw) => fw.id),
  );

  const selectedFrameworks = useMemo<Framework[]>(() => {
    return selectedIds
      .map((id) => frameworks.find((fw) => fw.id === id))
      .filter((fw): fw is Framework => Boolean(fw));
  }, [selectedIds]);

  const colorFor = useMemo(() => {
    const map = new Map<string, string>();
    selectedIds.forEach((id, idx) => {
      map.set(id, FRAMEWORK_COLORS[idx % FRAMEWORK_COLORS.length]);
    });
    return map;
  }, [selectedIds]);

  const toggleFramework = (id: string) => {
    setSelectedIds((prev) => {
      if (prev.includes(id)) {
        return prev.filter((x) => x !== id);
      }
      if (prev.length >= MAX_SELECTION) return prev; // limit reached
      return [...prev, id];
    });
  };

  // Radar chart data — one row per dimension, one column per framework name.
  const radarData = useMemo(() => {
    return RADAR_DIMENSIONS.map((dim) => {
      const row: Record<string, number | string> = { dimension: dim };
      selectedFrameworks.forEach((fw) => {
        let value = 0;
        switch (dim) {
          case 'Compliance':
            value = fw.compliance;
            break;
          case 'Control Coverage':
            value = controlCoverage(fw);
            break;
          case 'Evidence Coverage':
            value = evidenceCoverage(fw.evidenceLinked);
            break;
          case 'Risk Inverse':
            value = riskInverse(fw.riskLevel);
            break;
          case 'Maturity':
            value = fw.compliance;
            break;
        }
        row[fw.name] = value;
      });
      return row;
    });
  }, [selectedFrameworks]);

  // Bar chart data — one row per framework showing compliance %.
  const barData = useMemo(() => {
    return selectedFrameworks.map((fw, idx) => ({
      name: fw.name,
      compliance: fw.compliance,
      color: FRAMEWORK_COLORS[idx % FRAMEWORK_COLORS.length],
    }));
  }, [selectedFrameworks]);

  const hasEnoughSelection = selectedFrameworks.length >= 2;
  const selectionCount = selectedFrameworks.length;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="bg-card border-border max-w-4xl w-[calc(100%-2rem)] sm:w-full p-0 gap-0 max-h-[90vh] flex flex-col"
        showCloseButton
      >
        {/* Header */}
        <DialogHeader className="px-6 pt-6 pb-4 border-b border-border shrink-0">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-lg bg-primary/10 shrink-0">
                <GitCompare className="h-5 w-5 text-primary" />
              </div>
              <div>
                <DialogTitle className="text-base font-semibold text-foreground">
                  Compare Frameworks
                </DialogTitle>
                <DialogDescription className="text-xs mt-1">
                  Side-by-side comparison of up to {MAX_SELECTION} compliance frameworks across
                  key metrics, radar dimensions, and compliance scores.
                </DialogDescription>
              </div>
            </div>
            <Badge
              variant="outline"
              className="shrink-0 text-[11px] px-2 py-0.5 border-border/60 text-muted-foreground"
            >
              {selectionCount} / {MAX_SELECTION} selected
            </Badge>
          </div>
        </DialogHeader>

        {/* Scrollable Body */}
        <div className="flex-1 overflow-y-auto custom-scrollbar px-6 py-5 space-y-6">
          {/* Framework Selector */}
          <section>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-semibold text-foreground uppercase tracking-wide flex items-center gap-1.5">
                <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                Select Frameworks to Compare
              </h3>
              <span className="text-[11px] text-muted-foreground">
                Tap a card to toggle selection
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
              {frameworks.map((fw) => {
                const selected = selectedIds.includes(fw.id);
                const disabled = !selected && selectionCount >= MAX_SELECTION;
                const color = colorFor.get(fw.id);
                return (
                  <button
                    key={fw.id}
                    type="button"
                    onClick={() => toggleFramework(fw.id)}
                    disabled={disabled}
                    aria-pressed={selected}
                    className={[
                      'relative text-left rounded-lg border p-3 transition-all duration-150',
                      'focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/50',
                      selected
                        ? 'bg-primary/15 border-primary shadow-sm'
                        : 'bg-surface border-border hover:border-border/70 hover:bg-surface/60',
                      disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer',
                    ].join(' ')}
                  >
                    {/* Selection indicator */}
                    <div className="flex items-start justify-between mb-1.5">
                      <div
                        className="p-1 rounded-md shrink-0"
                        style={{
                          backgroundColor: selected
                            ? `${color}20`
                            : 'rgba(148, 163, 184, 0.08)',
                        }}
                      >
                        <Shield
                          className="h-3.5 w-3.5"
                          style={{ color: selected ? color : CHART_THEME.axis }}
                        />
                      </div>
                      {selected ? (
                        <span
                          className="flex items-center justify-center h-4 w-4 rounded-full shrink-0"
                          style={{ backgroundColor: color }}
                        >
                          <Check className="h-2.5 w-2.5 text-white" />
                        </span>
                      ) : disabled ? (
                        <Lock className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
                      ) : null}
                    </div>
                    <p className="text-xs font-semibold text-foreground truncate">{fw.name}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      v{fw.version} · {fw.compliance}% compliant
                    </p>
                  </button>
                );
              })}
            </div>
          </section>

          {/* Empty state OR comparison content */}
          {!hasEnoughSelection ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="p-3 rounded-full bg-muted/30 mb-3">
                <GitCompare className="h-6 w-6 text-muted-foreground" />
              </div>
              <p className="text-sm font-medium text-foreground">Select at least 2 frameworks to compare</p>
              <p className="text-xs text-muted-foreground mt-1 max-w-xs">
                Currently {selectionCount} framework{selectionCount === 1 ? '' : 's'} selected. Add
                at least {2 - selectionCount} more to view the comparison.
              </p>
            </div>
          ) : (
            <>
              {/* Comparison Table */}
              <section>
                <h3 className="text-xs font-semibold text-foreground uppercase tracking-wide flex items-center gap-1.5 mb-3">
                  <BarChart3 className="h-3.5 w-3.5 text-muted-foreground" />
                  Metric Comparison
                </h3>
                <div className="bg-card border border-border rounded-lg overflow-hidden">
                  <div className="overflow-x-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="hover:bg-transparent border-border/60">
                          <TableHead className="text-[11px] uppercase tracking-wide text-muted-foreground h-9 px-3 sticky left-0 bg-card z-10 min-w-[120px]">
                            Metric
                          </TableHead>
                          {selectedFrameworks.map((fw) => {
                            const color = colorFor.get(fw.id) || CHART_THEME.primary;
                            return (
                              <TableHead
                                key={fw.id}
                                className="text-[11px] uppercase tracking-wide h-9 px-3 min-w-[180px]"
                                style={{ color }}
                              >
                                <span className="flex items-center gap-1.5">
                                  <span
                                    className="w-1.5 h-1.5 rounded-full shrink-0"
                                    style={{ backgroundColor: color }}
                                  />
                                  {fw.name}
                                </span>
                              </TableHead>
                            );
                          })}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {/* Framework Name + version */}
                        <TableRow className="border-border/40 hover:bg-surface/40">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-card">
                            Framework
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <div className="flex items-center gap-1.5 flex-wrap">
                                <span className="font-semibold text-foreground">{fw.name}</span>
                                <Badge
                                  variant="outline"
                                  className="text-[10px] px-1.5 py-0 border-border/50 text-muted-foreground"
                                >
                                  v{fw.version}
                                </Badge>
                              </div>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Status */}
                        <TableRow className="border-border/40 hover:bg-surface/40 bg-muted/10">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-muted/10">
                            Status
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <Badge
                                variant="outline"
                                className={`text-[10px] px-1.5 py-0 capitalize ${getFrameworkStatusColor(fw.status)}`}
                              >
                                {fw.status}
                              </Badge>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Compliance with mini bar */}
                        <TableRow className="border-border/40 hover:bg-surface/40">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-card">
                            Compliance
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <div className="flex items-center gap-2">
                                <span className={`font-bold text-sm ${getScoreColor(fw.compliance)}`}>
                                  {fw.compliance}%
                                </span>
                                <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden min-w-[60px]">
                                  <div
                                    className={`h-full rounded-full transition-all duration-500 ${miniBarColor(fw.compliance)}`}
                                    style={{ width: `${fw.compliance}%` }}
                                  />
                                </div>
                              </div>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Controls covered / total */}
                        <TableRow className="border-border/40 hover:bg-surface/40 bg-muted/10">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-muted/10">
                            Controls
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <span className="text-foreground font-semibold">{fw.controlsCovered}</span>
                              <span className="text-muted-foreground"> / {fw.controlsTotal}</span>
                              <span className="text-muted-foreground ml-1.5 text-[10px]">
                                ({controlCoverage(fw)}%)
                              </span>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Evidence linked */}
                        <TableRow className="border-border/40 hover:bg-surface/40">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-card">
                            Evidence
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <span className="text-foreground font-semibold">{fw.evidenceLinked}</span>
                              <span className="text-muted-foreground ml-1.5 text-[10px]">
                                ({evidenceCoverage(fw.evidenceLinked)}% cov.)
                              </span>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Risk level */}
                        <TableRow className="border-border/40 hover:bg-surface/40 bg-muted/10">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-muted/10">
                            Risk Level
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <Badge
                                variant="outline"
                                className={`text-[10px] px-1.5 py-0 ${getRiskLevelBg(fw.riskLevel)}`}
                              >
                                {getRiskLevelLabel(fw.riskLevel)}
                              </Badge>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Last synced */}
                        <TableRow className="border-border/40 hover:bg-surface/40">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-card">
                            Last Synced
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs text-muted-foreground px-3 py-2">
                              {formatDate(fw.lastSync)}
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Domains count */}
                        <TableRow className="border-border/40 hover:bg-surface/40 bg-muted/10">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-muted/10">
                            Domains
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell key={fw.id} className="text-xs px-3 py-2">
                              <span className="text-foreground font-semibold">{fw.domains.length}</span>
                              <span className="text-muted-foreground text-[10px] ml-1">domains</span>
                            </TableCell>
                          ))}
                        </TableRow>

                        {/* Description */}
                        <TableRow className="border-border/40 hover:bg-surface/40">
                          <TableCell className="text-[11px] font-medium text-muted-foreground px-3 py-2 sticky left-0 bg-card align-top">
                            Description
                          </TableCell>
                          {selectedFrameworks.map((fw) => (
                            <TableCell
                              key={fw.id}
                              className="text-xs text-muted-foreground px-3 py-2 align-top"
                            >
                              <p className="leading-relaxed">{fw.description}</p>
                            </TableCell>
                          ))}
                        </TableRow>
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </section>

              {/* Charts: Radar + Bar */}
              <section className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {/* Radar Chart */}
                <div className="bg-card border border-border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                        <RadarIcon className="h-3.5 w-3.5 text-primary" />
                        Multi-Dimensional Radar
                      </h4>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        Comparison across {RADAR_DIMENSIONS.length} normalized dimensions
                      </p>
                    </div>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <RadarChart data={radarData} outerRadius="75%">
                        <PolarGrid stroke={CHART_THEME.grid} />
                        <PolarAngleAxis
                          dataKey="dimension"
                          tick={{ fill: CHART_THEME.axis, fontSize: 10 }}
                        />
                        <PolarRadiusAxis
                          angle={90}
                          domain={[0, 100]}
                          tick={{ fill: CHART_THEME.axis, fontSize: 9 }}
                          stroke={CHART_THEME.axisLine}
                          tickCount={5}
                        />
                        {selectedFrameworks.map((fw) => {
                          const color = colorFor.get(fw.id) || CHART_THEME.primary;
                          return (
                            <Radar
                              key={fw.id}
                              name={fw.name}
                              dataKey={fw.name}
                              stroke={color}
                              fill={color}
                              fillOpacity={0.15}
                              strokeWidth={2}
                            />
                          );
                        })}
                        <Tooltip content={<ComparisonTooltip />} />
                        <Legend
                          iconType="circle"
                          iconSize={8}
                          wrapperStyle={{ fontSize: 10, color: CHART_THEME.axis, paddingTop: 8 }}
                        />
                      </RadarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Bar Chart */}
                <div className="bg-card border border-border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h4 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                        <BarChart3 className="h-3.5 w-3.5 text-primary" />
                        Compliance Score Comparison
                      </h4>
                      <p className="text-[10px] text-muted-foreground mt-0.5">
                        Overall compliance percentage by framework
                      </p>
                    </div>
                  </div>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={barData} margin={{ top: 8, right: 8, bottom: 8, left: -16 }}>
                        <CartesianGrid {...GRID_PROPS} />
                        <XAxis
                          {...AXIS_PROPS}
                          dataKey="name"
                          tick={{ fill: CHART_THEME.axis, fontSize: 10 }}
                          interval={0}
                          angle={-15}
                          textAnchor="end"
                          height={48}
                        />
                        <YAxis
                          {...AXIS_PROPS}
                          domain={[0, 100]}
                          tickFormatter={(v: number) => `${v}%`}
                        />
                        <Tooltip
                          content={<ComparisonTooltip />}
                          cursor={{ fill: 'rgba(148, 163, 184, 0.08)' }}
                        />
                        <Bar dataKey="compliance" name="Compliance" radius={[4, 4, 0, 0]} maxBarSize={56}>
                          {barData.map((entry, idx) => (
                            <Cell key={`cell-${idx}`} fill={entry.color} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </section>

              {/* Insight banner */}
              <section className="bg-surface/50 border border-border/60 rounded-lg p-3 flex items-start gap-2.5">
                <AlertTriangle className="h-4 w-4 text-warning shrink-0 mt-0.5" />
                <div className="text-[11px] text-muted-foreground leading-relaxed">
                  <span className="text-foreground font-medium">Comparison Insight: </span>
                  Highest compliance is{' '}
                  <span className="text-foreground font-semibold">
                    {selectedFrameworks.reduce((max, fw) => (fw.compliance > max.compliance ? fw : max), selectedFrameworks[0]).name}
                  </span>{' '}
                  ({selectedFrameworks.reduce((max, fw) => (fw.compliance > max.compliance ? fw : max), selectedFrameworks[0]).compliance}%).
                  Lowest risk is{' '}
                  <span className="text-foreground font-semibold">
                    {(() => {
                      const order: RiskLevel[] = ['negligible', 'low', 'medium', 'high', 'critical'];
                      return [...selectedFrameworks].sort(
                        (a, b) => order.indexOf(a.riskLevel) - order.indexOf(b.riskLevel),
                      )[0].name;
                    })()}
                  </span>
                  . Radar dimensions are normalized 0–100; Risk Inverse is higher when risk is lower.
                </div>
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="shrink-0 border-t border-border px-6 py-3 flex items-center justify-between gap-3 bg-card">
          <p className="text-[11px] text-muted-foreground">
            Comparing {selectionCount} of {frameworks.length} available frameworks
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              className="text-xs h-8"
              onClick={() => setSelectedIds([])}
              disabled={selectionCount === 0}
            >
              Clear
            </Button>
            <Button
              variant="default"
              size="sm"
              className="text-xs h-8"
              onClick={() => onOpenChange(false)}
            >
              Done
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default FrameworkComparisonDialog;
