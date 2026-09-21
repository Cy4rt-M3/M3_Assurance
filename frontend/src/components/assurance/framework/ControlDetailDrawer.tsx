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
import {
  AlertTriangle,
  ShieldCheck,
  FileCheck,
  FileWarning,
  FileX,
  GitBranch,
  ArrowRight,
  User,
  Layers,
  FolderTree,
  Tag,
  Download,
  AlertCircle,
  TrendingUp,
  Calendar,
  CheckCircle2,
} from 'lucide-react';
import type { Control, MappedControl } from '@/lib/assurance/types';
import {
  getComplianceStatusBg,
  getComplianceStatusLabel,
  getRiskLevelBg,
  getRiskLevelLabel,
  getScoreColor,
  formatDate,
} from '@/lib/assurance/utils';
import { frameworks } from '@/lib/assurance/mock-data';

interface ControlDetailDrawerProps {
  control: Control | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// ─── Local helpers ──────────────────────────────────────────

function getFrameworkName(frameworkId: string): string {
  const fw = frameworks.find((f) => f.id === frameworkId);
  return fw ? fw.name : frameworkId;
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

function getFrameworkBadgeColor(framework: string): string {
  switch (framework) {
    case 'ISO 27001':
      return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'NIST CSF':
      return 'bg-success/15 text-success border-success/30';
    case 'GDPR':
      return 'bg-warning/15 text-warning border-warning/30';
    case 'PCI-DSS':
      return 'bg-danger/15 text-danger border-danger/30';
    case 'DPDP':
      return 'bg-primary/15 text-primary border-primary/30';
    default:
      return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

// ─── Detail Item ────────────────────────────────────────────

function DetailItem({ icon: Icon, label, value }: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
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

// ─── Evidence Stat Block ────────────────────────────────────

function EvidenceStat({
  icon: Icon,
  label,
  value,
  tone,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number;
  tone: 'default' | 'success' | 'danger';
}) {
  const toneClasses =
    tone === 'success'
      ? 'text-success bg-success/10'
      : tone === 'danger'
        ? 'text-danger bg-danger/10'
        : 'text-muted-foreground bg-muted/40';
  return (
    <div className="flex items-center gap-2.5 rounded-lg p-2.5 border border-border/50 bg-surface/60">
      <div className={`p-1.5 rounded-md ${toneClasses}`}>
        <Icon className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0">
        <p className={`text-lg font-bold leading-none ${tone === 'success' ? 'text-success' : tone === 'danger' ? 'text-danger' : 'text-foreground'}`}>
          {value}
        </p>
        <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-1">{label}</p>
      </div>
    </div>
  );
}

// ─── Cross-Framework Mapping Card ───────────────────────────

function MappingCard({ mapping, isLast }: { mapping: MappedControl; isLast: boolean }) {
  const pct = Math.round(mapping.confidence * 100);
  return (
    <div className="relative pl-4">
      {/* vertical connector line */}
      {!isLast && (
        <span
          aria-hidden
          className="absolute left-[7px] top-5 bottom-0 w-px bg-border/70"
        />
      )}
      {/* node dot */}
      <span
        aria-hidden
        className={`absolute left-0 top-1.5 h-3.5 w-3.5 rounded-full border-2 border-card ${
          mapping.confidence >= 0.8 ? 'bg-success' : mapping.confidence >= 0.6 ? 'bg-warning' : 'bg-danger'
        }`}
      />
      <div className="bg-surface rounded-lg p-3 border border-border/50 border-l-2 border-l-primary/60 mb-2">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 mb-1 flex-wrap">
              <Badge variant="outline" className={`text-[10px] px-1.5 py-0 ${getFrameworkBadgeColor(mapping.framework)}`}>
                {mapping.framework}
              </Badge>
              <span className="text-xs font-mono text-primary">{mapping.controlRef}</span>
            </div>
            <p className="text-xs text-foreground leading-snug">{mapping.title}</p>
          </div>
          <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0 mt-0.5" />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-muted-foreground uppercase tracking-wide shrink-0">Confidence</span>
          <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${confidenceBarColor(mapping.confidence)}`}
              style={{ width: `${pct}%` }}
            />
          </div>
          <span className={`text-[10px] font-semibold shrink-0 ${mapping.confidence >= 0.8 ? 'text-success' : mapping.confidence >= 0.6 ? 'text-warning' : 'text-danger'}`}>
            {pct}%
          </span>
        </div>
      </div>
    </div>
  );
}

// ─── Main Drawer Component ──────────────────────────────────

export function ControlDetailDrawer({ control, open, onOpenChange }: ControlDetailDrawerProps) {
  if (!control) return null;

  const hasMissing = control.missingEvidence > 0;
  const meetsRequirement = control.availableEvidence >= control.requiredEvidence;
  const confidencePct = Math.round(control.confidence * 100);
  // Ratio for evidence coverage bar (cap at 100%)
  const evidenceRatio =
    control.requiredEvidence > 0
      ? Math.min(100, Math.round((control.availableEvidence / control.requiredEvidence) * 100))
      : 100;

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent
        side="right"
        className="w-full sm:max-w-xl p-0 bg-card border-l border-border flex flex-col"
      >
        {/* ─── Sticky Header ─── */}
        <div className="sticky top-0 z-10 bg-card/95 backdrop-blur border-b border-border p-4">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5 min-w-0">
              <div className={`p-2 rounded-lg ${getComplianceStatusBg(control.complianceStatus)}`}>
                <ShieldCheck className="h-4 w-4" />
              </div>
              <div className="min-w-0">
                <SheetHeader className="p-0">
                  <SheetTitle className="text-sm font-mono text-foreground">
                    {control.controlRef}
                  </SheetTitle>
                  <SheetDescription className="sr-only">
                    Control detail view with evidence status, cross-framework mappings, and metadata
                  </SheetDescription>
                </SheetHeader>
                <p className="text-[11px] text-muted-foreground mt-0.5 truncate">Control Detail</p>
              </div>
            </div>
            <Badge
              variant="outline"
              className={`text-[10px] px-2 py-0.5 shrink-0 ${getComplianceStatusBg(control.complianceStatus)}`}
            >
              {getComplianceStatusLabel(control.complianceStatus)}
            </Badge>
          </div>
        </div>

        {/* ─── Scrollable Body ─── */}
        <div
          className="flex-1 overflow-y-auto p-4 space-y-5"
          style={{ maxHeight: 'calc(100vh - 130px)' }}
        >
          {/* Section 2: Title & Description */}
          <section className="space-y-2">
            <h2 className="text-base font-semibold text-foreground leading-tight">{control.title}</h2>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              <p className="text-xs text-muted-foreground leading-relaxed">{control.description}</p>
            </div>
          </section>

          {/* Section 3: Evidence Status Card */}
          <section className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Evidence Status
            </h3>
            <div
              className={`rounded-xl p-4 border ${
                hasMissing
                  ? 'bg-danger/5 border-danger/30'
                  : meetsRequirement
                    ? 'bg-success/5 border-success/30'
                    : 'bg-warning/5 border-warning/30'
              }`}
            >
              <div className="grid grid-cols-3 gap-2 mb-3">
                <EvidenceStat
                  icon={FileCheck}
                  label="Required"
                  value={control.requiredEvidence}
                  tone="default"
                />
                <EvidenceStat
                  icon={CheckCircle2}
                  label="Available"
                  value={control.availableEvidence}
                  tone={meetsRequirement ? 'success' : 'default'}
                />
                <EvidenceStat
                  icon={FileX}
                  label="Missing"
                  value={control.missingEvidence}
                  tone={hasMissing ? 'danger' : 'default'}
                />
              </div>

              {/* Coverage bar */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">
                    Evidence Coverage
                  </span>
                  <span
                    className={`text-xs font-bold ${
                      evidenceRatio >= 100 ? 'text-success' : evidenceRatio >= 60 ? 'text-warning' : 'text-danger'
                    }`}
                  >
                    {evidenceRatio}%
                  </span>
                </div>
                <div className="h-2 bg-muted/60 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      evidenceRatio >= 100 ? 'bg-success' : evidenceRatio >= 60 ? 'bg-warning' : 'bg-danger'
                    }`}
                    style={{ width: `${evidenceRatio}%` }}
                  />
                </div>
              </div>

              {/* Warning alert when missing > 0 */}
              {hasMissing && (
                <div className="mt-3 flex items-start gap-2 rounded-md bg-danger/10 border border-danger/30 p-2.5">
                  <AlertCircle className="h-3.5 w-3.5 text-danger shrink-0 mt-0.5" />
                  <div className="min-w-0">
                    <p className="text-[11px] font-semibold text-danger">
                      {control.missingEvidence} evidence {control.missingEvidence === 1 ? 'item is' : 'items are'} missing
                    </p>
                    <p className="text-[10px] text-muted-foreground leading-snug mt-0.5">
                      Remediation required to meet the {control.requiredEvidence} evidence requirement for full compliance.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </section>

          {/* Section 4: Compliance & Confidence */}
          <section className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Compliance &amp; Confidence
            </h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Compliance Status</span>
                <Badge
                  variant="outline"
                  className={`text-[11px] px-2 py-0.5 ${getComplianceStatusBg(control.complianceStatus)}`}
                >
                  {getComplianceStatusLabel(control.complianceStatus)}
                </Badge>
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Confidence Score</span>
                  <span className={`text-sm font-bold ${getScoreColor(confidencePct)}`}>{confidencePct}%</span>
                </div>
                <div className="h-2.5 bg-muted/60 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      confidencePct >= 80 ? 'bg-success' : confidencePct >= 60 ? 'bg-warning' : 'bg-danger'
                    }`}
                    style={{ width: `${confidencePct}%` }}
                  />
                </div>
                <p className="text-[10px] text-muted-foreground">
                  Confidence level: <span className="font-medium text-foreground">{confidenceLabel(control.confidence)}</span>
                </p>
              </div>

              <div className="flex items-center justify-between pt-2 border-t border-border/50">
                <div className="flex items-center gap-1.5">
                  <Calendar className="h-3 w-3 text-muted-foreground" />
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Last Validation</span>
                </div>
                <span className="text-xs font-medium text-foreground">{formatDate(control.lastValidation)}</span>
              </div>
            </div>
          </section>

          {/* Section 5: Metadata Grid */}
          <section className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Metadata
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <DetailItem icon={Layers} label="Framework" value={getFrameworkName(control.frameworkId)} />
              <DetailItem icon={FolderTree} label="Domain" value={control.domain} />
              <DetailItem icon={Tag} label="Category" value={control.category} />
              <DetailItem icon={User} label="Owner" value={control.owner} />
            </div>
            <div className="flex items-center gap-2 bg-surface rounded-lg p-2.5 border border-border/50">
              <TrendingUp className="h-3 w-3 text-muted-foreground" />
              <span className="text-[10px] text-muted-foreground uppercase tracking-wide">Priority</span>
              <Badge
                variant="outline"
                className={`text-[10px] px-1.5 py-0 ml-auto ${getRiskLevelBg(control.priority)}`}
              >
                {getRiskLevelLabel(control.priority)}
              </Badge>
            </div>
          </section>

          {/* Section 6: Cross-Framework Mappings */}
          <section className="space-y-2">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Cross-Framework Mappings
              </h3>
              <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                {control.mappedControls.length} {control.mappedControls.length === 1 ? 'mapping' : 'mappings'}
              </Badge>
            </div>
            {control.mappedControls.length > 0 ? (
              <div className="bg-surface/40 rounded-lg p-3 border border-border/50">
                {/* source node */}
                <div className="flex items-center gap-2 mb-2 pl-4 relative">
                  <span
                    aria-hidden
                    className="absolute left-0 top-0.5 h-3.5 w-3.5 rounded-full border-2 border-card bg-primary"
                  />
                  <GitBranch className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span className="text-[11px] font-mono text-primary">{control.controlRef}</span>
                  <span className="text-[10px] text-muted-foreground truncate">
                    {getFrameworkName(control.frameworkId)}
                  </span>
                </div>
                {/* connector from source to first mapping */}
                <div className="pl-4 relative">
                  <span
                    aria-hidden
                    className="absolute left-[7px] top-0 bottom-0 w-px bg-border/70"
                  />
                </div>
                {control.mappedControls.map((mc, idx) => (
                  <MappingCard
                    key={`${mc.framework}-${mc.controlRef}-${idx}`}
                    mapping={mc}
                    isLast={idx === control.mappedControls.length - 1}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-surface rounded-lg p-4 border border-border/50 text-center">
                <GitBranch className="h-6 w-6 text-muted-foreground mx-auto mb-1.5" />
                <p className="text-xs text-muted-foreground">No cross-framework mappings defined</p>
              </div>
            )}
          </section>

          {/* Section 7: Risk Mapping */}
          <section className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Risk Mapping
            </h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              {control.riskMapping.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {control.riskMapping.map((riskId) => (
                    <Badge
                      key={riskId}
                      variant="outline"
                      className="text-[10px] font-mono bg-card border-danger/30 text-danger"
                    >
                      <AlertTriangle className="h-3 w-3" />
                      {riskId}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-muted-foreground italic">No risks mapped to this control</p>
              )}
            </div>
          </section>
        </div>

        {/* ─── Sticky Footer Actions ─── */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur border-t border-border p-4 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <FileCheck className="h-3.5 w-3.5" />
            View Evidence
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <FileWarning className="h-3.5 w-3.5" />
            View Risks
          </Button>
          <Button variant="default" size="sm" className="flex-1 text-xs gap-1.5">
            <Download className="h-3.5 w-3.5" />
            Export
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}
