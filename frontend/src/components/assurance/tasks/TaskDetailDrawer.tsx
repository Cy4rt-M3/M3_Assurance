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
import { Separator } from '@/components/ui/separator';
import {
  CheckSquare, Clock, Eye, CheckCircle2, AlertCircle, Wrench,
  FileCheck, FileText, ShieldCheck, Calendar, User, Building2,
  Target, AlertTriangle, ArrowRight, Tag, TrendingUp,
} from 'lucide-react';
import type { GrcTask, TaskStatus, TaskType } from '@/lib/assurance/types';
import { formatDate, formatDateTime } from '@/lib/assurance/utils';

interface TaskDetailDrawerProps {
  task: GrcTask | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const statusConfig: Record<TaskStatus, { label: string; color: string; bg: string; icon: React.ComponentType<{ className?: string }> }> = {
  todo: { label: 'To Do', color: 'text-muted-foreground', bg: 'bg-muted/50 border-muted-foreground/20', icon: CheckSquare },
  in_progress: { label: 'In Progress', color: 'text-cyber', bg: 'bg-cyber/10 border-cyber/20', icon: Clock },
  review: { label: 'In Review', color: 'text-warning', bg: 'bg-warning/10 border-warning/20', icon: Eye },
  done: { label: 'Done', color: 'text-success', bg: 'bg-success/10 border-success/20', icon: CheckCircle2 },
  blocked: { label: 'Blocked', color: 'text-danger', bg: 'bg-danger/10 border-danger/20', icon: AlertCircle },
};

const typeConfig: Record<TaskType, { label: string; icon: React.ComponentType<{ className?: string }>; color: string; bg: string }> = {
  evidence_collection: { label: 'Evidence Collection', icon: FileCheck, color: 'text-success', bg: 'bg-success/15' },
  control_testing: { label: 'Control Testing', icon: ShieldCheck, color: 'text-cyber', bg: 'bg-cyber/15' },
  remediation: { label: 'Remediation', icon: Wrench, color: 'text-warning', bg: 'bg-warning/15' },
  review: { label: 'Review', icon: Eye, color: 'text-primary', bg: 'bg-primary/15' },
  approval: { label: 'Approval', icon: FileText, color: 'text-purple-400', bg: 'bg-purple-500/15' },
  audit_prep: { label: 'Audit Preparation', icon: CheckSquare, color: 'text-cyan-400', bg: 'bg-cyan-500/15' },
};

function getPriorityBg(priority: string): string {
  switch (priority) {
    case 'critical': return 'bg-danger/15 text-danger border-danger/30';
    case 'high': return 'bg-warning/15 text-warning border-warning/30';
    case 'medium': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'low': return 'bg-success/15 text-success border-success/30';
    default: return 'bg-muted text-muted-foreground border-muted-foreground/30';
  }
}

function isOverdue(dueDate: string, status: TaskStatus): boolean {
  return status !== 'done' && new Date(dueDate) < new Date('2025-01-15');
}

export function TaskDetailDrawer({ task, open, onOpenChange }: TaskDetailDrawerProps) {
  if (!task) return null;

  const statusInfo = statusConfig[task.status];
  const typeInfo = typeConfig[task.type];
  const overdue = isOverdue(task.dueDate, task.status);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full sm:max-w-xl p-0 bg-card border-l border-border overflow-y-auto">
        {/* Sticky Header */}
        <div className="sticky top-0 z-10 bg-card/95 backdrop-blur border-b border-border p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className={`p-2 rounded-lg ${typeInfo.bg}`}>
                <typeInfo.icon className={`h-4 w-4 ${typeInfo.color}`} />
              </div>
              <div>
                <SheetHeader className="p-0">
                  <SheetTitle className="text-sm font-mono text-foreground">{task.id}</SheetTitle>
                  <SheetDescription className="sr-only">Task detail with description, progress, and assignee information</SheetDescription>
                </SheetHeader>
                <p className="text-[11px] text-muted-foreground mt-0.5">{typeInfo.label}</p>
              </div>
            </div>
            <div className="flex items-center gap-1.5">
              <Badge variant="outline" className={`text-[10px] capitalize ${statusInfo.bg}`}>
                <statusInfo.icon className="h-2.5 w-2.5 mr-1" />
                {statusInfo.label}
              </Badge>
            </div>
          </div>
        </div>

        <div className="p-4 space-y-5">
          {/* Title & Description */}
          <div className="space-y-2">
            <h3 className="text-base font-semibold text-foreground leading-tight">{task.title}</h3>
            <p className="text-xs text-muted-foreground leading-relaxed">{task.description}</p>
          </div>

          {/* Progress Card */}
          {task.status !== 'done' && (
            <div className={`rounded-lg p-4 border ${
              task.progress >= 80 ? 'bg-success/5 border-success/20' :
              task.progress >= 50 ? 'bg-cyber/5 border-cyber/20' :
              task.progress > 0 ? 'bg-warning/5 border-warning/20' :
              'bg-surface border-border/50'
            }`}>
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-medium text-foreground flex items-center gap-1.5">
                  <TrendingUp className="h-3.5 w-3.5 text-primary" />
                  Task Progress
                </span>
                <span className={`text-lg font-bold ${
                  task.progress >= 80 ? 'text-success' :
                  task.progress >= 50 ? 'text-cyber' :
                  task.progress > 0 ? 'text-warning' : 'text-muted-foreground'
                }`}>{task.progress}%</span>
              </div>
              <div className="h-2.5 bg-muted/60 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${
                    task.progress >= 80 ? 'bg-success' :
                    task.progress >= 50 ? 'bg-cyber' :
                    task.progress > 0 ? 'bg-warning' : 'bg-muted-foreground'
                  }`}
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          )}

          {/* Priority & Overdue Alert */}
          {overdue && (
            <div className="flex items-center gap-2 p-3 rounded-lg bg-danger/10 border border-danger/20">
              <AlertCircle className="h-4 w-4 text-danger shrink-0" />
              <div>
                <p className="text-xs font-medium text-danger">Task Overdue</p>
                <p className="text-[10px] text-muted-foreground">This task was due on {formatDate(task.dueDate)}</p>
              </div>
            </div>
          )}

          {/* Metadata Grid */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Task Details</h3>
            <div className="grid grid-cols-2 gap-2">
              <DetailItem icon={Target} label="Priority" value={task.priority.charAt(0).toUpperCase() + task.priority.slice(1)} valueClass={getPriorityBg(task.priority).split(' ').find(c => c.startsWith('text-')) || 'text-foreground'} />
              <DetailItem icon={typeInfo.icon} label="Type" value={typeInfo.label} />
              <DetailItem icon={Building2} label="Framework" value={task.framework} />
              {task.controlRef && (
                <DetailItem icon={FileText} label="Control" value={task.controlRef} mono />
              )}
              <DetailItem icon={User} label="Assignee" value={task.assignee} />
              <DetailItem icon={Calendar} label="Due Date" value={formatDate(task.dueDate)} valueClass={overdue ? 'text-danger' : 'text-foreground'} />
              <DetailItem icon={Clock} label="Created" value={formatDateTime(task.createdAt)} />
              <DetailItem icon={CheckCircle2} label="Status" value={statusInfo.label} />
            </div>
          </div>

          {/* Assignee Card */}
          <div className="bg-surface rounded-lg p-3 border border-border/50 flex items-center gap-3">
            <div className="h-10 w-10 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
              <span className="text-sm font-semibold text-primary">{task.assigneeInitials}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground">{task.assignee}</p>
              <p className="text-[10px] text-muted-foreground">Assigned owner</p>
            </div>
            <Button variant="outline" size="sm" className="text-xs h-7">
              Reassign
            </Button>
          </div>

          {/* Tags */}
          {task.tags.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1.5">
                <Tag className="h-3 w-3" />
                Tags
              </h3>
              <div className="flex flex-wrap gap-1.5">
                {task.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="text-[10px] bg-surface border-border">
                    {tag}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Task Timeline / Checklist */}
          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Task Checklist</h3>
            <div className="bg-surface rounded-lg p-3 border border-border/50 space-y-2">
              {[
                { label: 'Task created and assigned', done: true },
                { label: 'Initial assessment completed', done: task.progress >= 25 },
                { label: 'Evidence collection in progress', done: task.progress >= 50 },
                { label: 'Review and validation', done: task.progress >= 75 },
                { label: 'Task completed', done: task.progress >= 100 },
              ].map((step, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <div className={`h-4 w-4 rounded-full flex items-center justify-center shrink-0 ${
                    step.done ? 'bg-success' : 'bg-muted border border-border'
                  }`}>
                    {step.done && <CheckCircle2 className="h-3 w-3 text-white" />}
                  </div>
                  <span className={`text-xs ${step.done ? 'text-foreground' : 'text-muted-foreground'}`}>
                    {step.label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Sticky Footer */}
        <div className="sticky bottom-0 bg-card/95 backdrop-blur border-t border-border p-4 flex gap-2">
          {task.status !== 'done' && (
            <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
              <ArrowRight className="h-3.5 w-3.5" />
              Advance Status
            </Button>
          )}
          <Button variant="outline" size="sm" className="flex-1 text-xs gap-1.5">
            <User className="h-3.5 w-3.5" />
            Reassign
          </Button>
          {task.status !== 'done' && (
            <Button variant="default" size="sm" className="flex-1 text-xs gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" />
              Complete
            </Button>
          )}
        </div>
      </SheetContent>
    </Sheet>
  );
}

function DetailItem({ icon: Icon, label, value, mono, valueClass }: {
  icon: React.ComponentType<{ className?: string }>,
  label: string,
  value: string,
  mono?: boolean,
  valueClass?: string,
}) {
  return (
    <div className="bg-surface rounded-lg p-2.5 border border-border/50">
      <div className="flex items-center gap-1.5 mb-1">
        <Icon className="h-3 w-3 text-muted-foreground" />
        <span className="text-[10px] text-muted-foreground uppercase tracking-wide">{label}</span>
      </div>
      <p className={`text-xs font-medium ${valueClass || 'text-foreground'} truncate ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}
