'use client';

import React, { useEffect, useState } from 'react';
import { Shield, FileCheck, AlertTriangle, TrendingUp, Activity, FileText, Clock, CheckCircle2, XCircle, AlertCircle, ArrowRight, Zap, ScanLine, Database, Target, FileBarChart, ChevronRight, ScrollText, Calendar, ChevronDown } from 'lucide-react';
import { frameworks, risks, evidenceItems, reports, resilienceScore, complianceTrendData, riskDistributionData, riskMatrixData, notifications as notifData, tasks as allTasks } from '@/lib/assurance/mock-data';
import { getScoreColor, getRiskLevelBg, getRiskLevelLabel, timeAgo } from '@/lib/assurance/utils';
import { CHART_THEME, TOOLTIP_STYLE } from '@/lib/assurance/chart-theme';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend,
} from 'recharts';
import { DashboardSkeleton } from '@/components/assurance/shared/Skeletons';
import { useNavigationStore } from '@/hooks/use-navigation';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { useCountUp } from '@/hooks/use-count-up';
import { EvidenceChainFlow } from './EvidenceChainFlow';

export function DashboardSection() {
  // Simulate an initial data fetch for a premium perceived-loading experience.
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const timer = setTimeout(() => setLoading(false), 600);
    return () => clearTimeout(timer);
  }, []);

  const activeFrameworks = frameworks.filter((f) => f.status === 'active').length;
  const pendingEvidence = evidenceItems.filter((e) => e.validationStatus === 'pending').length;
  const expiredEvidence = evidenceItems.filter((e) => e.validationStatus === 'expired').length;
  const validatedEvidence = evidenceItems.filter((e) => e.validationStatus === 'validated').length;
  const criticalRisks = risks.filter((r) => r.severity === 'critical').length;
  const openRisks = risks.filter((r) => r.status === 'open').length;
  const recentReports = reports.slice(0, 4);
  const unreadNotifications = notifData.filter((n) => !n.read).length;

  const avgCompliance = Math.round(
    frameworks.reduce((acc, f) => acc + f.compliance, 0) / frameworks.length
  );

  const kpiStats = [
    {
      label: 'Active Frameworks',
      value: activeFrameworks,
      sub: `of ${frameworks.length} total`,
      icon: Shield,
      color: 'text-primary',
      bg: 'bg-primary/10',
      borderColor: 'border-primary/20',
      trend: '+1',
      trendUp: true,
    },
    {
      label: 'Validated Evidence',
      value: validatedEvidence,
      sub: `${pendingEvidence} pending · ${expiredEvidence} expired`,
      icon: FileCheck,
      color: 'text-success',
      bg: 'bg-success/10',
      borderColor: 'border-success/20',
      trend: '+12%',
      trendUp: true,
    },
    {
      label: 'Critical Risks',
      value: criticalRisks,
      sub: `${openRisks} open risks`,
      icon: AlertTriangle,
      color: 'text-danger',
      bg: 'bg-danger/10',
      borderColor: 'border-danger/20',
      trend: '+2',
      trendUp: false,
    },
    {
      label: 'Resilience Score',
      value: `${resilienceScore.overall}%`,
      sub: `Compliance: ${resilienceScore.compliance}%`,
      icon: TrendingUp,
      color: getScoreColor(resilienceScore.overall),
      bg: getScoreColor(resilienceScore.overall) === 'text-success' ? 'bg-success/10' : getScoreColor(resilienceScore.overall) === 'text-warning' ? 'bg-warning/10' : 'bg-danger/10',
      borderColor: getScoreColor(resilienceScore.overall) === 'text-success' ? 'border-success/20' : getScoreColor(resilienceScore.overall) === 'text-warning' ? 'border-warning/20' : 'border-danger/20',
      trend: '+3%',
      trendUp: true,
    },
  ];

  // Traceability flow steps
  const traceabilitySteps = [
    { label: 'Strike Engine', sub: 'Module 1', icon: Zap, color: 'text-warning', bg: 'bg-warning/15', count: null },
    { label: 'Validator', sub: 'Module 2', icon: ScanLine, color: 'text-cyber', bg: 'bg-cyber/15', count: null },
    { label: 'Evidence', sub: 'Validated', icon: Database, color: 'text-success', bg: 'bg-success/15', count: validatedEvidence },
    { label: 'Control', sub: 'Mapped', icon: Target, color: 'text-primary', bg: 'bg-primary/15', count: 14 },
    { label: 'Framework', sub: 'Compliant', icon: Shield, color: 'text-purple-400', bg: 'bg-purple-500/15', count: 5 },
    { label: 'Report', sub: 'Generated', icon: FileBarChart, color: 'text-cyan-400', bg: 'bg-cyan-500/15', count: reports.filter(r => r.status === 'generated').length },
  ];

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="p-6 space-y-6">
      {/* Page Title */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Assurance Dashboard</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time overview of your GRC posture and compliance status
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Date Range Filter */}
          <DateRangeFilter />
          {/* Live indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border">
            <div className="h-2 w-2 rounded-full bg-success cyber-pulse" />
            <span className="text-xs text-muted-foreground">Live ·</span>
            <span className="text-xs font-medium text-foreground">{timeAgo('2025-01-15T10:30:00Z')}</span>
          </div>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {kpiStats.map((stat) => (
          <div
            key={stat.label}
            className={`bg-card border ${stat.borderColor} rounded-xl p-5 card-hover hover:border-primary/40 group relative overflow-hidden`}
          >
            <div className="absolute -right-4 -top-4 h-20 w-20 rounded-full bg-primary/5 group-hover:bg-primary/10 transition-colors" />
            <div className="relative flex items-start justify-between">
              <div className="space-y-1.5">
                <p className="text-[11px] text-muted-foreground font-medium uppercase tracking-wider">{stat.label}</p>
                <p className={`text-3xl font-bold ${stat.color} leading-none`}><KpiValue value={stat.value} /></p>
                <div className="flex items-center gap-2">
                  <p className="text-[11px] text-muted-foreground">{stat.sub}</p>
                </div>
              </div>
              <div className={`p-2.5 rounded-lg ${stat.bg} group-hover:scale-110 transition-transform`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </div>
            <div className="relative mt-3 flex items-center gap-1.5">
              <span className={`text-[10px] font-semibold flex items-center gap-0.5 ${stat.trendUp ? 'text-success' : 'text-danger'}`}>
                {stat.trendUp ? '↑' : '↓'} {stat.trend}
              </span>
              <span className="text-[10px] text-muted-foreground">vs last period</span>
            </div>
          </div>
        ))}
      </div>

      {/* Executive Compliance Scorecard */}
      <ExecutiveScorecard />

      {/* Quick Actions */}
      <QuickActions />

      {/* Compliance Traceability Flow */}
      <div className="bg-card border border-border rounded-xl p-5 card-hover">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Compliance Traceability Flow</h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">Evidence chain from security event to audit report</p>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-success/10 border border-success/20">
            <div className="h-1.5 w-1.5 rounded-full bg-success cyber-pulse" />
            <span className="text-[10px] font-medium text-success">Chain Verified</span>
          </div>
        </div>
        <div className="flex items-center gap-2 overflow-x-auto pb-2">
          {traceabilitySteps.map((step, idx) => (
            <React.Fragment key={step.label}>
              <div className="flex flex-col items-center gap-2 min-w-[110px]">
                <div className={`p-3 rounded-xl ${step.bg} border border-border/50`}>
                  <step.icon className={`h-5 w-5 ${step.color}`} />
                </div>
                <div className="text-center">
                  <p className="text-xs font-medium text-foreground">{step.label}</p>
                  <p className="text-[10px] text-muted-foreground">{step.sub}</p>
                  {step.count !== null && (
                    <p className={`text-sm font-bold mt-0.5 ${step.color}`}>{step.count}</p>
                  )}
                </div>
              </div>
              {idx < traceabilitySteps.length - 1 && (
                <div className="flex items-center shrink-0">
                  <div className="h-px w-8 bg-gradient-to-r from-border to-border/50" />
                  <ChevronRight className="h-4 w-4 text-muted-foreground/50 -ml-1" />
                </div>
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Executive Compliance Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Overall Compliance Gauge */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover lg:col-span-1">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Executive Summary</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Overall compliance posture</p>
            </div>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="flex flex-col items-center justify-center py-2">
            <ExecutiveGauge score={avgCompliance} />
            <div className="mt-3 text-center">
              <p className="text-xs text-muted-foreground">Average Compliance</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">across {frameworks.length} frameworks</p>
            </div>
          </div>
        </div>

        {/* Compliance Breakdown by Framework */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover lg:col-span-2">
          <div className="flex items-center justify-between mb-3">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Compliance Breakdown</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Framework status overview</p>
            </div>
            <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-success" /> Compliant</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-warning" /> Partial</span>
              <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full bg-danger" /> Non-Compliant</span>
            </div>
          </div>
          <div className="grid grid-cols-5 gap-2">
            {frameworks.map((fw) => (
              <div key={fw.id} className="text-center">
                <div className="relative h-20 flex items-end justify-center">
                  <div className="w-full bg-muted/40 rounded-md overflow-hidden h-full flex items-end">
                    <div
                      className={`w-full rounded-md transition-all duration-700 ${
                        fw.compliance >= 80 ? 'bg-success' : fw.compliance >= 60 ? 'bg-warning' : 'bg-danger'
                      }`}
                      style={{ height: `${fw.compliance}%` }}
                    />
                  </div>
                  <span className={`absolute top-1 text-[10px] font-bold ${getScoreColor(fw.compliance)}`}>
                    {fw.compliance}%
                  </span>
                </div>
                <p className="text-[10px] text-foreground font-medium mt-1.5 truncate">{fw.name}</p>
                <p className="text-[9px] text-muted-foreground">{fw.controlsCovered}/{fw.controlsTotal}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Compliance Maturity Meter */}
      <ComplianceMaturityMeter />

      {/* Evidence Chain Flow Diagram */}
      <EvidenceChainFlow />

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Compliance Trend Chart */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Compliance Trend</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">6-month progression across frameworks</p>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-primary/10">
              <Activity className="h-3 w-3 text-primary" />
              <span className="text-[10px] font-medium text-primary">Trending up</span>
            </div>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={complianceTrendData} margin={{ top: 5, right: 10, left: -15, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} vertical={false} />
                <XAxis dataKey="month" tick={{ fill: CHART_THEME.axis, fontSize: 11 }} axisLine={{ stroke: CHART_THEME.axisLine }} tickLine={false} />
                <YAxis tick={{ fill: CHART_THEME.axis, fontSize: 11 }} axisLine={{ stroke: CHART_THEME.axisLine }} tickLine={false} domain={[0, 100]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }} />
                <Line type="monotone" dataKey="iso" name="ISO 27001" stroke={CHART_THEME.primary} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.primary }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="gdpr" name="GDPR" stroke={CHART_THEME.success} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.success }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="nist" name="NIST CSF" stroke={CHART_THEME.warning} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.warning }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="pci" name="PCI-DSS" stroke={CHART_THEME.danger} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.danger }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="dpdp" name="DPDP" stroke={CHART_THEME.purple} strokeWidth={2} dot={{ r: 3, fill: CHART_THEME.purple }} activeDot={{ r: 5 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Risk Distribution */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Risk Distribution</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Risks by severity level</p>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-danger/10">
              <AlertTriangle className="h-3 w-3 text-danger" />
              <span className="text-[10px] font-medium text-danger">{criticalRisks} critical</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4 items-center">
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={75}
                    paddingAngle={3}
                    dataKey="value"
                    stroke="none"
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-2">
              {riskDistributionData.map((item) => (
                <div key={item.name} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="h-2.5 w-2.5 rounded-sm" style={{ backgroundColor: item.color }} />
                    <span className="text-xs text-foreground">{item.name}</span>
                  </div>
                  <span className="text-xs font-bold text-foreground">{item.value}</span>
                </div>
              ))}
              <div className="h-px bg-border my-2" />
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-muted-foreground">Total Risks</span>
                <span className="text-xs font-bold text-foreground">{riskDistributionData.reduce((a, b) => a + b.value, 0)}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Risk Matrix Heatmap */}
      <div className="bg-card border border-border rounded-xl p-5 card-hover">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Risk Matrix Heatmap</h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">Risk distribution by likelihood vs impact</p>
          </div>
          <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-success/40" /> Low</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-warning/40" /> Medium</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-danger/40" /> High</span>
            <span className="flex items-center gap-1"><span className="h-2 w-2 rounded bg-danger" /> Critical</span>
          </div>
        </div>
        <RiskMatrixHeatmap />
      </div>

      {/* Compliance Forecast */}
      <ComplianceForecast />

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Framework Compliance Bars */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Framework Compliance</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Current compliance levels</p>
            </div>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="space-y-4">
            {frameworks.map((fw) => (
              <div key={fw.id} className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-foreground font-semibold">{fw.name}</span>
                    <span className="text-[10px] text-muted-foreground px-1.5 py-0.5 rounded bg-muted/50">v{fw.version}</span>
                  </div>
                  <span className={`text-sm font-bold ${getScoreColor(fw.compliance)}`}>
                    {fw.compliance}%
                  </span>
                </div>
                <div className="h-2.5 bg-muted/60 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all duration-700 ${
                      fw.compliance >= 80 ? 'bg-success' : fw.compliance >= 60 ? 'bg-warning' : 'bg-danger'
                    }`}
                    style={{ width: `${fw.compliance}%` }}
                  />
                </div>
                <div className="flex justify-between text-[10px] text-muted-foreground">
                  <span>{fw.controlsCovered}/{fw.controlsTotal} controls</span>
                  <span>{fw.evidenceLinked} evidence items</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Activity & Alerts */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Recent Alerts</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">{unreadNotifications} unread notifications</p>
            </div>
            <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-warning/10">
              <AlertCircle className="h-3 w-3 text-warning" />
              <span className="text-[10px] font-medium text-warning">{unreadNotifications} new</span>
            </div>
          </div>
          <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
            {notifData.slice(0, 6).map((notif) => (
              <div
                key={notif.id}
                className={`p-3 rounded-lg border transition-colors ${
                  notif.read
                    ? 'bg-surface/50 border-border/50'
                    : 'bg-surface border-border hover:border-primary/30'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  <div className={`mt-1 h-2 w-2 shrink-0 rounded-full ${
                    notif.severity === 'error' ? 'bg-danger' :
                    notif.severity === 'warning' ? 'bg-warning' :
                    notif.severity === 'success' ? 'bg-success' : 'bg-primary'
                  }`} />
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground">{notif.title}</p>
                    <p className="text-[11px] text-muted-foreground mt-0.5 line-clamp-2">{notif.message}</p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className="text-[10px] text-muted-foreground font-medium">{timeAgo(notif.timestamp)}</span>
                      <span className="text-[10px] text-muted-foreground">·</span>
                      <span className="text-[10px] text-muted-foreground">{notif.source}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Activity Timeline */}
      <ActivityTimeline />

      {/* My Tasks Summary */}
      <MyTasksSummary />

      {/* Bottom Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Top Risks */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Top Risks</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Highest impact open risks</p>
            </div>
            <AlertTriangle className="h-4 w-4 text-danger" />
          </div>
          <div className="space-y-2">
            {risks
              .filter((r) => r.status === 'open')
              .sort((a, b) => b.residualRisk - a.residualRisk)
              .slice(0, 5)
              .map((risk) => (
                <div
                  key={risk.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border/50 hover:border-primary/30 transition-colors group"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${getRiskLevelBg(risk.severity)}`}>
                      {getRiskLevelLabel(risk.severity)}
                    </span>
                    <div className="min-w-0">
                      <p className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">{risk.title}</p>
                      <p className="text-[10px] text-muted-foreground">{risk.framework} · {risk.id}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0 ml-3">
                    <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${risk.residualRisk >= 70 ? 'bg-danger' : risk.residualRisk >= 40 ? 'bg-warning' : 'bg-success'}`}
                        style={{ width: `${risk.residualRisk}%` }}
                      />
                    </div>
                    <span className="text-[10px] font-semibold text-foreground w-8 text-right">{risk.residualRisk}%</span>
                  </div>
                </div>
              ))}
          </div>
        </div>

        {/* Recent Reports */}
        <div className="bg-card border border-border rounded-xl p-5 card-hover">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-sm font-semibold text-foreground">Recent Reports</h2>
              <p className="text-[11px] text-muted-foreground mt-0.5">Latest compliance reports</p>
            </div>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </div>
          <div className="space-y-2">
            {recentReports.map((report) => (
              <div
                key={report.id}
                className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border/50 hover:border-primary/30 transition-colors group"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`p-2 rounded-lg shrink-0 ${
                    report.status === 'generated' ? 'bg-success/10' :
                    report.status === 'scheduled' ? 'bg-primary/10' :
                    report.status === 'pending' ? 'bg-warning/10' : 'bg-muted'
                  }`}>
                    {report.status === 'generated' ? <CheckCircle2 className="h-3.5 w-3.5 text-success" /> :
                     report.status === 'scheduled' ? <Clock className="h-3.5 w-3.5 text-primary" /> :
                     report.status === 'pending' ? <AlertCircle className="h-3.5 w-3.5 text-warning" /> :
                     <XCircle className="h-3.5 w-3.5 text-muted-foreground" />}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">{report.title}</p>
                    <p className="text-[10px] text-muted-foreground mt-0.5">
                      {report.framework} · <span className="capitalize">{report.status}</span> · {timeAgo(report.generatedAt || report.scheduledAt || '')}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 ml-3">
                  <span className={`text-sm font-bold ${getScoreColor(report.complianceScore)}`}>
                    {report.complianceScore}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Evidence Traceability Banner */}
      <div className="bg-gradient-to-r from-primary/10 via-primary/5 to-transparent border border-primary/20 rounded-xl p-5">
        <div className="flex items-center gap-4">
          <div className="p-3 rounded-xl bg-primary/20 cyber-glow shrink-0">
            <Shield className="h-5 w-5 text-primary" />
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-foreground">Evidence-Backed Compliance</h3>
            <p className="text-xs text-muted-foreground mt-0.5">
              Every compliance decision is traceable through the evidence chain. No control is marked compliant without validated evidence.
            </p>
          </div>
          <div className="flex items-center gap-6 shrink-0">
            <div className="text-center">
              <p className="text-2xl font-bold text-success leading-none">{validatedEvidence}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Validated</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div className="text-center">
              <p className="text-2xl font-bold text-warning leading-none">{pendingEvidence}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Pending</p>
            </div>
            <div className="h-10 w-px bg-border" />
            <div className="text-center">
              <p className="text-2xl font-bold text-danger leading-none">{expiredEvidence}</p>
              <p className="text-[10px] text-muted-foreground mt-1">Expired</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Risk Matrix Heatmap Component
function RiskMatrixHeatmap() {
  // 5x5 grid: likelihood (rows) x impact (cols)
  const likelihoodLabels = ['Rare', 'Unlikely', 'Possible', 'Likely', 'Almost Certain'];
  const impactLabels = ['Insignificant', 'Minor', 'Moderate', 'Major', 'Severe'];

  // Build matrix from riskMatrixData
  const matrix: { count: number; level: string }[][] = [];
  for (let i = 0; i < 5; i++) {
    matrix[i] = [];
    for (let j = 0; j < 5; j++) {
      const likelihood = i + 1;
      const impact = j + 1;
      const cell = riskMatrixData.find((d) => d.likelihood === likelihood && d.impact === impact);
      const count = cell?.count || 0;
      // Determine risk level based on likelihood * impact
      const score = likelihood * impact;
      let level = 'low';
      if (score >= 20) level = 'critical';
      else if (score >= 12) level = 'high';
      else if (score >= 6) level = 'medium';
      matrix[i][j] = { count, level };
    }
  }

  const getCellColor = (level: string, count: number) => {
    if (count === 0) {
      switch (level) {
        case 'critical': return 'bg-danger/10';
        case 'high': return 'bg-danger/5';
        case 'medium': return 'bg-warning/5';
        case 'low': return 'bg-success/5';
        default: return 'bg-muted/20';
      }
    }
    switch (level) {
      case 'critical': return 'bg-danger/70 text-white';
      case 'high': return 'bg-danger/40 text-danger-foreground';
      case 'medium': return 'bg-warning/40 text-warning-foreground';
      case 'low': return 'bg-success/30 text-success-foreground';
      default: return 'bg-muted/20';
    }
  };

  return (
    <div className="overflow-x-auto">
      <div className="min-w-[500px]">
        {/* Impact labels - top */}
        <div className="flex">
          <div className="w-24 shrink-0" />
          <div className="flex-1 grid grid-cols-5 gap-1">
            {impactLabels.map((label) => (
              <div key={label} className="text-center text-[10px] text-muted-foreground font-medium pb-1.5">
                {label}
              </div>
            ))}
          </div>
        </div>
        {/* Matrix rows */}
        <div className="space-y-1">
          {matrix.map((row, i) => (
            <div key={i} className="flex items-center">
              <div className="w-24 shrink-0 text-[10px] text-muted-foreground font-medium pr-2 text-right">
                {likelihoodLabels[i]}
              </div>
              <div className="flex-1 grid grid-cols-5 gap-1">
                {row.map((cell, j) => (
                  <div
                    key={j}
                    className={`aspect-[2/1] rounded-md flex items-center justify-center text-xs font-bold transition-all hover:scale-105 cursor-default ${getCellColor(cell.level, cell.count)}`}
                    title={`${likelihoodLabels[i]} × ${impactLabels[j]}: ${cell.count} risk(s)`}
                  >
                    {cell.count > 0 && cell.count}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
        {/* Axis labels */}
        <div className="flex justify-between mt-3 text-[10px] text-muted-foreground">
          <span>← Likelihood</span>
          <span>Impact →</span>
        </div>
      </div>
    </div>
  );
}

// Executive Gauge Component - semi-circular gauge
function ExecutiveGauge({ score }: { score: number }) {
  const radius = 52;
  const circumference = Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;
  const color = score >= 80 ? CHART_THEME.success : score >= 60 ? CHART_THEME.warning : CHART_THEME.danger;

  return (
    <div className="relative">
      <svg width="140" height="80" viewBox="0 0 140 80">
        <path
          d={`M 8 72 A ${radius} ${radius} 0 0 1 132 72`}
          fill="none"
          stroke={CHART_THEME.grid}
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d={`M 8 72 A ${radius} ${radius} 0 0 1 132 72`}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.7s ease' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-end pb-1">
        <span className="text-3xl font-bold" style={{ color }}>{score}%</span>
      </div>
    </div>
  );
}

// Activity Timeline Component - recent compliance events
function ActivityTimeline() {
  const events = [
    { id: 1, type: 'evidence', title: 'Evidence Validated', desc: 'EVD-2025-006 AWS IAM scan validated', time: '2m ago', icon: FileCheck, color: 'text-success', bg: 'bg-success/15' },
    { id: 2, type: 'risk', title: 'Risk Escalated', desc: 'RISK-006 Shadow IT severity increased to High', time: '18m ago', icon: AlertTriangle, color: 'text-danger', bg: 'bg-danger/15' },
    { id: 3, type: 'report', title: 'Report Generated', desc: 'Q4 2024 ISO 27001 Compliance Report ready', time: '1h ago', icon: FileText, color: 'text-primary', bg: 'bg-primary/15' },
    { id: 4, type: 'framework', title: 'Framework Synced', desc: 'NIST CSF 2.0.3 definitions updated', time: '3h ago', icon: Shield, color: 'text-cyber', bg: 'bg-cyber/15' },
    { id: 5, type: 'evidence', title: 'Evidence Expired', desc: 'EVD-2025-005 requires revalidation', time: '5h ago', icon: AlertCircle, color: 'text-warning', bg: 'bg-warning/15' },
    { id: 6, type: 'control', title: 'Control Assessed', desc: 'A.9.1.1 Access Control Policy verified', time: '8h ago', icon: CheckCircle2, color: 'text-success', bg: 'bg-success/15' },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Activity Timeline</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Recent compliance events and system activity</p>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-primary/10">
          <Activity className="h-3 w-3 text-primary" />
          <span className="text-[10px] font-medium text-primary">Live feed</span>
        </div>
      </div>
      <div className="relative">
        <div className="absolute left-[15px] top-2 bottom-2 w-px bg-border" />
        <div className="space-y-3">
          {events.map((event) => (
            <div key={event.id} className="relative flex items-start gap-3 pl-1">
              <div className={`relative z-10 p-2 rounded-lg ${event.bg} shrink-0`}>
                <event.icon className={`h-3.5 w-3.5 ${event.color}`} />
              </div>
              <div className="flex-1 min-w-0 pb-1">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-medium text-foreground">{event.title}</p>
                  <span className="text-[10px] text-muted-foreground shrink-0">{event.time}</span>
                </div>
                <p className="text-[11px] text-muted-foreground mt-0.5 truncate">{event.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Compliance Forecast Component - projected compliance trajectory
function ComplianceForecast() {
  // Historical + forecast data
  const forecastData = [
    { month: 'Jul', actual: 65, forecast: null },
    { month: 'Aug', actual: 68, forecast: null },
    { month: 'Sep', actual: 70, forecast: null },
    { month: 'Oct', actual: 73, forecast: null },
    { month: 'Nov', actual: 75, forecast: null },
    { month: 'Dec', actual: 77, forecast: null },
    { month: 'Jan', actual: 78, forecast: 78 },
    { month: 'Feb', actual: null, forecast: 80 },
    { month: 'Mar', actual: null, forecast: 82 },
    { month: 'Apr', actual: null, forecast: 84 },
    { month: 'May', actual: null, forecast: 86 },
    { month: 'Jun', actual: null, forecast: 88 },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Compliance Forecast</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Projected compliance trajectory based on current trend</p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-primary" />
            Actual
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-0.5 w-4 bg-success" style={{ borderTop: '2px dashed' }} />
            Forecast
          </span>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-success/10">
            <TrendingUp className="h-3 w-3 text-success" />
            <span className="text-[10px] font-medium text-success">+10% projected</span>
          </div>
        </div>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={forecastData} margin={{ top: 5, right: 10, left: -15, bottom: 5 }}>
            <defs>
              <linearGradient id="forecastGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={CHART_THEME.success} stopOpacity={0.2} />
                <stop offset="100%" stopColor={CHART_THEME.success} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={CHART_THEME.grid} vertical={false} />
            <XAxis dataKey="month" tick={{ fill: CHART_THEME.axis, fontSize: 11 }} axisLine={{ stroke: CHART_THEME.axisLine }} tickLine={false} />
            <YAxis tick={{ fill: CHART_THEME.axis, fontSize: 11 }} axisLine={{ stroke: CHART_THEME.axisLine }} tickLine={false} domain={[50, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            {/* Actual line - solid */}
            <Line
              type="monotone"
              dataKey="actual"
              name="Actual"
              stroke={CHART_THEME.primary}
              strokeWidth={2.5}
              dot={{ r: 3, fill: CHART_THEME.primary }}
              activeDot={{ r: 5 }}
              connectNulls={false}
            />
            {/* Forecast line - dashed */}
            <Line
              type="monotone"
              dataKey="forecast"
              name="Forecast"
              stroke={CHART_THEME.success}
              strokeWidth={2.5}
              strokeDasharray="6 4"
              dot={{ r: 3, fill: CHART_THEME.success }}
              activeDot={{ r: 5 }}
              connectNulls={true}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-3">
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Current</p>
          <p className="text-lg font-bold text-foreground">78%</p>
          <p className="text-[10px] text-muted-foreground">January 2025</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Projected (6mo)</p>
          <p className="text-lg font-bold text-success">88%</p>
          <p className="text-[10px] text-muted-foreground">June 2025</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Target</p>
          <p className="text-lg font-bold text-cyber">90%</p>
          <p className="text-[10px] text-muted-foreground">Q3 2025 goal</p>
        </div>
      </div>
    </div>
  );
}

// Quick Actions Component
function QuickActions() {
  const { setActiveSection } = useNavigationStore();
  const { toast } = useToast();

  const actions = [
    { label: 'New Report', desc: 'Generate compliance report', icon: FileText, color: 'text-primary', bg: 'bg-primary/15', section: 'reports' as const },
    { label: 'Add Evidence', desc: 'Submit new evidence', icon: FileCheck, color: 'text-success', bg: 'bg-success/15', section: 'evidence' as const },
    { label: 'Review Risks', desc: 'Assess open risks', icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning/15', section: 'risk' as const },
    { label: 'View Tasks', desc: 'Check task board', icon: CheckCircle2, color: 'text-cyber', bg: 'bg-cyber/15', section: 'tasks' as const },
    { label: 'Audit Logs', desc: 'Review audit trail', icon: ScrollText, color: 'text-purple-400', bg: 'bg-purple-500/15', section: 'audit-logs' as const },
    { label: 'Framework Setup', desc: 'Manage frameworks', icon: Shield, color: 'text-cyan-400', bg: 'bg-cyan-500/15', section: 'frameworks' as const },
  ];

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Quick Actions</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Common tasks and shortcuts</p>
        </div>
        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-primary/10">
          <Zap className="h-3 w-3 text-primary" />
          <span className="text-[10px] font-medium text-primary">Shortcuts</span>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {actions.map((action) => (
          <button
            key={action.label}
            onClick={() => {
              setActiveSection(action.section);
              toast({ title: `Navigated to ${action.label}`, description: action.desc });
            }}
            className="group flex flex-col items-center gap-2 p-3 rounded-lg bg-surface border border-border/50 hover:border-primary/30 hover:bg-surface/70 transition-all"
          >
            <div className={`p-2.5 rounded-lg ${action.bg} group-hover:scale-110 transition-transform`}>
              <action.icon className={`h-4 w-4 ${action.color}`} />
            </div>
            <div className="text-center">
              <p className="text-xs font-medium text-foreground">{action.label}</p>
              <p className="text-[10px] text-muted-foreground mt-0.5">{action.desc}</p>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}

// My Tasks Summary Component
function MyTasksSummary() {
  const { setActiveSection } = useNavigationStore();

  const myTasks = allTasks.filter((t) => t.status !== 'done');
  const overdueTasks = allTasks.filter((t) => {
    return t.status !== 'done' && new Date(t.dueDate) < new Date('2025-01-15');
  });
  const criticalTasks = allTasks.filter((t) => t.priority === 'critical' && t.status !== 'done');
  const inProgressTasks = allTasks.filter((t) => t.status === 'in_progress');

  const upcomingTasks = allTasks
    .filter((t) => t.status !== 'done')
    .sort((a, b) => new Date(a.dueDate).getTime() - new Date(b.dueDate).getTime())
    .slice(0, 4);

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">My Tasks</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Assigned tasks requiring attention</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="text-xs gap-1"
          onClick={() => setActiveSection('tasks')}
        >
          View All
          <ChevronRight className="h-3 w-3" />
        </Button>
      </div>

      {/* Task Stats Row */}
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-surface rounded-lg p-3 border border-border/50 text-center">
          <p className="text-2xl font-bold text-foreground">{myTasks.length}</p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">Open</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50 text-center">
          <p className="text-2xl font-bold text-cyber">{inProgressTasks.length}</p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">In Progress</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50 text-center">
          <p className="text-2xl font-bold text-danger">{overdueTasks.length}</p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">Overdue</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50 text-center">
          <p className="text-2xl font-bold text-warning">{criticalTasks.length}</p>
          <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">Critical</p>
        </div>
      </div>

      {/* Upcoming Tasks List */}
      <div className="space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-wide text-muted-foreground mb-2">Upcoming Deadlines</p>
        {upcomingTasks.map((task) => {
          const overdue = task.status !== 'done' && new Date(task.dueDate) < new Date('2025-01-15');
          return (
            <div
              key={task.id}
              className="flex items-center justify-between p-2.5 rounded-lg bg-surface border border-border/50 hover:border-primary/30 transition-colors cursor-pointer group"
              onClick={() => setActiveSection('tasks')}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <div className={`h-2 w-2 shrink-0 rounded-full ${
                  task.priority === 'critical' ? 'bg-danger' :
                  task.priority === 'high' ? 'bg-warning' :
                  task.priority === 'medium' ? 'bg-cyber' : 'bg-success'
                }`} />
                <div className="min-w-0">
                  <p className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">{task.title}</p>
                  <p className="text-[10px] text-muted-foreground">{task.id} · {task.framework}</p>
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0 ml-2">
                <span className="text-[10px] text-muted-foreground">{task.assigneeInitials}</span>
                <span className={`text-[10px] font-medium ${overdue ? 'text-danger' : 'text-muted-foreground'}`}>
                  {overdue ? 'Overdue' : task.dueDate}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// KpiValue Component - handles count-up animation for numeric values
function KpiValue({ value }: { value: string | number }) {
  // Extract numeric part for count-up animation
  const str = String(value);
  const match = str.match(/^(\d+)(.*)$/);

  const targetNum = match ? parseInt(match[1], 10) : 0;
  const suffix = match ? match[2] : '';
  const animatedNum = useCountUp(targetNum, 1200);

  if (!match) {
    return <>{value}</>;
  }

  return <>{animatedNum}{suffix}</>;
}

// Compliance Maturity Meter Component
function ComplianceMaturityMeter() {
  const stages = [
    { level: 1, label: 'Initial', desc: 'Ad-hoc processes, no formal controls', score: 20, color: 'bg-danger', textColor: 'text-danger' },
    { level: 2, label: 'Developing', desc: 'Basic controls documented but not standardized', score: 40, color: 'bg-warning', textColor: 'text-warning' },
    { level: 3, label: 'Defined', desc: 'Standardized controls with formal documentation', score: 60, color: 'bg-cyber', textColor: 'text-cyber' },
    { level: 4, label: 'Managed', desc: 'Measured and monitored controls with KPIs', score: 80, color: 'bg-success', textColor: 'text-success' },
    { level: 5, label: 'Optimized', desc: 'Continuously improved and automated', score: 95, color: 'bg-primary', textColor: 'text-primary' },
  ];

  const currentScore = 73;
  const currentLevel = stages.find((s) => currentScore >= s.score - 20 && currentScore < s.score + 20) || stages[2];

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Compliance Maturity Meter</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Organization's GRC maturity level across 5 stages</p>
        </div>
        <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-cyber/10 border border-cyber/20">
          <span className="text-[10px] text-muted-foreground">Current:</span>
          <span className="text-xs font-bold text-cyber">Level {currentLevel.level} - {currentLevel.label}</span>
        </div>
      </div>

      {/* Maturity Progress Bar */}
      <div className="relative mb-6">
        <div className="h-3 bg-muted/60 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full bg-gradient-to-r from-danger via-warning via-cyber to-success transition-all duration-1000"
            style={{ width: `${currentScore}%` }}
          />
        </div>
        {/* Stage markers */}
        <div className="absolute inset-0 flex justify-between">
          {stages.map((stage) => (
            <div
              key={stage.level}
              className={`h-3 w-3 rounded-full border-2 border-card mt-0 ${stage.color} ${currentScore >= stage.score - 15 ? 'opacity-100' : 'opacity-40'}`}
              style={{ marginLeft: stage.level === 1 ? '-2px' : undefined, marginRight: stage.level === 5 ? '-2px' : undefined }}
              title={`Level ${stage.level}: ${stage.label}`}
            />
          ))}
        </div>
      </div>

      {/* Stage Cards */}
      <div className="grid grid-cols-5 gap-2">
        {stages.map((stage) => {
          const isCurrent = stage.level === currentLevel.level;
          const isPassed = stage.level < currentLevel.level;
          return (
            <div
              key={stage.level}
              className={`p-2.5 rounded-lg border text-center transition-all ${
                isCurrent
                  ? `${stage.color.replace('bg-', 'bg-')}/10 border-current/30 ring-1 ring-current/20`
                  : isPassed
                  ? 'bg-surface border-border/50 opacity-70'
                  : 'bg-surface/50 border-border/30 opacity-50'
              }`}
            >
              <div className={`h-6 w-6 rounded-full ${stage.color} mx-auto mb-1.5 flex items-center justify-center`}>
                <span className="text-[10px] font-bold text-white">{stage.level}</span>
              </div>
              <p className={`text-[10px] font-semibold ${isCurrent ? stage.textColor : 'text-muted-foreground'}`}>
                {stage.label}
              </p>
              <p className="text-[9px] text-muted-foreground mt-0.5 leading-tight line-clamp-2">
                {stage.desc}
              </p>
              {isCurrent && (
                <div className={`mt-1.5 text-[9px] font-bold ${stage.textColor}`}>
                  ● You are here
                </div>
              )}
              {isPassed && (
                <div className="mt-1.5 text-[9px] text-success font-bold">
                  ✓ Achieved
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary */}
      <div className="mt-4 flex items-center justify-between p-3 rounded-lg bg-surface border border-border/50">
        <div className="flex items-center gap-2">
          <TrendingUp className="h-4 w-4 text-success" />
          <div>
            <p className="text-xs font-medium text-foreground">Next Level: Managed (Level 4)</p>
            <p className="text-[10px] text-muted-foreground">7% improvement needed to reach Level 4</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm font-bold text-foreground">{currentScore}%</p>
          <p className="text-[10px] text-muted-foreground">Maturity Score</p>
        </div>
      </div>
    </div>
  );
}

// Date Range Filter Component
function DateRangeFilter() {
  const [range, setRange] = useState('30d');
  const [open, setOpen] = useState(false);

  const ranges = [
    { id: '7d', label: 'Last 7 days' },
    { id: '30d', label: 'Last 30 days' },
    { id: '90d', label: 'Last 90 days' },
    { id: 'ytd', label: 'Year to date' },
    { id: 'all', label: 'All time' },
  ];

  const current = ranges.find((r) => r.id === range) || ranges[1];

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border text-xs text-foreground hover:border-primary/30 transition-colors"
      >
        <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
        <span>{current.label}</span>
        <ChevronDown className={`h-3 w-3 text-muted-foreground transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute right-0 mt-1 w-48 bg-card border border-border rounded-lg shadow-xl z-50 py-1">
            {ranges.map((r) => (
              <button
                key={r.id}
                onClick={() => {
                  setRange(r.id);
                  setOpen(false);
                }}
                className={`w-full text-left px-3 py-1.5 text-xs transition-colors ${
                  r.id === range
                    ? 'bg-primary/10 text-primary font-medium'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/50'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// Executive Compliance Scorecard Component
function ExecutiveScorecard() {
  const metrics = [
    { label: 'Compliance Score', value: 73, max: 100, unit: '%', color: 'text-warning', bar: 'bg-warning', icon: Shield },
    { label: 'Resilience Score', value: 74, max: 100, unit: '%', color: 'text-warning', bar: 'bg-warning', icon: TrendingUp },
    { label: 'Risk Score', value: 68, max: 100, unit: '%', color: 'text-cyber', bar: 'bg-cyber', icon: AlertTriangle },
    { label: 'Evidence Coverage', value: 78, max: 100, unit: '%', color: 'text-success', bar: 'bg-success', icon: FileCheck },
    { label: 'Control Coverage', value: 71, max: 100, unit: '%', color: 'text-warning', bar: 'bg-warning', icon: Target },
    { label: 'Audit Readiness', value: 82, max: 100, unit: '%', color: 'text-success', bar: 'bg-success', icon: CheckCircle2 },
  ];

  const avgScore = Math.round(metrics.reduce((acc, m) => acc + m.value, 0) / metrics.length);
  const overallColor = avgScore >= 80 ? 'text-success' : avgScore >= 60 ? 'text-warning' : 'text-danger';
  const overallBg = avgScore >= 80 ? 'bg-success/10 border-success/20' : avgScore >= 60 ? 'bg-warning/10 border-warning/20' : 'bg-danger/10 border-danger/20';

  return (
    <div className={`rounded-xl p-5 border ${overallBg} card-hover`}>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Executive Scorecard</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">Key compliance metrics at a glance</p>
        </div>
        <div className="text-right">
          <p className={`text-2xl font-bold ${overallColor}`}>{avgScore}%</p>
          <p className="text-[10px] text-muted-foreground">Overall Score</p>
        </div>
      </div>
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <div key={metric.label} className="bg-card rounded-lg p-3 border border-border/50">
              <div className="flex items-center justify-between mb-2">
                <Icon className={`h-3.5 w-3.5 ${metric.color}`} />
                <span className={`text-lg font-bold ${metric.color}`}>{metric.value}{metric.unit}</span>
              </div>
              <p className="text-[10px] text-muted-foreground uppercase tracking-wide mb-1.5">{metric.label}</p>
              <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${metric.bar} transition-all duration-700`}
                  style={{ width: `${metric.value}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
