// M3 Assurance — live backend client, adapters and React Query hooks.

import { useQueries, useQuery } from '@tanstack/react-query';

import type { Framework, Report, ResilienceScore, Risk } from './types';

// ─── Backend response shapes ────────────────────────────────────────────

export interface RegistryFramework {
  framework_id: string;
  name: string;
  version: string;
  description: string;
  regions: string[];
}

export interface RegistryControl {
  control_id: string;
  framework_id: string;
  category: string;
  name: string;
  description: string;
  attack_mapping: string[];
}

export interface CrossWalkEntry {
  source_control_id: string;
  target_control_id: string;
  equivalence_level: string;
}

export interface M3Score {
  score_id: string;
  engagement_id: string;
  composite_score: number;
  coverage_score: number;
  detection_score: number;
  evidence_score: number;
  band: string;
}

export interface M3EvidenceSummary {
  engagement_id: string;
  total_links: number;
  unique_hashes: number;
  completeness_pct: number;
}

export interface M3EvidenceLink {
  link_id: string;
  control_id: string;
  verdict_id: string;
  evidence_hash: string;
  chain_position: number;
}

export interface M3Verdict {
  verdict_id: string;
  engagement_id: string;
  technique_id: string;
  outcome: string;
  severity_id: number | null;
  evidence_hash: string | null;
}

export interface M3ControlStatuses {
  engagement_id: string;
  control_statuses: Record<string, string>;
  coverage_pct: number;
  framework_ids: string[];
}

export interface M3Gap {
  analysis_id: string;
  engagement_id: string;
  control_id: string;
  gap_type: string;
  priority: number;
  remediation: string;
}

export interface M3Report {
  report_id: string;
  engagement_id: string;
  framework_ids: string[];
  composite_score: number;
  format: string;
  content_hash: string;
}

export interface M3Engagement {
  engagement_id: string;
  name: string;
  organization: string;
  frameworks: string[];
}

// ─── Typed gateway client ───────────────────────────────────────────────

const GATEWAY = '/api/m3';

async function request<T>(service: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${GATEWAY}/${service}/${path}`, init);
  if (!res.ok) {
    let detail = `${res.status}`;
    try {
      const body = (await res.json()) as { detail?: unknown };
      if (body.detail !== undefined) detail = String(body.detail).slice(0, 240);
    } catch {
      /* non-JSON error body */
    }
    throw new Error(`M3 ${service}/${path}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

function jsonInit(method: string, payload: unknown): RequestInit {
  return {
    method,
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  };
}

export const m3 = {
  frameworks: () => request<RegistryFramework[]>('registry', 'frameworks'),
  frameworkControls: (frameworkId: string) =>
    request<RegistryControl[]>(
      'registry',
      `frameworks/${encodeURIComponent(frameworkId)}/controls`,
    ),
  controlCrosswalks: (controlId: string) =>
    request<CrossWalkEntry[]>(
      'registry',
      `controls/${encodeURIComponent(controlId)}/crosswalks`,
    ),
  scores: (engagementId: string) =>
    request<M3Score[]>(`scorer`, `scores/${encodeURIComponent(engagementId)}`),
  evidenceSummary: (engagementId: string) =>
    request<M3EvidenceSummary>(
      'evidence',
      `evidence-summary/${encodeURIComponent(engagementId)}`,
    ),
  evidenceLinks: (verdictId?: string) => {
    const query = verdictId ? `?verdict_id=${encodeURIComponent(verdictId)}` : '';
    return request<M3EvidenceLink[]>('evidence', `evidence-links${query}`);
  },
  verdicts: (engagementId: string) =>
    request<M3Verdict[]>(
      'evidence',
      `verdicts/${encodeURIComponent(engagementId)}/engagement`,
    ),
  engagements: () => request<M3Engagement[]>('evidence', 'engagements'),
  reports: (engagementId: string) =>
    request<M3Report[]>(
      'reports',
      `reports?engagement_id=${encodeURIComponent(engagementId)}`,
    ),
  controlStatuses: (engagementId: string) =>
    request<M3ControlStatuses>(
      'mapping',
      `control-statuses/${encodeURIComponent(engagementId)}`,
    ),
  gaps: (engagementId: string) =>
    request<M3Gap[]>('gaps', `gaps/${encodeURIComponent(engagementId)}`),
  generateReport: (
    engagementId: string,
    frameworkIds: string[],
    format: string,
  ) =>
    request<M3Report>(
      'reports',
      'generate-report',
      jsonInit('POST', { engagement_id: engagementId, framework_ids: frameworkIds, format }),
    ),
  calculateScore: (engagementId: string) =>
    request<M3Score>(
      'scorer',
      'calculate-score',
      jsonInit('POST', { engagement_id: engagementId }),
    ),
  analyzeGaps: (engagementId: string) =>
    request<{ engagement_id: string; total_gaps: number; critical_gaps: number; gaps: M3Gap[] }>(
      'gaps',
      'analyze-gaps',
      jsonInit('POST', { engagement_id: engagementId }),
    ),
  publishReport: (reportId: string, channel: string, recipient: string) =>
    request<{ delivery_id: string; report_id: string; channel: string; recipient: string; status: string }>(
      'publish',
      'publish',
      jsonInit('POST', { report_id: reportId, channel, recipient }),
    ),
};

// ─── Adapters (backend shapes -> dashboard domain) ──────────────────────

const BAND_TO_RISK_LEVEL: Record<string, Risk['severity']> = {
  Critical: 'critical',
  'At Risk': 'high',
  Moderate: 'medium',
  Strong: 'low',
  Resilient: 'negligible',
};

export function frameworkCompliance(
  statuses: Record<string, string>,
  controlsByFramework: Map<string, RegistryControl[]>,
): Map<string, number> {
  const result = new Map<string, number>();
  const counts = new Map<string, { met: number; total: number }>();
  for (const [controlId, status] of Object.entries(statuses)) {
    let fw: string | undefined;
    for (const [frameworkId, controls] of controlsByFramework) {
      if (controls.some((control) => control.control_id === controlId)) {
        fw = frameworkId;
        break;
      }
    }
    const owner = fw ?? 'unknown';
    const entry = counts.get(owner) ?? { met: 0, total: 0 };
    entry.total += 1;
    if (status === 'Met') entry.met += 1;
    counts.set(owner, entry);
  }
  for (const [frameworkId, entry] of counts) {
    result.set(
      frameworkId,
      entry.total === 0 ? 0 : Math.round((entry.met / entry.total) * 100),
    );
  }
  return result;
}

export function m3ReportToDashboard(m: M3Report): Report {
  return {
    id: m.report_id,
    title: `Compliance report (${m.framework_ids.length} framework${m.framework_ids.length === 1 ? '' : 's'})`,
    type: 'Compliance',
    framework: m.framework_ids.join(', '),
    status: 'generated',
    generatedAt: new Date().toISOString(),
    businessUnit: '',
    dateRange: { start: '', end: '' },
    complianceScore: m.composite_score,
    resilienceScore: m.composite_score,
    controlsCovered: 0,
    evidenceLinked: 0,
    risksIdentified: 0,
    author: 'M3 Pipeline',
    downloaded: false,
    shared: false,
  };
}

// ─── React Query hooks ──────────────────────────────────────────────────

export function useM3Frameworks() {
  return useQuery({
    queryKey: ['m3', 'frameworks'],
    queryFn: m3.frameworks,
    staleTime: 5 * 60 * 1000,
  });
}

export function useM3Engagements() {
  return useQuery({
    queryKey: ['m3', 'engagements'],
    queryFn: m3.engagements,
  });
}

export function useM3Reports(engagementId: string) {
  return useQuery({
    queryKey: ['m3', 'reports', engagementId],
    queryFn: () => m3.reports(engagementId),
    enabled: Boolean(engagementId),
  });
}

/**
 * Aggregate hook: assembles a live, dashboard-shaped view of an engagement
 * from the seven backend services.
 */
export function useAssuranceDashboard(engagementId: string) {
  const scoreQuery = useQuery({
    queryKey: ['m3', 'score', engagementId],
    queryFn: () => m3.scores(engagementId),
    enabled: Boolean(engagementId),
  });
  const summaryQuery = useQuery({
    queryKey: ['m3', 'evidence-summary', engagementId],
    queryFn: () => m3.evidenceSummary(engagementId),
    enabled: Boolean(engagementId),
  });
  const statusesQuery = useQuery({
    queryKey: ['m3', 'statuses', engagementId],
    queryFn: () => m3.controlStatuses(engagementId),
    enabled: Boolean(engagementId),
  });
  const gapsQuery = useQuery({
    queryKey: ['m3', 'gaps', engagementId],
    queryFn: () => m3.gaps(engagementId),
    enabled: Boolean(engagementId),
  });
  const linksQuery = useQuery({
    queryKey: ['m3', 'evidence-links'],
    queryFn: () => m3.evidenceLinks(),
    enabled: Boolean(engagementId),
  });
  const frameworksQuery = useM3Frameworks();
  const verdictsQuery = useQuery({
    queryKey: ['m3', 'verdicts', engagementId],
    queryFn: () => m3.verdicts(engagementId),
    enabled: Boolean(engagementId),
  });

  const frameworkIds = statusesQuery.data?.framework_ids ?? [];
  const controlsQueries = useQueries({
    queries: frameworkIds.map((frameworkId) => ({
      queryKey: ['m3', 'controls', frameworkId],
      queryFn: () => m3.frameworkControls(frameworkId),
      enabled: true,
      staleTime: 10 * 60 * 1000,
    })),
  });

  const loading = [
    scoreQuery,
    summaryQuery,
    statusesQuery,
    gapsQuery,
    linksQuery,
    frameworksQuery,
    verdictsQuery,
    ...controlsQueries,
  ].some((query) => query.isPending);
  const error =
    [scoreQuery, summaryQuery, statusesQuery, gapsQuery, linksQuery, frameworksQuery, verdictsQuery].find(
      (query) => query.isError,
    )?.error ?? null;

  const controlsByFramework = new Map<string, RegistryControl[]>();
  frameworkIds.forEach((frameworkId, index) => {
    const controls = controlsQueries[index]?.data;
    if (controls) controlsByFramework.set(frameworkId, controls);
  });

  const statuses = statusesQuery.data?.control_statuses ?? {};
  const complianceByFramework = frameworkCompliance(statuses, controlsByFramework);
  const frameworkCounts = new Map<string, { covered: number; linked: number }>();
  for (const controlId of Object.keys(statuses)) {
    for (const [frameworkId, controls] of controlsByFramework) {
      if (controls.some((control) => control.control_id === controlId)) {
        const entry = frameworkCounts.get(frameworkId) ?? { covered: 0, linked: 0 };
        entry.covered += 1;
        frameworkCounts.set(frameworkId, entry);
        break;
      }
    }
  }
  const linkCountByFramework = new Map<string, number>();
  for (const link of linksQuery.data ?? []) {
    for (const [frameworkId, controls] of controlsByFramework) {
      if (controls.some((control) => control.control_id === link.control_id)) {
        linkCountByFramework.set(
          frameworkId,
          (linkCountByFramework.get(frameworkId) ?? 0) + 1,
        );
        break;
      }
    }
  }

  const evaluatedControls: RegistryControl[] = [...controlsByFramework.values()].flat();

  const frameworks: Framework[] = (frameworksQuery.data ?? []).map((fw) => {
    const covered = frameworkCounts.get(fw.framework_id)?.covered ?? 0;
    const linked = linkCountByFramework.get(fw.framework_id) ?? 0;
    const compliance = complianceByFramework.get(fw.framework_id) ?? 0;
    return {
      id: fw.framework_id,
      name: fw.name,
      version: fw.version,
      status: covered > 0 ? 'active' : 'inactive',
      compliance,
      controlsTotal: (controlsByFramework.get(fw.framework_id) ?? []).length || (covered || 0),
      controlsCovered: covered,
      evidenceLinked: linked,
      riskLevel: 'medium',
      lastSync: '',
      description: fw.description,
      domains: [],
    };
  });

  const scores = scoreQuery.data ?? [];
  const latestScore = scores[0] ?? null;
  const band = latestScore?.band ?? '';
  const gaps = gapsQuery.data ?? [];
  const criticalGaps = gaps.filter((gap) => gap.priority === 1).length;

  const score: ResilienceScore = latestScore
    ? {
        overall: latestScore.composite_score,
        compliance: latestScore.coverage_score,
        risk: Math.max(0, 100 - latestScore.detection_score),
        controlCoverage: latestScore.coverage_score,
        evidenceCoverage: latestScore.evidence_score,
        openRisks: gaps.length,
        criticalRisks: criticalGaps,
        formula: {
          evidenceConfidence: latestScore.evidence_score / 100,
          controlWeight: 0.4,
          frameworkWeight: 0,
          riskWeight: 0.35,
          businessImpact: 0,
        },
        history: scores.map((entry, index) => ({
          date: `${index + 1}`,
          score: entry.composite_score,
        })),
      }
    : {
        overall: 0,
        compliance: 0,
        risk: 0,
        controlCoverage: 0,
        evidenceCoverage: 0,
        openRisks: gaps.length,
        criticalRisks: criticalGaps,
        formula: {
          evidenceConfidence: 0,
          controlWeight: 0.4,
          frameworkWeight: 0,
          riskWeight: 0.35,
          businessImpact: 0,
        },
        history: [],
      };

  const residualRiskForPriority: Record<number, number> = { 1: 90, 2: 70, 3: 50, 4: 30, 5: 10 };
  const severityForPriority: Record<number, Risk['severity']> = {
    1: 'critical',
    2: 'high',
    3: 'medium',
    4: 'low',
    5: 'negligible',
  };
  const risks: Risk[] = gaps.map((gap, index) => ({
    id: gap.analysis_id || `GAP-${index}`,
    title: `${gap.control_id} — ${gap.gap_type}`,
    severity: severityForPriority[gap.priority] ?? 'medium',
    likelihood: Math.max(1, Math.min(5, gap.priority + 1)),
    impact: Math.max(1, Math.min(5, 6 - gap.priority)),
    framework: '',
    linkedControls: [gap.control_id],
    evidenceCount: 0,
    assets: [],
    residualRisk: residualRiskForPriority[gap.priority] ?? 50,
    trend: 'stable',
    status: gap.priority <= 2 ? 'open' : 'accepted',
    owner: '',
    description: gap.remediation,
  }));

  return {
    loading,
    error,
    engagementId,
    frameworks,
    score,
    band,
    risks,
    gaps,
    criticalGaps,
    verdicts: verdictsQuery.data ?? [],
    totalLinks: summaryQuery.data?.total_links ?? 0,
    uniqueHashes: summaryQuery.data?.unique_hashes ?? 0,
    completenessPct: summaryQuery.data?.completeness_pct ?? 0,
    controlsMapped: Object.keys(statuses).length,
    coveragePct: statusesQuery.data?.coverage_pct ?? 0,
    evaluatedFrameworkIds: frameworkIds,
    evaluatedControls,
    controlStatusMap: statuses,
    evidenceLinks: linksQuery.data ?? [],
  };
}