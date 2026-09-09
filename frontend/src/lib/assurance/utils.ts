import type { ComplianceStatus, RiskLevel, ValidationStatus, FrameworkStatus, ReportStatus } from './types';

export function getComplianceStatusColor(status: ComplianceStatus): string {
  switch (status) {
    case 'compliant': return 'text-success';
    case 'partially_compliant': return 'text-warning';
    case 'non_compliant': return 'text-danger';
    case 'not_assessed': return 'text-muted-foreground';
  }
}

export function getComplianceStatusBg(status: ComplianceStatus): string {
  switch (status) {
    case 'compliant': return 'bg-success/15 text-success border-success/30';
    case 'partially_compliant': return 'bg-warning/15 text-warning border-warning/30';
    case 'non_compliant': return 'bg-danger/15 text-danger border-danger/30';
    case 'not_assessed': return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

export function getComplianceStatusLabel(status: ComplianceStatus): string {
  switch (status) {
    case 'compliant': return 'Compliant';
    case 'partially_compliant': return 'Partial';
    case 'non_compliant': return 'Non-Compliant';
    case 'not_assessed': return 'Not Assessed';
  }
}

export function getRiskLevelColor(level: RiskLevel): string {
  switch (level) {
    case 'critical': return 'text-danger';
    case 'high': return 'text-warning';
    case 'medium': return 'text-cyber';
    case 'low': return 'text-success';
    case 'negligible': return 'text-muted-foreground';
  }
}

export function getRiskLevelBg(level: RiskLevel): string {
  switch (level) {
    case 'critical': return 'bg-danger/15 text-danger border-danger/30';
    case 'high': return 'bg-warning/15 text-warning border-warning/30';
    case 'medium': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'low': return 'bg-success/15 text-success border-success/30';
    case 'negligible': return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

export function getRiskLevelLabel(level: RiskLevel): string {
  return level.charAt(0).toUpperCase() + level.slice(1);
}

export function getValidationStatusColor(status: ValidationStatus): string {
  switch (status) {
    case 'validated': return 'bg-success/15 text-success border-success/30';
    case 'pending': return 'bg-warning/15 text-warning border-warning/30';
    case 'expired': return 'bg-danger/15 text-danger border-danger/30';
    case 'rejected': return 'bg-danger/15 text-danger border-danger/30';
  }
}

export function getValidationStatusLabel(status: ValidationStatus): string {
  return status.charAt(0).toUpperCase() + status.slice(1);
}

export function getFrameworkStatusColor(status: FrameworkStatus): string {
  switch (status) {
    case 'active': return 'bg-success/15 text-success border-success/30';
    case 'inactive': return 'bg-muted text-muted-foreground border-muted-foreground/30';
    case 'draft': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'deprecated': return 'bg-danger/15 text-danger border-danger/30';
  }
}

export function getReportStatusColor(status: ReportStatus): string {
  switch (status) {
    case 'generated': return 'bg-success/15 text-success border-success/30';
    case 'scheduled': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'pending': return 'bg-warning/15 text-warning border-warning/30';
    case 'failed': return 'bg-danger/15 text-danger border-danger/30';
    case 'draft': return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

export function getScoreColor(score: number): string {
  if (score >= 80) return 'text-success';
  if (score >= 60) return 'text-warning';
  return 'text-danger';
}

export function getScoreBg(score: number): string {
  if (score >= 80) return 'bg-success/10';
  if (score >= 60) return 'bg-warning/10';
  return 'bg-danger/10';
}

export function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return dateStr;
  }
}

export function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' });
  } catch {
    return dateStr;
  }
}

export function timeAgo(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  if (seconds < 60) return 'just now';
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return formatDate(dateStr);
}

export function truncateHash(hash: string): string {
  if (hash.startsWith('sha256:')) {
    return hash.substring(0, 18) + '...' + hash.substring(hash.length - 6);
  }
  return hash.substring(0, 12) + '...';
}
