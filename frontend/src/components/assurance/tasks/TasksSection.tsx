'use client';

import React, { useState, useMemo } from 'react';
import { tasks as initialTasks } from '@/lib/assurance/mock-data';
import type { GrcTask, TaskStatus, TaskPriority, TaskType } from '@/lib/assurance/types';
import { getRiskLevelBg, getRiskLevelLabel, formatDate } from '@/lib/assurance/utils';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { TaskDetailDrawer } from './TaskDetailDrawer';
import { useRecentlyViewedStore } from '@/hooks/use-recently-viewed';
import {
  CheckSquare, ClipboardList, Clock, AlertCircle, Plus, Search,
  FileText, ShieldCheck, Wrench, Eye, CheckCircle2, FileCheck,
  Calendar, User, Filter, LayoutGrid, List, ArrowRight,
} from 'lucide-react';

const statusConfig: Record<TaskStatus, { label: string; color: string; bg: string; icon: React.ComponentType<{ className?: string }> }> = {
  todo: { label: 'To Do', color: 'text-muted-foreground', bg: 'bg-muted/50 border-muted-foreground/20', icon: ClipboardList },
  in_progress: { label: 'In Progress', color: 'text-cyber', bg: 'bg-cyber/10 border-cyber/20', icon: Clock },
  review: { label: 'In Review', color: 'text-warning', bg: 'bg-warning/10 border-warning/20', icon: Eye },
  done: { label: 'Done', color: 'text-success', bg: 'bg-success/10 border-success/20', icon: CheckCircle2 },
  blocked: { label: 'Blocked', color: 'text-danger', bg: 'bg-danger/10 border-danger/20', icon: AlertCircle },
};

const typeConfig: Record<TaskType, { label: string; icon: React.ComponentType<{ className?: string }>; color: string }> = {
  evidence_collection: { label: 'Evidence', icon: FileCheck, color: 'text-success' },
  control_testing: { label: 'Testing', icon: ShieldCheck, color: 'text-cyber' },
  remediation: { label: 'Remediation', icon: Wrench, color: 'text-warning' },
  review: { label: 'Review', icon: Eye, color: 'text-primary' },
  approval: { label: 'Approval', icon: FileText, color: 'text-purple-400' },
  audit_prep: { label: 'Audit Prep', icon: CheckSquare, color: 'text-cyan-400' },
};

function getPriorityBg(priority: TaskPriority): string {
  switch (priority) {
    case 'critical': return 'bg-danger/15 text-danger border-danger/30';
    case 'high': return 'bg-warning/15 text-warning border-warning/30';
    case 'medium': return 'bg-cyber/15 text-cyber border-cyber/30';
    case 'low': return 'bg-success/15 text-success border-success/30';
  }
}

function isOverdue(dueDate: string): boolean {
  return new Date(dueDate) < new Date('2025-01-15');
}

export function TasksSection() {
  const [tasks] = useState(initialTasks);
  const [view, setView] = useState<'board' | 'list'>('board');
  const [searchQuery, setSearchQuery] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [frameworkFilter, setFrameworkFilter] = useState('all');
  const [selectedTask, setSelectedTask] = useState<GrcTask | null>(null);
  const addRecent = useRecentlyViewedStore((s) => s.addRecent);

  const handleSelectTask = (task: GrcTask) => {
    setSelectedTask(task);
    addRecent({
      id: task.id,
      type: 'control' as const,
      title: task.title,
      subtitle: task.id,
      section: 'tasks',
    });
  };

  const filteredTasks = useMemo(() => {
    return tasks.filter((t) => {
      const q = searchQuery.toLowerCase();
      const matchSearch = !q || t.title.toLowerCase().includes(q) || t.id.toLowerCase().includes(q) || t.assignee.toLowerCase().includes(q);
      const matchPriority = priorityFilter === 'all' || t.priority === priorityFilter;
      const matchFramework = frameworkFilter === 'all' || t.framework === frameworkFilter;
      return matchSearch && matchPriority && matchFramework;
    });
  }, [tasks, searchQuery, priorityFilter, frameworkFilter]);

  const stats = useMemo(() => ({
    total: tasks.length,
    todo: tasks.filter((t) => t.status === 'todo').length,
    inProgress: tasks.filter((t) => t.status === 'in_progress').length,
    review: tasks.filter((t) => t.status === 'review').length,
    done: tasks.filter((t) => t.status === 'done').length,
    blocked: tasks.filter((t) => t.status === 'blocked').length,
    overdue: tasks.filter((t) => isOverdue(t.dueDate) && t.status !== 'done').length,
    critical: tasks.filter((t) => t.priority === 'critical' && t.status !== 'done').length,
  }), [tasks]);

  const uniqueFrameworks = useMemo(() => Array.from(new Set(tasks.map((t) => t.framework))), [tasks]);

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-foreground">Task Management</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Assign, track, and manage GRC tasks, remediation actions, and approvals
          </p>
        </div>
        <Button size="sm" className="gap-1.5">
          <Plus className="h-3.5 w-3.5" />
          New Task
        </Button>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <StatCard label="Total" value={stats.total} color="text-foreground" />
        <StatCard label="To Do" value={stats.todo} color="text-muted-foreground" />
        <StatCard label="In Progress" value={stats.inProgress} color="text-cyber" />
        <StatCard label="In Review" value={stats.review} color="text-warning" />
        <StatCard label="Done" value={stats.done} color="text-success" />
        <StatCard label="Overdue" value={stats.overdue} color="text-danger" />
        <StatCard label="Critical" value={stats.critical} color="text-danger" />
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row gap-2 items-center">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Search tasks..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 h-8 text-xs bg-card border-border"
          />
        </div>
        <Select value={priorityFilter} onValueChange={setPriorityFilter}>
          <SelectTrigger className="w-[130px] h-8 text-xs" size="sm">
            <SelectValue placeholder="Priority" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Priorities</SelectItem>
            <SelectItem value="critical">Critical</SelectItem>
            <SelectItem value="high">High</SelectItem>
            <SelectItem value="medium">Medium</SelectItem>
            <SelectItem value="low">Low</SelectItem>
          </SelectContent>
        </Select>
        <Select value={frameworkFilter} onValueChange={setFrameworkFilter}>
          <SelectTrigger className="w-[140px] h-8 text-xs" size="sm">
            <SelectValue placeholder="Framework" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Frameworks</SelectItem>
            {uniqueFrameworks.map((fw) => (
              <SelectItem key={fw} value={fw}>{fw}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex items-center gap-1 ml-auto bg-card border border-border rounded-md p-0.5">
          <Button
            variant={view === 'board' ? 'default' : 'ghost'}
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => setView('board')}
          >
            <LayoutGrid className="h-3.5 w-3.5" />
            Board
          </Button>
          <Button
            variant={view === 'list' ? 'default' : 'ghost'}
            size="sm"
            className="h-7 text-xs gap-1"
            onClick={() => setView('list')}
          >
            <List className="h-3.5 w-3.5" />
            List
          </Button>
        </div>
      </div>

      {/* Task Views */}
      {view === 'board' ? (
        <TaskBoard tasks={filteredTasks} onSelect={handleSelectTask} />
      ) : (
        <TaskList tasks={filteredTasks} onSelect={handleSelectTask} />
      )}

      <TaskDetailDrawer
        task={selectedTask}
        open={!!selectedTask}
        onOpenChange={(open) => !open && setSelectedTask(null)}
      />
    </div>
  );
}

// Stat Card
function StatCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="bg-card border border-border rounded-lg p-3 text-center">
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      <p className="text-[10px] text-muted-foreground uppercase tracking-wide mt-0.5">{label}</p>
    </div>
  );
}

// Kanban Board View
function TaskBoard({ tasks, onSelect }: { tasks: GrcTask[]; onSelect: (task: GrcTask) => void }) {
  const columns: TaskStatus[] = ['todo', 'in_progress', 'review', 'blocked', 'done'];

  return (
    <div className="overflow-x-auto pb-2">
      <div className="grid grid-cols-5 gap-3 min-w-[1000px]">
        {columns.map((status) => {
          const columnTasks = tasks.filter((t) => t.status === status);
          const config = statusConfig[status];
          return (
            <div key={status} className={`rounded-xl border ${config.bg} flex flex-col`}>
              {/* Column Header */}
              <div className="p-3 border-b border-border/30 sticky top-0">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <config.icon className={`h-3.5 w-3.5 ${config.color}`} />
                    <span className="text-xs font-semibold text-foreground">{config.label}</span>
                  </div>
                  <Badge variant="outline" className="text-[10px] bg-card">{columnTasks.length}</Badge>
                </div>
              </div>
              {/* Column Body */}
              <div className="p-2 space-y-2 flex-1 min-h-[200px]">
                {columnTasks.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-[10px] text-muted-foreground">No tasks</p>
                  </div>
                ) : (
                  columnTasks.map((task) => <TaskCard key={task.id} task={task} onSelect={onSelect} />)
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Task Card (for board view)
function TaskCard({ task, onSelect }: { task: GrcTask; onSelect: (task: GrcTask) => void }) {
  const typeInfo = typeConfig[task.type];
  const overdue = isOverdue(task.dueDate);

  return (
    <div
      className="bg-card border border-border rounded-lg p-3 space-y-2 hover:border-primary/30 transition-colors cursor-pointer group"
      onClick={() => onSelect(task)}
    >
      {/* Top row: ID + Priority */}
      <div className="flex items-center justify-between">
        <span className="text-[10px] font-mono text-muted-foreground">{task.id}</span>
        <Badge variant="outline" className={`text-[9px] px-1.5 py-0 ${getPriorityBg(task.priority)}`}>
          {task.priority}
        </Badge>
      </div>

      {/* Title */}
      <p className="text-xs font-medium text-foreground leading-tight line-clamp-2 group-hover:text-primary transition-colors">
        {task.title}
      </p>

      {/* Type + Framework */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <Badge variant="outline" className={`text-[9px] px-1.5 py-0 gap-1 ${typeInfo.color} border-current/20`}>
          <typeInfo.icon className="h-2.5 w-2.5" />
          {typeInfo.label}
        </Badge>
        <span className="text-[10px] text-muted-foreground">{task.framework}</span>
        {task.controlRef && (
          <span className="text-[10px] font-mono text-muted-foreground">{task.controlRef}</span>
        )}
      </div>

      {/* Progress */}
      {task.progress > 0 && task.progress < 100 && (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[9px] text-muted-foreground">
            <span>Progress</span>
            <span>{task.progress}%</span>
          </div>
          <div className="h-1 bg-muted rounded-full overflow-hidden">
            <div
              className={`h-full rounded-full ${task.progress >= 80 ? 'bg-success' : task.progress >= 50 ? 'bg-cyber' : 'bg-warning'}`}
              style={{ width: `${task.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer: Assignee + Due Date */}
      <div className="flex items-center justify-between pt-1 border-t border-border/30">
        <div className="flex items-center gap-1.5">
          <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center">
            <span className="text-[9px] font-semibold text-primary">{task.assigneeInitials}</span>
          </div>
          <span className="text-[10px] text-muted-foreground truncate max-w-[60px]">{task.assignee}</span>
        </div>
        <div className={`flex items-center gap-1 text-[10px] ${overdue ? 'text-danger' : 'text-muted-foreground'}`}>
          <Calendar className="h-2.5 w-2.5" />
          {formatDate(task.dueDate)}
        </div>
      </div>

      {/* Tags */}
      {task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {task.tags.slice(0, 2).map((tag) => (
            <span key={tag} className="text-[9px] px-1.5 py-0.5 rounded bg-muted/50 text-muted-foreground">
              {tag}
            </span>
          ))}
          {task.tags.length > 2 && (
            <span className="text-[9px] text-muted-foreground">+{task.tags.length - 2}</span>
          )}
        </div>
      )}

      {/* Overdue indicator */}
      {overdue && (
        <div className="flex items-center gap-1 text-[9px] text-danger font-medium">
          <AlertCircle className="h-2.5 w-2.5" />
          Overdue
        </div>
      )}
    </div>
  );
}

// List View
function TaskList({ tasks, onSelect }: { tasks: GrcTask[]; onSelect: (task: GrcTask) => void }) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border bg-surface/50">
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Task ID</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Title</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Type</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Priority</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Status</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Framework</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Assignee</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Due Date</th>
              <th className="text-left text-[11px] font-medium text-muted-foreground px-4 py-2.5">Progress</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => {
              const typeInfo = typeConfig[task.type];
              const statusInfo = statusConfig[task.status];
              const overdue = isOverdue(task.dueDate) && task.status !== 'done';
              return (
                <tr key={task.id} className="border-b border-border/50 hover:bg-surface/50 transition-colors cursor-pointer" onClick={() => onSelect(task)}>
                  <td className="px-4 py-2.5">
                    <span className="text-[11px] font-mono text-primary">{task.id}</span>
                  </td>
                  <td className="px-4 py-2.5 max-w-[280px]">
                    <p className="text-xs font-medium text-foreground truncate">{task.title}</p>
                    {task.controlRef && (
                      <p className="text-[10px] text-muted-foreground font-mono">{task.controlRef}</p>
                    )}
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant="outline" className={`text-[10px] gap-1 ${typeInfo.color} border-current/20`}>
                      <typeInfo.icon className="h-2.5 w-2.5" />
                      {typeInfo.label}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant="outline" className={`text-[10px] ${getPriorityBg(task.priority)}`}>
                      {task.priority}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5">
                    <Badge variant="outline" className={`text-[10px] ${statusInfo.bg}`}>
                      {statusInfo.label}
                    </Badge>
                  </td>
                  <td className="px-4 py-2.5 text-xs text-foreground">{task.framework}</td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-1.5">
                      <div className="h-5 w-5 rounded-full bg-primary/20 flex items-center justify-center shrink-0">
                        <span className="text-[9px] font-semibold text-primary">{task.assigneeInitials}</span>
                      </div>
                      <span className="text-[11px] text-muted-foreground truncate max-w-[80px]">{task.assignee}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5">
                    <span className={`text-[11px] ${overdue ? 'text-danger font-medium' : 'text-muted-foreground'}`}>
                      {formatDate(task.dueDate)}
                    </span>
                  </td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="w-12 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${task.progress >= 100 ? 'bg-success' : task.progress >= 50 ? 'bg-cyber' : 'bg-warning'}`}
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-muted-foreground w-8">{task.progress}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={9} className="text-center py-12 text-muted-foreground text-xs">
                  No tasks match your filters
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
