'use client';

import React, { useState, useMemo } from 'react';
import {
  Tabs,
  TabsList,
  TabsTrigger,
  TabsContent,
} from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { FrameworkComparisonDialog } from '@/components/assurance/framework/FrameworkComparisonDialog';
import {
  frameworks,
  controls,
} from '@/lib/assurance/mock-data';
import {
  getComplianceStatusBg,
  getComplianceStatusLabel,
  getRiskLevelBg,
  getRiskLevelLabel,
  getFrameworkStatusColor,
  getScoreColor,
  formatDate,
  timeAgo,
} from '@/lib/assurance/utils';
import {
  Shield,
  Search,
  GitBranch,
  FileCheck,
  Clock,
  Users,
  AlertTriangle,
  ChevronRight,
  Layers,
  ArrowRight,
  BarChart3,
  GitCompare,
} from 'lucide-react';
import type { Framework, Control } from '@/lib/assurance/types';
import { useRecentlyViewedStore } from '@/hooks/use-recently-viewed';
import { ControlDetailDrawer } from './ControlDetailDrawer';

// ─── Helpers ────────────────────────────────────────────────

function progressBarColor(value: number): string {
  if (value >= 80) return 'bg-success';
  if (value >= 60) return 'bg-warning';
  return 'bg-danger';
}

function confidenceBarColor(value: number): string {
  if (value >= 0.8) return 'bg-success';
  if (value >= 0.6) return 'bg-warning';
  return 'bg-danger';
}

function confidenceLabel(value: number): string {
  if (value >= 0.8) return 'High';
  if (value >= 0.6) return 'Medium';
  return 'Low';
}

function getFrameworkName(frameworkId: string): string {
  const fw = frameworks.find((f) => f.id === frameworkId);
  return fw ? fw.name : frameworkId;
}

function getPriorityIcon(priority: string) {
  switch (priority) {
    case 'critical':
      return <AlertTriangle className="h-3 w-3 text-danger" />;
    case 'high':
      return <AlertTriangle className="h-3 w-3 text-warning" />;
    default:
      return null;
  }
}

// ─── Tab 1: Framework Dashboard ─────────────────────────────

function FrameworkDashboard() {
  const [compareOpen, setCompareOpen] = useState(false);
  return (
    <div className="space-y-4">
      {/* Dashboard tab header */}
      <div className="flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-primary" />
          <h2 className="text-sm font-semibold text-foreground">Framework Dashboard</h2>
          <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
            {frameworks.length} frameworks
          </Badge>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="h-8 gap-1.5 text-xs"
          onClick={() => setCompareOpen(true)}
        >
          <GitCompare className="h-3.5 w-3.5" />
          Compare Frameworks
        </Button>
      </div>

      {/* Framework cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {frameworks.map((fw: Framework) => (
          <div
            key={fw.id}
            className="bg-card border border-border rounded-lg p-5 hover:border-primary/30 transition-all duration-200 hover:shadow-md hover:shadow-primary/5 group"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2 min-w-0">
              <div className="p-1.5 rounded-md bg-primary/10 shrink-0">
                <Shield className="h-4 w-4 text-primary" />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-foreground truncate">
                  {fw.name}
                </h3>
              </div>
            </div>
            <div className="flex items-center gap-1.5 shrink-0 ml-2">
              <Badge
                variant="outline"
                className="text-[10px] px-1.5 py-0 border-border/50 text-muted-foreground"
              >
                v{fw.version}
              </Badge>
              <Badge
                variant="outline"
                className={`text-[10px] px-1.5 py-0 ${getFrameworkStatusColor(fw.status)}`}
              >
                {fw.status}
              </Badge>
            </div>
          </div>

          {/* Description */}
          <p className="text-xs text-muted-foreground mb-4 line-clamp-2">
            {fw.description}
          </p>

          {/* Compliance Bar */}
          <div className="mb-3">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-xs text-muted-foreground">Compliance</span>
              <span className={`text-sm font-bold ${getScoreColor(fw.compliance)}`}>
                {fw.compliance}%
              </span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${progressBarColor(fw.compliance)}`}
                style={{ width: `${fw.compliance}%` }}
              />
            </div>
          </div>

          {/* Stats Row */}
          <div className="grid grid-cols-3 gap-3 mb-3">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Controls</p>
              <p className="text-sm font-semibold text-foreground">
                {fw.controlsCovered}
                <span className="text-muted-foreground font-normal">/{fw.controlsTotal}</span>
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Evidence</p>
              <p className="text-sm font-semibold text-foreground">{fw.evidenceLinked}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Risk</p>
              <div className="flex justify-center">
                <Badge
                  variant="outline"
                  className={`text-[10px] px-1.5 py-0 ${getRiskLevelBg(fw.riskLevel)}`}
                >
                  {getRiskLevelLabel(fw.riskLevel)}
                </Badge>
              </div>
            </div>
          </div>

          {/* Last Synced */}
          <div className="flex items-center gap-1.5 pt-3 border-t border-border/50">
            <Clock className="h-3 w-3 text-muted-foreground shrink-0" />
            <span className="text-[11px] text-muted-foreground">
              Last synced {timeAgo(fw.lastSync)}
            </span>
          </div>
        </div>
      ))}
      </div>

      {/* Framework Comparison Dialog */}
      <FrameworkComparisonDialog open={compareOpen} onOpenChange={setCompareOpen} />
    </div>
  );
}

// ─── Tab 2: Control Explorer ────────────────────────────────

function ControlExplorer({ onSelect }: { onSelect: (control: Control) => void }) {
  const [selectedFramework, setSelectedFramework] = useState<string>('all');

  const filteredControls = useMemo(() => {
    if (selectedFramework === 'all') return controls;
    return controls.filter((c: Control) => c.frameworkId === selectedFramework);
  }, [selectedFramework]);

  // Group controls by domain
  const groupedByDomain = useMemo(() => {
    const groups: Record<string, Control[]> = {};
    filteredControls.forEach((ctrl: Control) => {
      if (!groups[ctrl.domain]) groups[ctrl.domain] = [];
      groups[ctrl.domain].push(ctrl);
    });
    return groups;
  }, [filteredControls]);

  return (
    <div className="space-y-4">
      {/* Framework Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Framework:</span>
        </div>
        <Select value={selectedFramework} onValueChange={setSelectedFramework}>
          <SelectTrigger className="w-[200px]" size="sm">
            <SelectValue placeholder="Select framework" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Frameworks</SelectItem>
            {frameworks.map((fw: Framework) => (
              <SelectItem key={fw.id} value={fw.id}>
                {fw.name} (v{fw.version})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground ml-2">
          {filteredControls.length} controls
        </span>
      </div>

      {/* Controls by Domain - Accordion */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <Accordion type="multiple" defaultValue={Object.keys(groupedByDomain)} className="w-full">
          {Object.entries(groupedByDomain).map(([domain, domainControls]) => (
            <AccordionItem key={domain} value={domain}>
              <AccordionTrigger className="px-4 py-3 hover:no-underline hover:bg-surface/50 text-sm font-medium text-foreground">
                <div className="flex items-center gap-2">
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>{domain}</span>
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0 ml-1">
                    {domainControls.length}
                  </Badge>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-0 pb-0">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="text-[11px] text-muted-foreground h-8 px-4">Ref</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Title</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Owner</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Priority</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Status</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8 text-center">Evidence</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Confidence</TableHead>
                      <TableHead className="text-[11px] text-muted-foreground h-8">Last Validation</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {domainControls.map((ctrl: Control) => (
                      <TableRow
                        key={ctrl.id}
                        className="cursor-pointer hover:bg-primary/5 transition-colors"
                        onClick={() => onSelect(ctrl)}
                      >
                        <TableCell className="text-xs font-mono text-primary px-4">
                          {ctrl.controlRef}
                        </TableCell>
                        <TableCell className="text-xs text-foreground max-w-[200px]">
                          <span className="truncate block">{ctrl.title}</span>
                        </TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Users className="h-3 w-3 shrink-0" />
                            <span className="truncate max-w-[100px]">{ctrl.owner}</span>
                          </div>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`text-[10px] px-1.5 py-0 ${getRiskLevelBg(ctrl.priority)}`}
                          >
                            <span className="flex items-center gap-0.5">
                              {getPriorityIcon(ctrl.priority)}
                              {getRiskLevelLabel(ctrl.priority)}
                            </span>
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`text-[10px] px-1.5 py-0 ${getComplianceStatusBg(ctrl.complianceStatus)}`}
                          >
                            {getComplianceStatusLabel(ctrl.complianceStatus)}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-center text-foreground">
                          {ctrl.evidenceCount}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1.5">
                            <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                              <div
                                className={`h-full rounded-full ${confidenceBarColor(ctrl.confidence)}`}
                                style={{ width: `${ctrl.confidence * 100}%` }}
                              />
                            </div>
                            <span className={`text-[10px] font-medium ${ctrl.confidence >= 0.8 ? 'text-success' : ctrl.confidence >= 0.6 ? 'text-warning' : 'text-danger'}`}>
                              {Math.round(ctrl.confidence * 100)}%
                            </span>
                          </div>
                        </TableCell>
                        <TableCell className="text-[11px] text-muted-foreground">
                          {formatDate(ctrl.lastValidation)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </div>
  );
}

// ─── Tab 3: Control Mapping ─────────────────────────────────

function ControlMapping() {
  const [selectedFramework, setSelectedFramework] = useState<string>('fw-iso27001');

  const controlsWithMappings = useMemo(() => {
    return controls.filter(
      (c: Control) => c.frameworkId === selectedFramework && c.mappedControls.length > 0
    );
  }, [selectedFramework]);

  // Get unique mapped frameworks for column headers
  const mappedFrameworks = useMemo(() => {
    const fwSet = new Set<string>();
    controlsWithMappings.forEach((ctrl: Control) => {
      ctrl.mappedControls.forEach((mc) => fwSet.add(mc.framework));
    });
    return Array.from(fwSet).sort();
  }, [controlsWithMappings]);

  return (
    <div className="space-y-4">
      {/* Framework Selector */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Source Framework:</span>
        </div>
        <Select value={selectedFramework} onValueChange={setSelectedFramework}>
          <SelectTrigger className="w-[200px]" size="sm">
            <SelectValue placeholder="Select framework" />
          </SelectTrigger>
          <SelectContent>
            {frameworks.map((fw: Framework) => (
              <SelectItem key={fw.id} value={fw.id}>
                {fw.name} (v{fw.version})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <span className="text-xs text-muted-foreground ml-2">
          {controlsWithMappings.length} mapped controls
        </span>
      </div>

      {/* Mapping Visualization */}
      {controlsWithMappings.length === 0 ? (
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <GitBranch className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            No mapped controls found for this framework
          </p>
        </div>
      ) : (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <ScrollArea className="w-full">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="text-[11px] text-muted-foreground h-9 px-4 min-w-[140px]">
                    Source Control
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[180px]">
                    Title
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 w-10 text-center">
                    <ArrowRight className="h-3.5 w-3.5 mx-auto text-muted-foreground" />
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[160px]">
                    Mapped Framework
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[140px]">
                    Mapped Control
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[160px]">
                    Mapped Title
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[130px]">
                    Confidence
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {controlsWithMappings.flatMap((ctrl: Control) =>
                  ctrl.mappedControls.map((mc, mcIdx) => (
                    <TableRow key={`${ctrl.id}-${mcIdx}`} className="hover:bg-surface/50">
                      {mcIdx === 0 ? (
                        <>
                          <TableCell
                            className="text-xs font-mono text-primary px-4 align-top"
                            rowSpan={ctrl.mappedControls.length}
                          >
                            {ctrl.controlRef}
                          </TableCell>
                          <TableCell
                            className="text-xs text-foreground align-top max-w-[180px]"
                            rowSpan={ctrl.mappedControls.length}
                          >
                            <span className="line-clamp-2">{ctrl.title}</span>
                          </TableCell>
                        </>
                      ) : null}
                      <TableCell className="text-center w-10">
                        <ArrowRight className="h-3 w-3 mx-auto text-muted-foreground" />
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className="text-[10px] px-1.5 py-0 bg-primary/5 text-primary border-primary/20"
                        >
                          {mc.framework}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs font-mono text-foreground">
                        {mc.controlRef}
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground max-w-[160px]">
                        <span className="line-clamp-2">{mc.title}</span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-muted rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full ${confidenceBarColor(mc.confidence)}`}
                              style={{ width: `${mc.confidence * 100}%` }}
                            />
                          </div>
                          <span
                            className={`text-[10px] font-semibold ${
                              mc.confidence >= 0.8
                                ? 'text-success'
                                : mc.confidence >= 0.6
                                ? 'text-warning'
                                : 'text-danger'
                            }`}
                          >
                            {Math.round(mc.confidence * 100)}%
                          </span>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </ScrollArea>
        </div>
      )}

      {/* Mapping Summary */}
      {controlsWithMappings.length > 0 && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {mappedFrameworks.map((fwName) => {
            const mappings = controlsWithMappings.flatMap((ctrl: Control) =>
              ctrl.mappedControls.filter((mc) => mc.framework === fwName)
            );
            const avgConfidence =
              mappings.length > 0
                ? mappings.reduce((acc, mc) => acc + mc.confidence, 0) / mappings.length
                : 0;
            return (
              <div
                key={fwName}
                className="bg-card border border-border rounded-lg p-3 hover:border-primary/30 transition-colors"
              >
                <p className="text-xs text-muted-foreground mb-1">{fwName}</p>
                <p className="text-lg font-bold text-foreground">{mappings.length}</p>
                <div className="flex items-center gap-1.5 mt-1">
                  <div className="flex-1 h-1 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${confidenceBarColor(avgConfidence)}`}
                      style={{ width: `${avgConfidence * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    avg {Math.round(avgConfidence * 100)}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Tab 4: Evidence Requirements ───────────────────────────

function EvidenceRequirements() {
  const [selectedFramework, setSelectedFramework] = useState<string>('all');

  const filteredControls = useMemo(() => {
    if (selectedFramework === 'all') return controls;
    return controls.filter((c: Control) => c.frameworkId === selectedFramework);
  }, [selectedFramework]);

  const totalRequired = filteredControls.reduce((a, c) => a + c.requiredEvidence, 0);
  const totalAvailable = filteredControls.reduce((a, c) => a + c.availableEvidence, 0);
  const totalMissing = filteredControls.reduce((a, c) => a + c.missingEvidence, 0);

  return (
    <div className="space-y-4">
      {/* Header with selector and summary */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 justify-between">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <FileCheck className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Framework:</span>
          </div>
          <Select value={selectedFramework} onValueChange={setSelectedFramework}>
            <SelectTrigger className="w-[200px]" size="sm">
              <SelectValue placeholder="Select framework" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Frameworks</SelectItem>
              {frameworks.map((fw: Framework) => (
                <SelectItem key={fw.id} value={fw.id}>
                  {fw.name} (v{fw.version})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Summary Stats */}
        <div className="flex items-center gap-4">
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Required</p>
            <p className="text-sm font-bold text-foreground">{totalRequired}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Available</p>
            <p className="text-sm font-bold text-success">{totalAvailable}</p>
          </div>
          <div className="text-center">
            <p className="text-[10px] text-muted-foreground uppercase tracking-wide">Missing</p>
            <p className={`text-sm font-bold ${totalMissing > 0 ? 'text-danger' : 'text-success'}`}>
              {totalMissing}
            </p>
          </div>
        </div>
      </div>

      {/* Evidence Matrix Table */}
      <div className="bg-card border border-border rounded-lg overflow-hidden">
        <ScrollArea className="w-full">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead className="text-[11px] text-muted-foreground h-9 px-4 min-w-[100px]">
                  Control Ref
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[180px]">
                  Title
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[90px]">
                  Framework
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 text-center w-[70px]">
                  Required
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 text-center w-[70px]">
                  Available
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 text-center w-[70px]">
                  Missing
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[110px]">
                  Validation
                </TableHead>
                <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[150px]">
                  Confidence Level
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredControls.map((ctrl: Control) => {
                const hasMissing = ctrl.missingEvidence > 0;
                return (
                  <TableRow
                    key={ctrl.id}
                    className={`hover:bg-surface/50 ${hasMissing ? 'bg-danger/[0.03]' : ''}`}
                  >
                    <TableCell className="text-xs font-mono text-primary px-4">
                      {ctrl.controlRef}
                    </TableCell>
                    <TableCell className="text-xs text-foreground max-w-[180px]">
                      <span className="truncate block">{ctrl.title}</span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className="text-[10px] px-1.5 py-0 bg-primary/5 text-primary border-primary/20"
                      >
                        {getFrameworkName(ctrl.frameworkId)}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-xs text-center text-foreground">
                      {ctrl.requiredEvidence}
                    </TableCell>
                    <TableCell className="text-xs text-center text-success">
                      {ctrl.availableEvidence}
                    </TableCell>
                    <TableCell className="text-xs text-center">
                      {hasMissing ? (
                        <span className="text-danger font-semibold">{ctrl.missingEvidence}</span>
                      ) : (
                        <span className="text-success">0</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`text-[10px] px-1.5 py-0 ${getComplianceStatusBg(ctrl.complianceStatus)}`}
                      >
                        {getComplianceStatusLabel(ctrl.complianceStatus)}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden max-w-[80px]">
                          <div
                            className={`h-full rounded-full ${confidenceBarColor(ctrl.confidence)}`}
                            style={{ width: `${ctrl.confidence * 100}%` }}
                          />
                        </div>
                        <div className="flex items-center gap-1">
                          <span
                            className={`text-[10px] font-semibold ${
                              ctrl.confidence >= 0.8
                                ? 'text-success'
                                : ctrl.confidence >= 0.6
                                ? 'text-warning'
                                : 'text-danger'
                            }`}
                          >
                            {Math.round(ctrl.confidence * 100)}%
                          </span>
                          <span
                            className={`text-[10px] ${
                              ctrl.confidence >= 0.8
                                ? 'text-success/70'
                                : ctrl.confidence >= 0.6
                                ? 'text-warning/70'
                                : 'text-danger/70'
                            }`}
                          >
                            ({confidenceLabel(ctrl.confidence)})
                          </span>
                        </div>
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </ScrollArea>
      </div>

      {/* Evidence Gap Highlight */}
      {totalMissing > 0 && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-danger shrink-0" />
            <h4 className="text-sm font-semibold text-danger">Evidence Gaps Detected</h4>
          </div>
          <div className="space-y-1.5">
            {filteredControls
              .filter((c: Control) => c.missingEvidence > 0)
              .map((ctrl: Control) => (
                <div
                  key={ctrl.id}
                  className="flex items-center gap-3 text-xs"
                >
                  <span className="font-mono text-primary shrink-0">{ctrl.controlRef}</span>
                  <span className="text-foreground truncate">{ctrl.title}</span>
                  <span className="text-danger font-semibold shrink-0 ml-auto">
                    {ctrl.missingEvidence} missing
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────

export function FrameworkSection() {
  const [selectedControl, setSelectedControlState] = useState<Control | null>(null);
  const addRecent = useRecentlyViewedStore((s) => s.addRecent);

  const setSelectedControl = (control: Control | null) => {
    setSelectedControlState(control);
    if (control) {
      addRecent({
        id: control.controlRef,
        type: 'control',
        title: control.title,
        subtitle: control.controlRef,
        section: 'frameworks',
      });
    }
  };

  return (
    <div className="p-6 space-y-5">
      {/* Section Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">Framework & Regulatory Playbook</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Configure compliance frameworks, explore controls, map cross-framework relationships, and manage evidence requirements
        </p>
      </div>

      {/* Tabs */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="bg-muted/50">
          <TabsTrigger value="dashboard" className="gap-1.5 text-xs">
            <BarChart3 className="h-3.5 w-3.5" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="controls" className="gap-1.5 text-xs">
            <Search className="h-3.5 w-3.5" />
            Control Explorer
          </TabsTrigger>
          <TabsTrigger value="mapping" className="gap-1.5 text-xs">
            <GitBranch className="h-3.5 w-3.5" />
            Control Mapping
          </TabsTrigger>
          <TabsTrigger value="evidence" className="gap-1.5 text-xs">
            <FileCheck className="h-3.5 w-3.5" />
            Evidence Requirements
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <FrameworkDashboard />
        </TabsContent>

        <TabsContent value="controls">
          <ControlExplorer onSelect={setSelectedControl} />
        </TabsContent>

        <TabsContent value="mapping">
          <ControlMapping />
        </TabsContent>

        <TabsContent value="evidence">
          <EvidenceRequirements />
        </TabsContent>
      </Tabs>

      <ControlDetailDrawer
        control={selectedControl}
        open={!!selectedControl}
        onOpenChange={(open) => !open && setSelectedControl(null)}
      />
    </div>
  );
}
