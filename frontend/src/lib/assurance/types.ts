// CyBreach Assurance Module - Type Definitions

export type ComplianceStatus = 'compliant' | 'partially_compliant' | 'non_compliant' | 'not_assessed';
export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'negligible';
export type ValidationStatus = 'validated' | 'pending' | 'expired' | 'rejected';
export type EvidenceType = 'automated_scan' | 'manual_review' | 'policy_document' | 'configuration' | 'log_evidence' | 'interview' | 'observation';
export type ReportStatus = 'generated' | 'scheduled' | 'pending' | 'failed' | 'draft';
export type FrameworkStatus = 'active' | 'inactive' | 'draft' | 'deprecated';

export interface Framework {
  id: string;
  name: string;
  version: string;
  status: FrameworkStatus;
  compliance: number;
  controlsTotal: number;
  controlsCovered: number;
  evidenceLinked: number;
  riskLevel: RiskLevel;
  lastSync: string;
  description: string;
  domains: Domain[];
}

export interface Domain {
  id: string;
  name: string;
  frameworkId: string;
  categories: Category[];
}

export interface Category {
  id: string;
  name: string;
  domainId: string;
  controls: Control[];
}

export interface Control {
  id: string;
  controlRef: string;
  title: string;
  description: string;
  frameworkId: string;
  domain: string;
  category: string;
  owner: string;
  priority: RiskLevel;
  complianceStatus: ComplianceStatus;
  evidenceCount: number;
  riskMapping: string[];
  lastValidation: string;
  mappedControls: MappedControl[];
  requiredEvidence: number;
  availableEvidence: number;
  missingEvidence: number;
  confidence: number;
}

export interface MappedControl {
  framework: string;
  controlRef: string;
  title: string;
  confidence: number;
}

export interface Evidence {
  id: string;
  asset: string;
  source: string;
  framework: string;
  control: string;
  controlRef: string;
  evidenceType: EvidenceType;
  validationStatus: ValidationStatus;
  timestamp: string;
  confidenceScore: number;
  owner: string;
  immutableHash: string;
  description: string;
  metadata: Record<string, string>;
  linkedControls: string[];
  linkedRisks: string[];
  linkedReports: string[];
  auditTrail: AuditEvent[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  module: string;
  actor: string;
  hash: string;
  status: string;
  description: string;
}

export interface MissingEvidence {
  controlId: string;
  controlRef: string;
  controlTitle: string;
  framework: string;
  issue: 'missing' | 'expired' | 'weak' | 'duplicate' | 'invalid';
  severity: RiskLevel;
  remediation: string;
  dueDate: string;
}

export interface Risk {
  id: string;
  title: string;
  severity: RiskLevel;
  likelihood: number;
  impact: number;
  framework: string;
  linkedControls: string[];
  evidenceCount: number;
  assets: string[];
  residualRisk: number;
  trend: 'increasing' | 'stable' | 'decreasing';
  status: 'open' | 'mitigated' | 'accepted' | 'closed';
  owner: string;
  description: string;
}

export interface ResilienceScore {
  overall: number;
  compliance: number;
  risk: number;
  controlCoverage: number;
  evidenceCoverage: number;
  openRisks: number;
  criticalRisks: number;
  formula: {
    evidenceConfidence: number;
    controlWeight: number;
    frameworkWeight: number;
    riskWeight: number;
    businessImpact: number;
  };
  history: { date: string; score: number }[];
}

export interface GapAnalysis {
  missingControls: { id: string; title: string; framework: string; priority: RiskLevel }[];
  weakControls: { id: string; title: string; framework: string; evidence: number; required: number }[];
  highRiskAreas: { name: string; riskCount: number; framework: string }[];
  frameworkGaps: { framework: string; gap: number; description: string }[];
  evidenceGaps: { framework: string; missing: number; total: number }[];
  recommendations: { title: string; priority: RiskLevel; impact: string; effort: string }[];
}

export interface Report {
  id: string;
  title: string;
  type: string;
  framework: string;
  status: ReportStatus;
  generatedAt: string;
  scheduledAt?: string;
  businessUnit: string;
  dateRange: { start: string; end: string };
  complianceScore: number;
  resilienceScore: number;
  controlsCovered: number;
  evidenceLinked: number;
  risksIdentified: number;
  author: string;
  downloaded: boolean;
  shared: boolean;
}

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  framework?: string;
  category: string;
  lastUsed: string;
  usageCount: number;
}

export interface Notification {
  id: string;
  type: 'evidence_missing' | 'validation_failed' | 'framework_updated' | 'risk_increased' | 'report_generated' | 'approval_required';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
  severity: 'info' | 'warning' | 'error' | 'success';
  source: string;
}

export type TaskStatus = 'todo' | 'in_progress' | 'review' | 'done' | 'blocked';
export type TaskPriority = 'critical' | 'high' | 'medium' | 'low';
export type TaskType = 'evidence_collection' | 'control_testing' | 'remediation' | 'review' | 'approval' | 'audit_prep';

export interface GrcTask {
  id: string;
  title: string;
  description: string;
  type: TaskType;
  status: TaskStatus;
  priority: TaskPriority;
  assignee: string;
  assigneeInitials: string;
  framework: string;
  controlRef?: string;
  dueDate: string;
  createdAt: string;
  progress: number;
  tags: string[];
}

export type SectionId = 'dashboard' | 'frameworks' | 'evidence' | 'risk' | 'reports' | 'tasks' | 'notifications' | 'settings' | 'audit-logs';
