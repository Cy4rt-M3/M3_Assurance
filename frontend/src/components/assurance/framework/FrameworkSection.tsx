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
import {
  Shield,
  Search,
  GitBranch,
  FileCheck,
  Layers,
  ChevronRight,
  X,
  Loader2,
  AlertTriangle,
} from 'lucide-react';
import {
  useRealFrameworks,
  useRealControls,
  type RealControl,
} from '@/lib/assurance/use-real-frameworks';

// ─── Shared framework picker ─────────────────────────────────

function FrameworkPicker({
  value,
  onChange,
  frameworks,
  loading,
}: {
  value: string;
  onChange: (v: string) => void;
  frameworks: { id: string; name: string; version: string | null; controlCount: number }[];
  loading: boolean;
}) {
  return (
    <Select value={value} onValueChange={onChange} disabled={loading}>
      <SelectTrigger className="w-[240px]" size="sm">
        <SelectValue placeholder={loading ? 'Loading…' : 'Select framework'} />
      </SelectTrigger>
      <SelectContent>
        {frameworks.map((fw) => (
          <SelectItem key={fw.id} value={fw.id}>
            {fw.name}
            {fw.version ? ` (v${fw.version})` : ''} — {fw.controlCount} controls
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

// ─── Tab 1: Frameworks overview ──────────────────────────────

function FrameworksOverview({ onViewControls }: { onViewControls: (id: string) => void }) {
  const { frameworks, status } = useRealFrameworks();

  if (status === 'loading') {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground py-10 justify-center">
        <Loader2 className="h-4 w-4 animate-spin" /> Loading frameworks…
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex items-center gap-2 text-sm text-danger py-10 justify-center">
        <AlertTriangle className="h-4 w-4" /> Couldn't load frameworks from the API.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Shield className="h-4 w-4 text-primary" />
        <h2 className="text-sm font-semibold text-foreground">Frameworks</h2>
        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
          {frameworks.length} frameworks
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {frameworks.map((fw) => (
          <div
            key={fw.id}
            className="bg-card border border-border rounded-lg p-5 hover:border-primary/30 transition-all duration-200"
          >
            <div className="flex items-center gap-2 mb-3">
              <div className="p-1.5 rounded-md bg-primary/10 shrink-0">
                <Shield className="h-4 w-4 text-primary" />
              </div>
              <div className="min-w-0">
                <h3 className="text-sm font-semibold text-foreground truncate">{fw.name}</h3>
                {fw.version && (
                  <span className="text-[11px] text-muted-foreground">v{fw.version}</span>
                )}
              </div>
            </div>

            <div className="flex items-center justify-between pt-3 border-t border-border/50">
              <span className="text-xs text-muted-foreground">
                <span className="font-semibold text-foreground">{fw.controlCount}</span> controls
              </span>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs"
                onClick={() => onViewControls(fw.id)}
              >
                View controls
              </Button>
            </div>
          </div>
        ))}
      </div>

      {frameworks.length === 0 && (
        <div className="text-sm text-muted-foreground border border-dashed border-border rounded-lg py-8 text-center">
          No frameworks found. Check that the local database has been migrated.
        </div>
      )}
    </div>
  );
}

// ─── Control detail panel (real fields only) ─────────────────

function ControlDetailPanel({
  control,
  onClose,
}: {
  control: RealControl;
  onClose: () => void;
}) {
  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-start justify-between">
        <div>
          <span className="text-xs font-mono text-primary">{control.controlId}</span>
          <h3 className="text-sm font-semibold text-foreground">{control.controlName}</h3>
        </div>
        <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={onClose}>
          <X className="h-4 w-4" />
        </Button>
      </div>

      {control.description && (
        <p className="text-xs text-muted-foreground">{control.description}</p>
      )}

      <div className="grid grid-cols-2 gap-3 text-xs">
        <Field label="Function / Domain" value={control.functionDomain} />
        <Field label="Category" value={control.category} />
        <Field label="Control Type" value={control.controlType} />
        <Field label="Status" value={control.status} />
        <Field label="Priority" value={control.priority} />
        <Field label="Parent Control" value={control.parentControlId} />
        <Field
          label="Evidence Required"
          value={
            control.evidenceRequired === null
              ? null
              : control.evidenceRequired
              ? 'Yes'
              : 'No'
          }
        />
        <Field label="Owner" value={control.owner} />
      </div>

      {control.controlObjective && (
        <div>
          <p className="text-[11px] uppercase tracking-wide text-muted-foreground mb-1">
            Objective
          </p>
          <p className="text-xs text-foreground">{control.controlObjective}</p>
        </div>
      )}

      {control.evidenceType.length > 0 && (
        <TagList label="Evidence Type" items={control.evidenceType} />
      )}
      {control.evidenceSource.length > 0 && (
        <TagList label="Evidence Source" items={control.evidenceSource} />
      )}
      {control.equivalentControls.length > 0 && (
        <TagList label="Equivalent Controls" items={control.equivalentControls} />
      )}
      {control.keywords.length > 0 && <TagList label="Keywords" items={control.keywords} />}
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{label}</p>
      <p className="text-foreground">{value ?? '—'}</p>
    </div>
  );
}

function TagList({ label, items }: { label: string; items: string[] }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground mb-1">{label}</p>
      <div className="flex flex-wrap gap-1">
        {items.map((item, i) => (
          <Badge key={i} variant="outline" className="text-[10px] px-1.5 py-0">
            {item}
          </Badge>
        ))}
      </div>
    </div>
  );
}

// ─── Tab 2: Controls (framework selection + list) ────────────

function ControlsExplorer({
  selectedFramework,
  setSelectedFramework,
}: {
  selectedFramework: string;
  setSelectedFramework: (v: string) => void;
}) {
  const { frameworks, status: fwStatus } = useRealFrameworks();
  const { controls, total, status } = useRealControls(selectedFramework || null);
  const [selectedControl, setSelectedControl] = useState<RealControl | null>(null);

  const groupedByDomain = useMemo(() => {
    const groups: Record<string, RealControl[]> = {};
    controls.forEach((c) => {
      const key = c.functionDomain || 'Uncategorized';
      if (!groups[key]) groups[key] = [];
      groups[key].push(c);
    });
    return groups;
  }, [controls]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Framework:</span>
        </div>
        <FrameworkPicker
          value={selectedFramework}
          onChange={(v) => {
            setSelectedFramework(v);
            setSelectedControl(null);
          }}
          frameworks={frameworks}
          loading={fwStatus === 'loading'}
        />
        {status === 'ready' && (
          <span className="text-xs text-muted-foreground">{total} controls</span>
        )}
      </div>

      {!selectedFramework && (
        <div className="text-sm text-muted-foreground border border-dashed border-border rounded-lg py-8 text-center">
          Select a framework to see its controls.
        </div>
      )}

      {selectedFramework && status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-8 justify-center">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading controls…
        </div>
      )}

      {selectedFramework && status === 'ready' && controls.length === 0 && (
        <div className="text-sm text-muted-foreground border border-dashed border-border rounded-lg py-8 text-center">
          No controls found for this framework.
        </div>
      )}

      {selectedFramework && status === 'ready' && controls.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className={selectedControl ? 'lg:col-span-2' : 'lg:col-span-3'}>
            <div className="bg-card border border-border rounded-lg overflow-hidden">
              <Accordion
                type="multiple"
                defaultValue={Object.keys(groupedByDomain)}
                className="w-full"
              >
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
                            <TableHead className="text-[11px] text-muted-foreground h-8 px-4">
                              Ref
                            </TableHead>
                            <TableHead className="text-[11px] text-muted-foreground h-8">
                              Title
                            </TableHead>
                            <TableHead className="text-[11px] text-muted-foreground h-8">
                              Category
                            </TableHead>
                            <TableHead className="text-[11px] text-muted-foreground h-8">
                              Priority
                            </TableHead>
                            <TableHead className="text-[11px] text-muted-foreground h-8">
                              Status
                            </TableHead>
                          </TableRow>
                        </TableHeader>
                        <TableBody>
                          {domainControls.map((ctrl) => (
                            <TableRow
                              key={ctrl.controlId}
                              className="cursor-pointer hover:bg-primary/5 transition-colors"
                              onClick={() => setSelectedControl(ctrl)}
                            >
                              <TableCell className="text-xs font-mono text-primary px-4">
                                {ctrl.controlId}
                              </TableCell>
                              <TableCell className="text-xs text-foreground max-w-[220px]">
                                <span className="truncate block">{ctrl.controlName}</span>
                              </TableCell>
                              <TableCell className="text-xs text-muted-foreground max-w-[160px]">
                                <span className="truncate block">{ctrl.category ?? '—'}</span>
                              </TableCell>
                              <TableCell className="text-xs text-muted-foreground">
                                {ctrl.priority ?? '—'}
                              </TableCell>
                              <TableCell>
                                <Badge variant="outline" className="text-[10px] px-1.5 py-0">
                                  {ctrl.status ?? 'Unknown'}
                                </Badge>
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

          {selectedControl && (
            <div className="lg:col-span-1">
              <ControlDetailPanel
                control={selectedControl}
                onClose={() => setSelectedControl(null)}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Tab 3: Control Mapping (equivalent controls) ────────────

function ControlMapping({
  selectedFramework,
  setSelectedFramework,
}: {
  selectedFramework: string;
  setSelectedFramework: (v: string) => void;
}) {
  const { frameworks, status: fwStatus } = useRealFrameworks();
  const { controls, status } = useRealControls(selectedFramework || null);

  const mapped = useMemo(
    () => controls.filter((c) => c.equivalentControls.length > 0),
    [controls]
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Framework:</span>
        </div>
        <FrameworkPicker
          value={selectedFramework}
          onChange={setSelectedFramework}
          frameworks={frameworks}
          loading={fwStatus === 'loading'}
        />
        {status === 'ready' && (
          <span className="text-xs text-muted-foreground">
            {mapped.length} controls with mappings
          </span>
        )}
      </div>

      {!selectedFramework && (
        <div className="text-sm text-muted-foreground border border-dashed border-border rounded-lg py-8 text-center">
          Select a framework to see its control mappings.
        </div>
      )}

      {selectedFramework && status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-8 justify-center">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading mappings…
        </div>
      )}

      {selectedFramework && status === 'ready' && mapped.length === 0 && (
        <div className="bg-card border border-border rounded-lg p-8 text-center">
          <GitBranch className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
          <p className="text-sm text-muted-foreground">
            No cross-framework mappings recorded for this framework yet.
          </p>
        </div>
      )}

      {selectedFramework && status === 'ready' && mapped.length > 0 && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <ScrollArea className="w-full">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="text-[11px] text-muted-foreground h-9 px-4 min-w-[120px]">
                    Control
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[200px]">
                    Title
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[300px]">
                    Equivalent Controls
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mapped.map((ctrl) => (
                  <TableRow key={ctrl.controlId} className="hover:bg-surface/50">
                    <TableCell className="text-xs font-mono text-primary px-4 align-top">
                      {ctrl.controlId}
                    </TableCell>
                    <TableCell className="text-xs text-foreground align-top max-w-[220px]">
                      <span className="line-clamp-2">{ctrl.controlName}</span>
                    </TableCell>
                    <TableCell className="align-top">
                      <div className="flex flex-wrap gap-1">
                        {ctrl.equivalentControls.map((eq, i) => (
                          <Badge
                            key={i}
                            variant="outline"
                            className="text-[10px] px-1.5 py-0 bg-primary/5 text-primary border-primary/20"
                          >
                            {eq}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

// ─── Tab 4: Evidence fields (as recorded, no counts) ─────────

function EvidenceFields({
  selectedFramework,
  setSelectedFramework,
}: {
  selectedFramework: string;
  setSelectedFramework: (v: string) => void;
}) {
  const { frameworks, status: fwStatus } = useRealFrameworks();
  const { controls, status } = useRealControls(selectedFramework || null);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-2">
          <FileCheck className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm text-muted-foreground">Framework:</span>
        </div>
        <FrameworkPicker
          value={selectedFramework}
          onChange={setSelectedFramework}
          frameworks={frameworks}
          loading={fwStatus === 'loading'}
        />
      </div>

      {!selectedFramework && (
        <div className="text-sm text-muted-foreground border border-dashed border-border rounded-lg py-8 text-center">
          Select a framework to see evidence fields.
        </div>
      )}

      {selectedFramework && status === 'loading' && (
        <div className="flex items-center gap-2 text-sm text-muted-foreground py-8 justify-center">
          <Loader2 className="h-4 w-4 animate-spin" /> Loading…
        </div>
      )}

      {selectedFramework && status === 'ready' && (
        <div className="bg-card border border-border rounded-lg overflow-hidden">
          <ScrollArea className="w-full">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="text-[11px] text-muted-foreground h-9 px-4 min-w-[100px]">
                    Ref
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[180px]">
                    Title
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 w-[110px]">
                    Evidence Req.
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[200px]">
                    Evidence Type
                  </TableHead>
                  <TableHead className="text-[11px] text-muted-foreground h-9 min-w-[200px]">
                    Evidence Source
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {controls.map((ctrl) => (
                  <TableRow key={ctrl.controlId} className="hover:bg-surface/50">
                    <TableCell className="text-xs font-mono text-primary px-4">
                      {ctrl.controlId}
                    </TableCell>
                    <TableCell className="text-xs text-foreground max-w-[180px]">
                      <span className="truncate block">{ctrl.controlName}</span>
                    </TableCell>
                    <TableCell>
                      {ctrl.evidenceRequired === null ? (
                        <span className="text-xs text-muted-foreground">—</span>
                      ) : (
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1.5 py-0 ${
                            ctrl.evidenceRequired
                              ? 'bg-warning/10 text-warning border-warning/30'
                              : 'bg-muted text-muted-foreground'
                          }`}
                        >
                          {ctrl.evidenceRequired ? 'Required' : 'Not required'}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {ctrl.evidenceType.length > 0 ? ctrl.evidenceType.join(', ') : '—'}
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {ctrl.evidenceSource.length > 0 ? ctrl.evidenceSource.join(', ') : '—'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </ScrollArea>
        </div>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────

export function FrameworkSection() {
  const [tab, setTab] = useState('dashboard');
  const [selectedFramework, setSelectedFramework] = useState('');

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-xl font-bold text-foreground">Framework & Regulatory Playbook</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Live data from the Framework Registry — frameworks, controls, and cross-framework
          mappings.
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab} className="w-full">
        <TabsList className="bg-muted/50">
          <TabsTrigger value="dashboard" className="gap-1.5 text-xs">
            <Shield className="h-3.5 w-3.5" />
            Frameworks
          </TabsTrigger>
          <TabsTrigger value="controls" className="gap-1.5 text-xs">
            <Search className="h-3.5 w-3.5" />
            Controls
          </TabsTrigger>
          <TabsTrigger value="mapping" className="gap-1.5 text-xs">
            <GitBranch className="h-3.5 w-3.5" />
            Control Mapping
          </TabsTrigger>
          <TabsTrigger value="evidence" className="gap-1.5 text-xs">
            <FileCheck className="h-3.5 w-3.5" />
            Evidence
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <FrameworksOverview
            onViewControls={(id) => {
              setSelectedFramework(id);
              setTab('controls');
            }}
          />
        </TabsContent>

        <TabsContent value="controls">
          <ControlsExplorer
            selectedFramework={selectedFramework}
            setSelectedFramework={setSelectedFramework}
          />
        </TabsContent>

        <TabsContent value="mapping">
          <ControlMapping
            selectedFramework={selectedFramework}
            setSelectedFramework={setSelectedFramework}
          />
        </TabsContent>

        <TabsContent value="evidence">
          <EvidenceFields
            selectedFramework={selectedFramework}
            setSelectedFramework={setSelectedFramework}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}