'use client';

import React, { useState, useMemo } from 'react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Input } from '@/components/ui/input';
import { Separator } from '@/components/ui/separator';
import {
  FileText,
  Download,
  Share2,
  Plus,
  BarChart3,
  LayoutGrid,
  FileCheck,
  Clock,
  FilePen,
  ChevronLeft,
  ChevronRight,
  Check,
  Zap,
  Shield,
  AlertTriangle,
  Eye,
  Table,
  FileSpreadsheet,
  ArrowRight,
  Search,
  ArrowUpDown,
  TrendingUp,
  TrendingDown,
} from 'lucide-react';
import { reportTemplates, controls, risks, evidenceItems } from '@/lib/assurance/mock-data';
import { getReportStatusColor, getScoreColor, formatDate } from '@/lib/assurance/utils';
import type { Report, ReportStatus } from '@/lib/assurance/types';
import {
  exportToJSON,
  timestampForFilename,
  sanitizeFilenameSegment,
} from '@/lib/assurance/export-utils';
import { ReportDetailDrawer } from './ReportDetailDrawer';
import { useReportsStore } from '@/hooks/use-reports';
import { useRecentlyViewedStore } from '@/hooks/use-recently-viewed';
import { usePermission } from '@/components/assurance/shared/PermissionGate';
import { Lock } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

// ===================== KPI Card =====================
function KpiCard({
  icon: Icon,
  value,
  label,
  color,
  bg,
}: {
  icon: React.ElementType;
  value: string | number;
  label: string;
  color: string;
  bg: string;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 hover:border-primary/30 transition-colors">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs text-muted-foreground font-medium">{label}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <div className={`p-2 rounded-lg ${bg}`}>
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
      </div>
    </div>
  );
}

// ===================== Tab 1: Reports Dashboard =====================
function ReportsDashboard({ onSelectReport }: { onSelectReport: (id: string) => void }) {
  const reports = useReportsStore((state) => state.reports);
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [frameworkFilter, setFrameworkFilter] = useState('all');
  const [sortBy, setSortBy] = useState<'date' | 'compliance' | 'title'>('date');

  const totalReports = reports.length;
  const generatedReports = reports.filter((r) => r.status === 'generated').length;
  const scheduledReports = reports.filter((r) => r.status === 'scheduled').length;
  const draftReports = reports.filter((r) => r.status === 'draft').length;

  const uniqueFrameworks = useMemo(() => Array.from(new Set(reports.map((r) => r.framework))), [reports]);

  function handleQuickDownload(report: Report) {
    const filename = `cybreach_report_${sanitizeFilenameSegment(report.title)}_${timestampForFilename()}`;
    exportToJSON(report, filename);
    toast({
      title: 'Report exported',
      description: `${report.title} downloaded as JSON.`,
    });
  }

  const filteredReports = useMemo(() => {
    let result = reports.filter((r) => {
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || r.title.toLowerCase().includes(q) || r.type.toLowerCase().includes(q) || r.id.toLowerCase().includes(q);
      const matchStatus = statusFilter === 'all' || r.status === statusFilter;
      const matchFramework = frameworkFilter === 'all' || r.framework === frameworkFilter;
      return matchSearch && matchStatus && matchFramework;
    });

    result = [...result].sort((a, b) => {
      if (sortBy === 'compliance') return b.complianceScore - a.complianceScore;
      if (sortBy === 'title') return a.title.localeCompare(b.title);
      // date - default
      const dateA = a.generatedAt || a.scheduledAt || '';
      const dateB = b.generatedAt || b.scheduledAt || '';
      return new Date(dateB).getTime() - new Date(dateA).getTime();
    });

    return result;
  }, [reports, searchQuery, statusFilter, frameworkFilter, sortBy]);

  return (
    <div className="space-y-6">
      {/* KPI Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KpiCard icon={FileText} value={totalReports} label="Total Reports" color="text-foreground" bg="bg-primary/10" />
        <KpiCard icon={FileCheck} value={generatedReports} label="Generated Reports" color="text-success" bg="bg-success/10" />
        <KpiCard icon={Clock} value={scheduledReports} label="Scheduled Reports" color="text-cyber" bg="bg-cyber/10" />
        <KpiCard icon={FilePen} value={draftReports} label="Draft Reports" color="text-muted-foreground" bg="bg-muted" />
      </div>

      {/* Reports List with Filters */}
      <div className="bg-card border border-border rounded-lg p-5">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Reports</h2>
            <p className="text-[11px] text-muted-foreground mt-0.5">{filteredReports.length} of {reports.length} reports shown</p>
          </div>
        </div>

        {/* Filters Bar */}
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search reports..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 h-8 text-xs bg-surface border-border"
            />
          </div>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="w-[140px] h-8 text-xs" size="sm">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Statuses</SelectItem>
              <SelectItem value="generated">Generated</SelectItem>
              <SelectItem value="scheduled">Scheduled</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="draft">Draft</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
            </SelectContent>
          </Select>
          <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
            <SelectTrigger className="w-[150px] h-8 text-xs" size="sm">
              <SelectValue placeholder="Framework" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Frameworks</SelectItem>
              {uniqueFrameworks.map((fw) => (
                <SelectItem key={fw} value={fw}>{fw}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={sortBy} onValueChange={(v) => setSortBy(v as 'date' | 'compliance' | 'title')}>
            <SelectTrigger className="w-[140px] h-8 text-xs" size="sm">
              <ArrowUpDown className="h-3 w-3 mr-1" />
              <SelectValue placeholder="Sort" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="date">Sort: Date</SelectItem>
              <SelectItem value="compliance">Sort: Compliance</SelectItem>
              <SelectItem value="title">Sort: Title</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Reports List */}
        <div className="space-y-2 max-h-[420px] overflow-y-auto pr-1 custom-scrollbar">
          {filteredReports.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-2 opacity-50" />
              <p className="text-sm text-muted-foreground">No reports match your filters</p>
              <Button
                variant="ghost"
                size="sm"
                className="mt-2 text-xs"
                onClick={() => { setSearchQuery(''); setStatusFilter('all'); setFrameworkFilter('all'); }}
              >
                Clear filters
              </Button>
            </div>
          ) : (
            filteredReports.map((report) => (
              <div
                key={report.id}
                className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border/50 hover:border-primary/30 transition-colors cursor-pointer group"
                onClick={() => onSelectReport(report.id)}
              >
                <div className="min-w-0 flex-1 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="text-xs font-medium text-foreground truncate group-hover:text-primary transition-colors">{report.title}</p>
                    <Badge variant="outline" className="text-[10px] px-1.5 py-0">{report.type}</Badge>
                    <span className="text-[10px] font-mono text-muted-foreground">{report.id}</span>
                  </div>
                  <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
                    <span>{report.framework}</span>
                    <span className="text-border">|</span>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-semibold border capitalize ${getReportStatusColor(report.status)}`}>
                      {report.status}
                    </span>
                    <span className="text-border">|</span>
                    <span className={getScoreColor(report.complianceScore)}>{report.complianceScore}% compliance</span>
                  </div>
                </div>
                <div className="flex items-center gap-1 ml-3">
                  <span className="text-[11px] text-muted-foreground mr-2">
                    {report.generatedAt ? formatDate(report.generatedAt) : report.scheduledAt ? `Scheduled: ${formatDate(report.scheduledAt)}` : '—'}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7"
                    aria-label={`Download ${report.title} as JSON`}
                    onClick={(e) => { e.stopPropagation(); handleQuickDownload(report); }}
                  >
                    <Download className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                  <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); }}>
                    <Share2 className="h-3.5 w-3.5 text-muted-foreground" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// ===================== Tab 2: Report Builder Wizard =====================
const WIZARD_STEPS = [
  { label: 'Framework', icon: Shield },
  { label: 'Business Unit', icon: BarChart3 },
  { label: 'Date Range', icon: Clock },
  { label: 'Controls', icon: FileCheck },
  { label: 'Evidence', icon: Eye },
  { label: 'Risk Summary', icon: AlertTriangle },
  { label: 'Preview', icon: LayoutGrid },
  { label: 'Generate', icon: Zap },
];

const FRAMEWORKS = ['ISO 27001', 'GDPR', 'NIST CSF', 'DPDP', 'PCI-DSS', 'All'];
const BUSINESS_UNITS = ['Enterprise', 'Payment Services', 'Data Privacy', 'India Operations', 'Board'];
const EVIDENCE_TYPES = ['Automated Scan', 'Manual Review', 'Policy Document', 'Configuration', 'Log Evidence', 'Interview', 'Observation'];

function ReportBuilderWizard({
  onGenerate,
  onComplete,
}: {
  onGenerate: (report: Report) => void;
  onComplete: () => void;
}) {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedFramework, setSelectedFramework] = useState('ISO 27001');
  const [selectedBusinessUnit, setSelectedBusinessUnit] = useState('Enterprise');
  const [dateStart, setDateStart] = useState('2024-10-01');
  const [dateEnd, setDateEnd] = useState('2024-12-31');
  const [selectedControls, setSelectedControls] = useState<Set<string>>(new Set(['ctrl-001', 'ctrl-002']));
  const [selectedEvidenceTypes, setSelectedEvidenceTypes] = useState<Set<string>>(new Set(['Automated Scan', 'Policy Document']));
  const [generated, setGenerated] = useState(false);
  const canGenerate = usePermission('canGenerate');

  const first5Controls = controls.slice(0, 5);

  function toggleControl(id: string) {
    setSelectedControls((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleEvidenceType(type: string) {
    setSelectedEvidenceTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function handleGenerate() {
    // Calculate mock metrics derived from wizard selections
    const evidenceCount = evidenceItems.filter((e) => {
      const typeLabel = e.evidenceType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
      return selectedEvidenceTypes.has(typeLabel);
    }).length || selectedEvidenceTypes.size * 4;

    const newReport: Report = {
      id: `RPT-${new Date().getFullYear()}-${String(Date.now()).slice(-3)}`,
      title: `${selectedFramework} Compliance Report`,
      type: 'Custom Report',
      framework: selectedFramework,
      status: 'generated',
      generatedAt: new Date().toISOString(),
      businessUnit: selectedBusinessUnit,
      dateRange: { start: dateStart, end: dateEnd },
      complianceScore: 75,
      resilienceScore: 72,
      controlsCovered: selectedControls.size,
      evidenceLinked: evidenceCount,
      risksIdentified: risks.length,
      author: 'Alex Kowalski',
      downloaded: false,
      shared: false,
    };

    onGenerate(newReport);
    setGenerated(true);
  }

  function handleReset() {
    setCurrentStep(0);
    setGenerated(false);
  }

  // Step content renderer
  function renderStepContent() {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Select Framework</h3>
            <p className="text-xs text-muted-foreground">Choose the compliance framework for this report.</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {FRAMEWORKS.map((fw) => (
                <button
                  key={fw}
                  onClick={() => setSelectedFramework(fw)}
                  className={`p-3 rounded-lg border text-left transition-all ${
                    selectedFramework === fw
                      ? 'border-primary bg-primary/10 text-primary'
                      : 'border-border bg-surface hover:border-primary/30 text-foreground'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
                        selectedFramework === fw ? 'border-primary' : 'border-muted-foreground/40'
                      }`}
                    >
                      {selectedFramework === fw && <div className="w-2 h-2 rounded-full bg-primary" />}
                    </div>
                    <span className="text-xs font-medium">{fw}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Select Business Unit</h3>
            <p className="text-xs text-muted-foreground">Choose the business unit this report covers.</p>
            <Select value={selectedBusinessUnit} onValueChange={setSelectedBusinessUnit}>
              <SelectTrigger className="w-full sm:w-64">
                <SelectValue placeholder="Select business unit" />
              </SelectTrigger>
              <SelectContent>
                {BUSINESS_UNITS.map((bu) => (
                  <SelectItem key={bu} value={bu}>
                    {bu}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 mt-2">
              {BUSINESS_UNITS.map((bu) => (
                <button
                  key={bu}
                  onClick={() => setSelectedBusinessUnit(bu)}
                  className={`p-2 rounded-md border text-xs text-center transition-all ${
                    selectedBusinessUnit === bu
                      ? 'border-primary bg-primary/10 text-primary font-medium'
                      : 'border-border bg-surface hover:border-primary/30 text-muted-foreground'
                  }`}
                >
                  {bu}
                </button>
              ))}
            </div>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Choose Date Range</h3>
            <p className="text-xs text-muted-foreground">Define the reporting period for the compliance assessment.</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground font-medium">Start Date</label>
                <Input
                  type="date"
                  value={dateStart}
                  onChange={(e) => setDateStart(e.target.value)}
                  className="bg-surface"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs text-muted-foreground font-medium">End Date</label>
                <Input
                  type="date"
                  value={dateEnd}
                  onChange={(e) => setDateEnd(e.target.value)}
                  className="bg-surface"
                />
              </div>
            </div>
          </div>
        );

      case 3:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Select Controls</h3>
            <p className="text-xs text-muted-foreground">Choose which controls to include in the report.</p>
            <div className="space-y-2">
              {first5Controls.map((ctrl) => (
                <div
                  key={ctrl.id}
                  className="flex items-center gap-3 p-2.5 rounded-md bg-surface border border-border/50 hover:border-primary/30 transition-colors"
                >
                  <Checkbox
                    checked={selectedControls.has(ctrl.id)}
                    onCheckedChange={() => toggleControl(ctrl.id)}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-medium text-foreground">{ctrl.controlRef}</span>
                      <span className="text-xs text-muted-foreground truncate">{ctrl.title}</span>
                    </div>
                    <span className="text-[11px] text-muted-foreground">{ctrl.domain} · {ctrl.category}</span>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-[10px] ${
                      ctrl.complianceStatus === 'compliant'
                        ? 'text-success border-success/30'
                        : ctrl.complianceStatus === 'partially_compliant'
                        ? 'text-warning border-warning/30'
                        : 'text-danger border-danger/30'
                    }`}
                  >
                    {ctrl.complianceStatus.replace('_', ' ')}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Attach Evidence</h3>
            <p className="text-xs text-muted-foreground">Select which evidence types to include in the report.</p>
            <div className="bg-surface border border-border/50 rounded-md p-3 mb-3">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-foreground">Evidence Summary</span>
                <Badge variant="outline" className="text-[10px]">{evidenceItems.length} items</Badge>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="p-2 rounded bg-success/10">
                  <p className="text-sm font-bold text-success">{evidenceItems.filter((e) => e.validationStatus === 'validated').length}</p>
                  <p className="text-[10px] text-muted-foreground">Validated</p>
                </div>
                <div className="p-2 rounded bg-warning/10">
                  <p className="text-sm font-bold text-warning">{evidenceItems.filter((e) => e.validationStatus === 'pending').length}</p>
                  <p className="text-[10px] text-muted-foreground">Pending</p>
                </div>
                <div className="p-2 rounded bg-danger/10">
                  <p className="text-sm font-bold text-danger">{evidenceItems.filter((e) => e.validationStatus === 'expired' || e.validationStatus === 'rejected').length}</p>
                  <p className="text-[10px] text-muted-foreground">Issues</p>
                </div>
              </div>
            </div>
            <div className="space-y-2">
              {EVIDENCE_TYPES.map((type) => (
                <div
                  key={type}
                  className="flex items-center gap-3 p-2 rounded-md hover:bg-surface/50 transition-colors cursor-pointer"
                  onClick={() => toggleEvidenceType(type)}
                >
                  <Checkbox checked={selectedEvidenceTypes.has(type)} onCheckedChange={() => toggleEvidenceType(type)} />
                  <span className="text-xs text-foreground">{type}</span>
                </div>
              ))}
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Risk Summary</h3>
            <p className="text-xs text-muted-foreground">Preview of risk findings that will be included in the report.</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-3">
              <div className="p-2 rounded bg-danger/10 text-center">
                <p className="text-lg font-bold text-danger">{risks.filter((r) => r.severity === 'critical').length}</p>
                <p className="text-[10px] text-muted-foreground">Critical</p>
              </div>
              <div className="p-2 rounded bg-warning/10 text-center">
                <p className="text-lg font-bold text-warning">{risks.filter((r) => r.severity === 'high').length}</p>
                <p className="text-[10px] text-muted-foreground">High</p>
              </div>
              <div className="p-2 rounded bg-cyber/10 text-center">
                <p className="text-lg font-bold text-cyber">{risks.filter((r) => r.severity === 'medium').length}</p>
                <p className="text-[10px] text-muted-foreground">Medium</p>
              </div>
              <div className="p-2 rounded bg-success/10 text-center">
                <p className="text-lg font-bold text-success">{risks.filter((r) => r.severity === 'low' || r.severity === 'negligible').length}</p>
                <p className="text-[10px] text-muted-foreground">Low</p>
              </div>
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
              {risks.slice(0, 6).map((risk) => (
                <div
                  key={risk.id}
                  className="flex items-center justify-between p-2.5 rounded-md bg-surface border border-border/50"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-xs font-medium text-foreground truncate">{risk.title}</p>
                    <p className="text-[11px] text-muted-foreground">{risk.framework} · {risk.status}</p>
                  </div>
                  <Badge
                    variant="outline"
                    className={`text-[10px] ml-2 ${
                      risk.severity === 'critical'
                        ? 'text-danger border-danger/30'
                        : risk.severity === 'high'
                        ? 'text-warning border-warning/30'
                        : risk.severity === 'medium'
                        ? 'text-cyber border-cyber/30'
                        : 'text-success border-success/30'
                    }`}
                  >
                    {risk.severity}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        );

      case 6:
        return (
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-foreground">Report Preview</h3>
            <p className="text-xs text-muted-foreground">Review your selections before generating the report.</p>
            <div className="bg-surface border border-border/50 rounded-md p-4 space-y-3">
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-muted-foreground">Framework</span>
                  <p className="font-medium text-foreground">{selectedFramework}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Business Unit</span>
                  <p className="font-medium text-foreground">{selectedBusinessUnit}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Date Range</span>
                  <p className="font-medium text-foreground">{dateStart} — {dateEnd}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Controls Selected</span>
                  <p className="font-medium text-foreground">{selectedControls.size} of {first5Controls.length}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Evidence Types</span>
                  <p className="font-medium text-foreground">{selectedEvidenceTypes.size} of {EVIDENCE_TYPES.length}</p>
                </div>
                <div>
                  <span className="text-muted-foreground">Risks Included</span>
                  <p className="font-medium text-foreground">{risks.length} findings</p>
                </div>
              </div>
              <Separator />
              <div>
                <span className="text-xs text-muted-foreground">Selected Controls</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {first5Controls
                    .filter((c) => selectedControls.has(c.id))
                    .map((c) => (
                      <Badge key={c.id} variant="outline" className="text-[10px]">
                        {c.controlRef}
                      </Badge>
                    ))}
                </div>
              </div>
              <div>
                <span className="text-xs text-muted-foreground">Evidence Types</span>
                <div className="flex flex-wrap gap-1.5 mt-1.5">
                  {Array.from(selectedEvidenceTypes).map((type) => (
                    <Badge key={type} variant="outline" className="text-[10px]">
                      {type}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        );

      case 7:
        return (
          <div className="space-y-4 text-center py-6">
            {generated ? (
              <>
                <div className="mx-auto w-16 h-16 rounded-full bg-success/20 flex items-center justify-center">
                  <Check className="h-8 w-8 text-success" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">Report Generated Successfully!</h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  Your {selectedFramework} compliance report for {selectedBusinessUnit} has been generated and is ready for review.
                </p>
                <div className="flex justify-center gap-3 mt-4 flex-wrap">
                  <Button variant="outline" size="sm" onClick={handleReset}>
                    Generate Another
                  </Button>
                  <Button size="sm" onClick={onComplete}>
                    <LayoutGrid className="h-3.5 w-3.5 mr-1.5" />
                    View Reports
                  </Button>
                  <Button variant="outline" size="sm">
                    <Download className="h-3.5 w-3.5 mr-1.5" />
                    Download PDF
                  </Button>
                </div>
              </>
            ) : (
              <>
                <div className="mx-auto w-16 h-16 rounded-full bg-primary/20 flex items-center justify-center">
                  <Zap className="h-8 w-8 text-primary" />
                </div>
                <h3 className="text-sm font-semibold text-foreground">Ready to Generate</h3>
                <p className="text-xs text-muted-foreground max-w-md mx-auto">
                  Your {selectedFramework} compliance report for {selectedBusinessUnit} is configured and ready to be generated.
                  This action will create a new report entry.
                </p>
                {canGenerate ? (
                  <Button size="sm" className="mt-4" onClick={handleGenerate}>
                    <Zap className="h-3.5 w-3.5 mr-1.5" />
                    Generate Report
                  </Button>
                ) : (
                  <div className="mt-4 flex flex-col items-center gap-2">
                    <Button size="sm" disabled className="opacity-50 cursor-not-allowed">
                      <Lock className="h-3.5 w-3.5 mr-1.5" />
                      Generate Report
                    </Button>
                    <p className="text-[10px] text-muted-foreground italic">
                      Your role does not have permission to generate reports
                    </p>
                  </div>
                )}
              </>
            )}
          </div>
        );

      default:
        return null;
    }
  }

  return (
    <div className="space-y-6">
      {/* Step Indicator */}
      <div className="bg-card border border-border rounded-lg p-4 overflow-x-auto">
        <div className="flex items-center gap-1 min-w-max">
          {WIZARD_STEPS.map((step, i) => (
            <React.Fragment key={step.label}>
              <button
                onClick={() => setCurrentStep(i)}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-md transition-all text-xs ${
                  i === currentStep
                    ? 'bg-primary/15 text-primary font-semibold'
                    : i < currentStep
                    ? 'text-success'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[11px] font-bold border-2 ${
                    i === currentStep
                      ? 'border-primary bg-primary text-primary-foreground'
                      : i < currentStep
                      ? 'border-success bg-success/20 text-success'
                      : 'border-muted-foreground/30 text-muted-foreground'
                  }`}
                >
                  {i < currentStep ? <Check className="h-3 w-3" /> : i + 1}
                </div>
                <span className="hidden sm:inline">{step.label}</span>
              </button>
              {i < WIZARD_STEPS.length - 1 && (
                <div className={`w-4 h-px ${i < currentStep ? 'bg-success' : 'bg-muted-foreground/20'}`} />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-card border border-border rounded-lg p-6">
        {renderStepContent()}
      </div>

      {/* Navigation */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentStep((prev) => Math.max(0, prev - 1))}
          disabled={currentStep === 0}
        >
          <ChevronLeft className="h-3.5 w-3.5 mr-1" />
          Previous
        </Button>
        <span className="text-xs text-muted-foreground">
          Step {currentStep + 1} of {WIZARD_STEPS.length}
        </span>
        <Button
          size="sm"
          onClick={() => setCurrentStep((prev) => Math.min(WIZARD_STEPS.length - 1, prev + 1))}
          disabled={currentStep === WIZARD_STEPS.length - 1}
        >
          Next
          <ChevronRight className="h-3.5 w-3.5 ml-1" />
        </Button>
      </div>
    </div>
  );
}

// ===================== Tab 3: Templates =====================
function TemplatesTab() {
  const categoryColors: Record<string, string> = {
    Executive: 'bg-primary/15 text-primary border-primary/30',
    Audit: 'bg-cyber/15 text-cyber border-cyber/30',
    Assessment: 'bg-warning/15 text-warning border-warning/30',
    Compliance: 'bg-success/15 text-success border-success/30',
    Risk: 'bg-danger/15 text-danger border-danger/30',
    Evidence: 'bg-muted text-muted-foreground border-muted-foreground/30',
    Analysis: 'bg-cyber/15 text-cyber border-cyber/30',
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-semibold text-foreground">Report Templates</h2>
        <Badge variant="outline" className="text-[11px]">{reportTemplates.length} templates</Badge>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reportTemplates.map((template) => (
          <div
            key={template.id}
            className="bg-card border border-border rounded-lg p-4 hover:border-primary/30 transition-all group"
          >
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <h3 className="text-sm font-semibold text-foreground">{template.name}</h3>
                <FileText className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{template.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {template.framework && (
                  <Badge variant="outline" className="text-[10px] border-primary/30 text-primary">
                    {template.framework}
                  </Badge>
                )}
                <Badge
                  variant="outline"
                  className={`text-[10px] ${categoryColors[template.category] || 'bg-muted text-muted-foreground border-muted-foreground/30'}`}
                >
                  {template.category}
                </Badge>
              </div>
              <Separator />
              <div className="flex items-center justify-between">
                <div className="text-[11px] text-muted-foreground">
                  <span>Last used: {formatDate(template.lastUsed)}</span>
                  <span className="ml-2">· {template.usageCount} uses</span>
                </div>
                <Button variant="outline" size="sm" className="h-7 text-[11px] opacity-0 group-hover:opacity-100 transition-opacity">
                  Use Template
                  <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ===================== Tab 4: Report Detail / Preview =====================
function ReportDetailTab({ selectedReportId, onSelectReport }: { selectedReportId: string; onSelectReport: (id: string) => void }) {
  const reports = useReportsStore((state) => state.reports);
  const report = reports.find((r) => r.id === selectedReportId) ?? reports[0];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left: Report List */}
      <div className="lg:col-span-4 xl:col-span-3">
        <div className="bg-card border border-border rounded-lg p-3">
          <h3 className="text-xs font-semibold text-foreground mb-3">Reports</h3>
          <div className="space-y-1.5 max-h-[560px] overflow-y-auto custom-scrollbar">
            {reports.map((r) => (
              <button
                key={r.id}
                onClick={() => onSelectReport(r.id)}
                className={`w-full text-left p-2.5 rounded-md border transition-all text-xs ${
                  r.id === selectedReportId
                    ? 'border-primary bg-primary/10 text-foreground'
                    : 'border-transparent bg-surface hover:border-primary/30 text-muted-foreground'
                }`}
              >
                <p className={`font-medium truncate ${r.id === selectedReportId ? 'text-foreground' : 'text-foreground/80'}`}>
                  {r.title}
                </p>
                <div className="flex items-center gap-1.5 mt-1">
                  <span className="text-[11px]">{r.framework}</span>
                  <span className="text-border">·</span>
                  <span className={`text-[11px] ${getScoreColor(r.complianceScore)}`}>{r.complianceScore}%</span>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Right: Report Detail */}
      <div className="lg:col-span-8 xl:col-span-9">
        {report && (
          <div className="space-y-4">
            {/* Header */}
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="space-y-1">
                  <h2 className="text-sm font-bold text-foreground">{report.title}</h2>
                  <div className="flex items-center gap-2 text-[11px] text-muted-foreground flex-wrap">
                    <span>{report.author}</span>
                    <span className="text-border">·</span>
                    <span>{report.generatedAt ? formatDate(report.generatedAt) : 'Not generated'}</span>
                    <span className="text-border">·</span>
                    <span>{report.businessUnit}</span>
                    <span className="text-border">·</span>
                    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-semibold ${getReportStatusColor(report.status)}`}>
                      {report.status}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 flex-shrink-0">
                  <Button variant="outline" size="sm" className="h-7 text-[11px]">
                    <Download className="h-3 w-3 mr-1" />
                    PDF
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px]">
                    <FileSpreadsheet className="h-3 w-3 mr-1" />
                    Excel
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px]">
                    <Table className="h-3 w-3 mr-1" />
                    CSV
                  </Button>
                  <Button variant="outline" size="sm" className="h-7 text-[11px]">
                    <Share2 className="h-3 w-3 mr-1" />
                    Share
                  </Button>
                </div>
              </div>
            </div>

            {/* Score Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-[11px] text-muted-foreground mb-1">Compliance</p>
                <p className={`text-xl font-bold ${getScoreColor(report.complianceScore)}`}>{report.complianceScore}%</p>
              </div>
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-[11px] text-muted-foreground mb-1">Resilience</p>
                <p className={`text-xl font-bold ${getScoreColor(report.resilienceScore)}`}>{report.resilienceScore}%</p>
              </div>
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-[11px] text-muted-foreground mb-1">Controls</p>
                <p className="text-xl font-bold text-foreground">{report.controlsCovered}</p>
              </div>
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-[11px] text-muted-foreground mb-1">Evidence</p>
                <p className="text-xl font-bold text-foreground">{report.evidenceLinked}</p>
              </div>
              <div className="bg-card border border-border rounded-lg p-3 text-center">
                <p className="text-[11px] text-muted-foreground mb-1">Risks</p>
                <p className="text-xl font-bold text-danger">{report.risksIdentified}</p>
              </div>
            </div>

            {/* Mock Report Preview */}
            <div className="bg-card border border-border rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-foreground">Report Preview</h3>
                <Badge variant="outline" className="text-[10px]">Mock</Badge>
              </div>
              <div className="bg-surface border border-border/50 rounded-md p-4 space-y-4">
                {/* Mock Title */}
                <div className="text-center space-y-2 pb-4 border-b border-border/30">
                  <h4 className="text-base font-bold text-foreground">{report.title}</h4>
                  <p className="text-xs text-muted-foreground">Prepared by {report.author} · {report.businessUnit}</p>
                  <p className="text-[11px] text-muted-foreground">Period: {report.dateRange.start} — {report.dateRange.end}</p>
                </div>

                {/* Section 1 */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <div className="w-1 h-4 bg-primary rounded-sm" />
                    Executive Summary
                  </h5>
                  <p className="text-[11px] text-muted-foreground leading-relaxed">
                    This report provides a comprehensive assessment of {report.framework} compliance for {report.businessUnit}.
                    The overall compliance score is {report.complianceScore}% with a resilience score of {report.resilienceScore}%.
                    {report.risksIdentified} risks were identified, with {report.controlsCovered} controls covered and {report.evidenceLinked} evidence items linked.
                  </p>
                </div>

                <Separator />

                {/* Section 2 */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <div className="w-1 h-4 bg-success rounded-sm" />
                    Compliance Overview
                  </h5>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-2 rounded bg-success/10 border border-success/20">
                      <p className="text-[10px] text-muted-foreground">Compliant Controls</p>
                      <p className="text-sm font-bold text-success">{Math.round(report.controlsCovered * 0.72)}</p>
                    </div>
                    <div className="p-2 rounded bg-warning/10 border border-warning/20">
                      <p className="text-[10px] text-muted-foreground">Partially Compliant</p>
                      <p className="text-sm font-bold text-warning">{Math.round(report.controlsCovered * 0.18)}</p>
                    </div>
                    <div className="p-2 rounded bg-danger/10 border border-danger/20">
                      <p className="text-[10px] text-muted-foreground">Non-Compliant</p>
                      <p className="text-sm font-bold text-danger">{Math.round(report.controlsCovered * 0.10)}</p>
                    </div>
                    <div className="p-2 rounded bg-muted border border-muted-foreground/20">
                      <p className="text-[10px] text-muted-foreground">Not Assessed</p>
                      <p className="text-sm font-bold text-muted-foreground">{Math.round(report.controlsCovered * 0.05)}</p>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Section 3 */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <div className="w-1 h-4 bg-warning rounded-sm" />
                    Risk Findings
                  </h5>
                  <div className="space-y-1.5">
                    {risks.slice(0, 3).map((risk) => (
                      <div key={risk.id} className="flex items-center justify-between p-2 rounded bg-background/50 border border-border/30">
                        <span className="text-[11px] text-foreground">{risk.title}</span>
                        <Badge
                          variant="outline"
                          className={`text-[10px] ${
                            risk.severity === 'critical'
                              ? 'text-danger border-danger/30'
                              : risk.severity === 'high'
                              ? 'text-warning border-warning/30'
                              : 'text-cyber border-cyber/30'
                          }`}
                        >
                          {risk.severity}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>

                <Separator />

                {/* Section 4 */}
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                    <div className="w-1 h-4 bg-cyber rounded-sm" />
                    Recommendations
                  </h5>
                  <ul className="space-y-1 text-[11px] text-muted-foreground list-disc list-inside">
                    <li>Address {report.risksIdentified} identified risks with priority remediation</li>
                    <li>Improve evidence coverage for controls with missing validation</li>
                    <li>Schedule quarterly compliance reviews to maintain trajectory</li>
                    <li>Implement automated evidence collection for continuous monitoring</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// ===================== Main Component =====================
export function ReportsSection() {
  const reports = useReportsStore((state) => state.reports);
  const addReport = useReportsStore((state) => state.addReport);
  const { toast } = useToast();
  const [selectedReportId, setSelectedReportId] = useState<string>(reports[0]?.id ?? '');
  const [activeTab, setActiveTab] = useState('dashboard');
  const [drawerReport, setDrawerReport] = useState<Report | null>(null);
  const addRecent = useRecentlyViewedStore((s) => s.addRecent);

  function handleSelectReport(id: string) {
    setSelectedReportId(id);
    const report = reports.find((r) => r.id === id) ?? null;
    setDrawerReport(report);
    if (report) {
      addRecent({
        id: report.id,
        type: 'report',
        title: report.title,
        subtitle: report.framework,
        section: 'reports',
      });
    }
  }

  function handleGenerateReport(report: Report) {
    addReport(report);
    setSelectedReportId(report.id);
    toast({
      title: 'Report generated successfully',
      description: `${report.title} (${report.id}) has been added to your reports.`,
    });
  }

  function handleWizardComplete() {
    setActiveTab('dashboard');
  }

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-foreground">Report Generation</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Generate, manage, and customize compliance reports
        </p>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="dashboard">
            <BarChart3 className="h-3.5 w-3.5 mr-1" />
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="builder">
            <Plus className="h-3.5 w-3.5 mr-1" />
            Builder
          </TabsTrigger>
          <TabsTrigger value="templates">
            <LayoutGrid className="h-3.5 w-3.5 mr-1" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="detail">
            <Eye className="h-3.5 w-3.5 mr-1" />
            Detail
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <ReportsDashboard onSelectReport={handleSelectReport} />
        </TabsContent>

        <TabsContent value="builder">
          <ReportBuilderWizard onGenerate={handleGenerateReport} onComplete={handleWizardComplete} />
        </TabsContent>

        <TabsContent value="templates">
          <TemplatesTab />
        </TabsContent>

        <TabsContent value="detail">
          <ReportDetailTab selectedReportId={selectedReportId} onSelectReport={setSelectedReportId} />
        </TabsContent>
      </Tabs>

      <ReportDetailDrawer
        report={drawerReport}
        open={!!drawerReport}
        onOpenChange={(open) => !open && setDrawerReport(null)}
      />
    </div>
  );
}
