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
  ShieldAlert, TrendingUp, TrendingDown, Minus, Target,
  User, FileText, Database, AlertTriangle, CheckCircle2,
  ArrowUp, ArrowRight, ArrowDown,
} from 'lucide-react';
import type { Risk } from '@/lib/assurance/types';
import {
  getRiskLevelBg, getRiskLevelLabel, getRiskLevelColor, getScoreColor,
} from '@/lib/assurance/utils';

interface RiskDetailDrawerProps {
  risk: Risk | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

function getMitigationRecommendation(severity: string): { title: string; description: string; timeline: string } {
  switch (severity) {
    case 'critical':
      return {
        title: 'Immediate Executive Escalation Required',
        description: 'Activate incident response procedures. Escalate to CISO and executive leadership immediately. Consider business impact and activate business continuity plans if necessary.',
        timeline: 'Immediate (24-48 hours)',
      };
    case 'high':
      return {
        title: 'Prioritize Remediation',
        description: 'Assign dedicated risk owner. Develop and execute remediation plan. Monitor progress weekly with status reports to risk committee.',
        timeline: '30 days',
      };
    case 'medium':
      return {
        title: 'Schedule Remediation',
        description: 'Include remediation in next sprint cycle. Monitor monthly with periodic status reviews. Document risk acceptance if deferred.',
        timeline: '90 days',
      };
    case 'low':
      return {
        title: 'Monitor and Review',
        description: 'Accept risk with documented justification or schedule periodic review. Include in quarterly risk assessment cycle.',
        timeline: 'Quarterly review',
      };
    default:
      return {
        title: 'Periodic Review',
        description: 'Include in routine risk assessment. No immediate action required.',
        timeline: 'Annual review',
      };
  }
}

function ScaleDots({ value, max = 5 }: { value: number; max?: number }) {
  return (
    <div className="flex items-center gap-1">
      {Array.from({ length: max }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 w-4 rounded-sm ${i < value ? 'bg-danger' : 'bg-muted'}`}
        />
      ))}
    </div>
  );
}

export function RiskDetailDrawer({ risk, open, onOpenChange }: RiskDetailDrawerProps) {
  if (!risk) return null;

  const recommendation = getMitigationRecommendation(risk.severity);
  const score = risk.likelihood * risk.impact;
  const matrixLevel = score >= 20 ? 'critical' : score >= 12 ? 'high' : score >= 6 ? 'medium' : 'low';

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 bg-card border-l border-border overflow-y-auto">
        {/* Sticky Header */}
        <div className="sticky top-0 z-10 bg-card/95 backdrop-blur border-b border-border p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className={`p-2 rounded-lg ${getRiskLevelBg(risk.severity)}`}>
                <ShieldAlert className="h-4 w-4" />
              </div>
              <div>
                <SheetHeader className="p-0">
                  <SheetTitle className="text-sm font-mono text-foreground">{risk.id}</SheetTitle>
                  <SheetDescription className="sr-only">Risk detail view with score, position, and mitigation recommendations</SheetDescription>
                </SheetHeader>
                <p className="text-[11px] text-muted-foreground mt-0.5">Risk Detail</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge variant="outline" className={`text-[10px] ${getRiskLevelBg(risk.severity)}`}>
                {getRiskLevelLabel(risk.severity)}
              </Badge>
              <Badge variant="outline" className="text-[10px] bg-muted text-muted-foreground border-muted-foreground/30 capitalize">
                {risk.status}
              </Badge>
            </div>
          </div>
        </div>

        <div className="p-4 space-y-5">
          {/* Risk Title & Description */}
          <div className="space-y-2">
            <h3 className="text-base font-semibold text-foreground">{risk.title}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{risk.description}</p>
          </div>

          {/* Risk Score Visualization */}
          <div className={`rounded-xl p-4 border ${
            risk.severity === 'critical' ? 'bg-danger/10 border-danger/30' :
            risk.severity === 'high' ? 'bg-warning/10 border-warning/30' :
            risk.severity === 'medium' ? 'bg-cyber/10 border-cyber/30' :
            'bg-success/10 border-success/30'
          }`}>
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-3">Risk Score</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-[10px] text-muted-foreground uppercase mb-1.5">Likelihood</p>
                <div className="flex items-center gap-2">
                  <ScaleDots value={risk.likelihood} />
                  <span className="text-sm font-bold text-foreground">{risk.likelihood}/5</span>
                </div>
              </div>
              <div>
                <p className="text-[10px] text-muted-foreground uppercase mb-1.5">Impact</p>
                <div className="flex items-center gap-2">
                  <ScaleDots value={risk.impact} />
                  <span className="text-sm font-bold text-foreground">{risk.impact}/5</span>
                </div>
              </div>
            </div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Residual Risk</span>
                <span className={`text-2xl font-bold ${getScoreColor(risk.residualRisk)}`}>{risk.residualRisk}%</span>
              </div>
              <div className="h-2.5 bg-muted/60 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    risk.residualRisk >= 70 ? 'bg-danger' :
                    risk.residualRisk >= 40 ? 'bg-warning' : 'bg-success'
                  }`}
                  style={{ width: `${risk.residualRisk}%` }}
                />
              </div>
            </div>
          </div>

          {/* Mini Risk Matrix */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Risk Position</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              <div className="grid grid-cols-6 gap-1 text-[9px]">
                {/* Header row */}
                <div className="text-muted-foreground text-right pr-1 self-center">L \ I</div>
                {[1, 2, 3, 4, 5].map((impact) => (
                  <div key={impact} className="text-center text-muted-foreground font-medium">{impact}</div>
                ))}
                {/* Matrix rows - likelihood 5 (top) to 1 (bottom) */}
                {[5, 4, 3, 2, 1].map((likelihood) => (
                  <React.Fragment key={likelihood}>
                    <div className="text-muted-foreground text-right pr-1 self-center font-medium">{likelihood}</div>
                    {[1, 2, 3, 4, 5].map((impact) => {
                      const cellScore = likelihood * impact;
                      const cellLevel = cellScore >= 20 ? 'critical' : cellScore >= 12 ? 'high' : cellScore >= 6 ? 'medium' : 'low';
                      const isCurrent = likelihood === risk.likelihood && impact === risk.impact;
                      const bgColor = cellLevel === 'critical' ? 'bg-danger/30' :
                                      cellLevel === 'high' ? 'bg-danger/15' :
                                      cellLevel === 'medium' ? 'bg-warning/15' : 'bg-success/15';
                      return (
                        <div
                          key={impact}
                          className={`aspect-square rounded flex items-center justify-center ${bgColor} ${
                            isCurrent ? 'ring-2 ring-primary ring-offset-1 ring-offset-card' : ''
                          }`}
                        >
                          {isCurrent && <div className="h-1.5 w-1.5 rounded-full bg-primary" />}
                        </div>
                      );
                    })}
                  </React.Fragment>
                ))}
              </div>
              <p className="text-[10px] text-muted-foreground mt-2 text-center">
                Likelihood (rows) × Impact (cols) — Current risk position highlighted
              </p>
            </div>
          </div>

          {/* Metadata Grid */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Details</h3>
            <div className="grid grid-cols-2 gap-2">
              <DetailItem icon={ShieldAlert} label="Framework" value={risk.framework} />
              <DetailItem icon={User} label="Owner" value={risk.owner} />
              <DetailItem
                icon={risk.trend === 'increasing' ? TrendingUp : risk.trend === 'decreasing' ? TrendingDown : Minus}
                label="Trend"
                value={risk.trend.charAt(0).toUpperCase() + risk.trend.slice(1)}
                valueColor={risk.trend === 'increasing' ? 'text-danger' : risk.trend === 'decreasing' ? 'text-success' : 'text-warning'}
              />
              <DetailItem icon={Target} label="Status" value={risk.status.charAt(0).toUpperCase() + risk.status.slice(1)} />
            </div>
          </div>

          {/* Affected Assets */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Affected Assets</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              <div className="flex flex-wrap gap-1.5">
                {risk.assets.map((asset) => (
                  <Badge key={asset} variant="outline" className="text-[10px] bg-card border-border">
                    {asset}
                  </Badge>
                ))}
              </div>
            </div>
          </div>

          {/* Linked Controls */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Linked Controls</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50">
              {risk.linkedControls.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {risk.linkedControls.map((control) => (
                    <Badge key={control} variant="outline" className="text-[10px] font-mono bg-card border-border text-primary">
                      {control}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-[10px] text-muted-foreground italic">No controls linked</p>
              )}
            </div>
          </div>

          {/* Evidence Summary */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Evidence Summary</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50 flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/15">
                <Database className="h-4 w-4 text-primary" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-bold text-foreground">{risk.evidenceCount}</p>
                <p className="text-[10px] text-muted-foreground">Evidence items linked</p>
              </div>
              {risk.evidenceCount === 0 && (
                <Badge variant="outline" className="text-[10px] bg-danger/15 text-danger border-danger/30">
                  No Evidence
                </Badge>
              )}
            </div>
          </div>

          {/* Mitigation Recommendation */}
          <div className={`rounded-lg p-4 border ${
            risk.severity === 'critical' ? 'bg-danger/5 border-danger/20' :
            risk.severity === 'high' ? 'bg-warning/5 border-warning/20' :
            'bg-surface border-border/50'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className={`h-4 w-4 ${getRiskLevelColor(risk.severity)}`} />
              <h3 className="text-xs font-semibold text-foreground">Mitigation Recommendation</h3>
            </div>
            <p className="text-sm font-medium text-foreground mb-1.5">{recommendation.title}</p>
            <p className="text-xs text-muted-foreground leading-relaxed mb-2">{recommendation.description}</p>
            <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground">
              <span className="font-medium">Timeline:</span>
              <span className="text-foreground">{recommendation.timeline}</span>
            </div>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur border-t border-border p-4 flex gap-2">
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Mitigate
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <FileText className="h-3.5 w-3.5" />
            Accept
          </Button>
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <User className="h-3.5 w-3.5" />
            Assign
          </Button>
        </div>
      </SheetContent>
    </Sheet>
  );
}

function DetailItem({ icon: Icon, label, value, valueColor }: {
  icon: React.ComponentType<{ className?: string }>,
  label: string,
  value: string,
  valueColor?: string,
}) {
  return (
    <div className="bg-surface rounded-lg p-2.5 border border-border/50">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="h-3 w-3 text-muted-foreground" />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <p className={`text-xs font-medium ${valueColor || 'text-foreground'} truncate`}>{value}</p>
    </div>
  );
}
