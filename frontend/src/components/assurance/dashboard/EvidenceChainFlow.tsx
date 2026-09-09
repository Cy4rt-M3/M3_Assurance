'use client';

import React, { useState } from 'react';
import { Zap, ScanLine, Database, Target, Shield, FileText, ChevronRight, CheckCircle2, AlertCircle, Clock, ArrowRight } from 'lucide-react';

interface FlowNode {
  id: string;
  label: string;
  sublabel: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  bgColor: string;
  borderColor: string;
  status: 'active' | 'warning' | 'error';
  count?: string;
  x: number;
  y: number;
}

interface FlowConnection {
  from: string;
  to: string;
  status: 'active' | 'pending';
  label?: string;
}

const nodes: FlowNode[] = [
  {
    id: 'strike',
    label: 'Strike Engine',
    sublabel: 'Module 1',
    icon: Zap,
    color: 'text-warning',
    bgColor: 'bg-warning/15',
    borderColor: 'border-warning/30',
    status: 'active',
    count: '248 events',
    x: 60,
    y: 120,
  },
  {
    id: 'validator',
    label: 'Validator',
    sublabel: 'Module 2',
    icon: ScanLine,
    color: 'text-cyber',
    bgColor: 'bg-cyber/15',
    borderColor: 'border-cyber/30',
    status: 'active',
    count: '192 validated',
    x: 260,
    y: 120,
  },
  {
    id: 'evidence',
    label: 'Evidence Store',
    sublabel: 'Validated Evidence',
    icon: Database,
    color: 'text-success',
    bgColor: 'bg-success/15',
    borderColor: 'border-success/30',
    status: 'active',
    count: '8 items',
    x: 460,
    y: 120,
  },
  {
    id: 'control',
    label: 'Control Mapping',
    sublabel: 'Compliance Controls',
    icon: Target,
    color: 'text-primary',
    bgColor: 'bg-primary/15',
    borderColor: 'border-primary/30',
    status: 'active',
    count: '14 controls',
    x: 660,
    y: 120,
  },
  {
    id: 'framework',
    label: 'Framework',
    sublabel: 'Compliance Status',
    icon: Shield,
    color: 'text-purple-400',
    bgColor: 'bg-purple-500/15',
    borderColor: 'border-purple-500/30',
    status: 'warning',
    count: '73% avg',
    x: 860,
    y: 120,
  },
  {
    id: 'report',
    label: 'Audit Report',
    sublabel: 'Executive Output',
    icon: FileText,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/15',
    borderColor: 'border-cyan-500/30',
    status: 'active',
    count: '6 reports',
    x: 1060,
    y: 120,
  },
];

const connections: FlowConnection[] = [
  { from: 'strike', to: 'validator', status: 'active', label: 'security events' },
  { from: 'validator', to: 'evidence', status: 'active', label: 'validated' },
  { from: 'evidence', to: 'control', status: 'active', label: 'mapped' },
  { from: 'control', to: 'framework', status: 'active', label: 'assessed' },
  { from: 'framework', to: 'report', status: 'pending', label: 'generated' },
];

export function EvidenceChainFlow() {
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hoveredConn, setHoveredConn] = useState<string | null>(null);

  const nodeWidth = 140;
  const nodeHeight = 80;

  const getNodeById = (id: string) => nodes.find((n) => n.id === id);

  return (
    <div className="bg-card border border-border rounded-xl p-5 card-hover">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Evidence Chain Flow</h2>
          <p className="text-[11px] text-muted-foreground mt-0.5">
            Interactive traceability diagram — evidence flows from security events to audit reports
          </p>
        </div>
        <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-success cyber-pulse" />
            Active
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-warning" />
            Warning
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-muted-foreground" />
            Pending
          </span>
        </div>
      </div>

      {/* Flow Diagram */}
      <div className="overflow-x-auto pb-2">
        <div className="relative min-w-[1180px] h-[260px]">
          {/* SVG Connections */}
          <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 0 }}>
            {connections.map((conn) => {
              const from = getNodeById(conn.from);
              const to = getNodeById(conn.to);
              if (!from || !to) return null;

              const fromX = from.x + nodeWidth;
              const toX = to.x;
              const midY = from.y + nodeHeight / 2;
              const midX = (fromX + toX) / 2;

              const isActive = conn.status === 'active';
              const isHovered = hoveredConn === `${conn.from}-${conn.to}`;
              const isDimmed = hoveredNode && hoveredNode !== conn.from && hoveredNode !== conn.to;

              return (
                <g key={`${conn.from}-${conn.to}`}>
                  {/* Connection path */}
                  <path
                    d={`M ${fromX} ${midY} L ${midX} ${midY} L ${midX} ${midY} L ${toX} ${midY}`}
                    fill="none"
                    stroke={isActive ? (isHovered ? '#22C55E' : '#22C55E80') : '#F59E0B80'}
                    strokeWidth={isHovered ? 3 : 2}
                    strokeDasharray={isActive ? 'none' : '6 4'}
                    className={`transition-all ${isDimmed ? 'opacity-20' : 'opacity-100'}`}
                  />
                  {/* Animated dot on active connections */}
                  {isActive && (
                    <circle r="3" fill="#22C55E">
                      <animateMotion
                        dur="3s"
                        repeatCount="indefinite"
                        path={`M ${fromX} ${midY} L ${toX} ${midY}`}
                      />
                    </circle>
                  )}
                  {/* Connection label */}
                  <text
                    x={midX}
                    y={midY - 8}
                    textAnchor="middle"
                    fill="#94A3B8"
                    fontSize="10"
                    className={`transition-opacity ${isDimmed ? 'opacity-20' : 'opacity-100'}`}
                  >
                    {conn.label}
                  </text>
                </g>
              );
            })}
          </svg>

          {/* Nodes */}
          {nodes.map((node) => {
            const isHovered = hoveredNode === node.id;
            const isDimmed = hoveredNode && hoveredNode !== node.id;
            const statusColor = node.status === 'active' ? 'bg-success' : node.status === 'warning' ? 'bg-warning' : 'bg-muted-foreground';

            return (
              <div
                key={node.id}
                className={`absolute transition-all duration-200 ${isDimmed ? 'opacity-40' : 'opacity-100'}`}
                style={{
                  left: node.x,
                  top: node.y,
                  width: nodeWidth,
                  height: nodeHeight,
                  zIndex: isHovered ? 10 : 1,
                }}
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
              >
                <div
                  className={`w-full h-full rounded-xl border ${node.borderColor} ${node.bgColor} p-3 cursor-pointer transition-all ${
                    isHovered ? 'scale-105 shadow-lg' : 'hover:scale-102'
                  }`}
                >
                  {/* Status dot */}
                  <div className="flex items-center justify-between mb-2">
                    <div className={`p-1.5 rounded-lg ${node.bgColor}`}>
                      <node.icon className={`h-4 w-4 ${node.color}`} />
                    </div>
                    <div className={`h-2 w-2 rounded-full ${statusColor} ${node.status === 'active' ? 'cyber-pulse' : ''}`} />
                  </div>
                  {/* Label */}
                  <p className="text-xs font-semibold text-foreground">{node.label}</p>
                  <p className="text-[10px] text-muted-foreground">{node.sublabel}</p>
                  {node.count && (
                    <p className={`text-[10px] font-bold mt-1 ${node.color}`}>{node.count}</p>
                  )}
                </div>

                {/* Hover tooltip */}
                {isHovered && (
                  <div className="absolute -top-20 left-1/2 -translate-x-1/2 bg-card border border-border rounded-lg shadow-xl p-2.5 w-48 z-20">
                    <div className="flex items-center gap-2 mb-1.5">
                      <node.icon className={`h-3.5 w-3.5 ${node.color}`} />
                      <span className="text-xs font-semibold text-foreground">{node.label}</span>
                    </div>
                    <p className="text-[10px] text-muted-foreground leading-relaxed">
                      {getNodeDescription(node.id)}
                    </p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Chain Summary */}
      <div className="mt-4 grid grid-cols-3 gap-3">
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <CheckCircle2 className="h-3.5 w-3.5 text-success" />
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Chain Integrity</span>
          </div>
          <p className="text-sm font-bold text-success">Verified</p>
          <p className="text-[10px] text-muted-foreground">All evidence cryptographically linked</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <Clock className="h-3.5 w-3.5 text-cyber" />
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Avg Latency</span>
          </div>
          <p className="text-sm font-bold text-cyber">4.2 min</p>
          <p className="text-[10px] text-muted-foreground">Event to evidence mapping</p>
        </div>
        <div className="bg-surface rounded-lg p-3 border border-border/50">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle className="h-3.5 w-3.5 text-warning" />
            <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">Gaps Detected</span>
          </div>
          <p className="text-sm font-bold text-warning">2 controls</p>
          <p className="text-[10px] text-muted-foreground">Missing evidence linkage</p>
        </div>
      </div>
    </div>
  );
}

function getNodeDescription(id: string): string {
  const descriptions: Record<string, string> = {
    strike: 'Strike Engine (Module 1) generates security events through automated scanning and monitoring of IT assets.',
    validator: 'Validator (Module 2) verifies and validates evidence from the Strike Engine before storing it.',
    evidence: 'Validated evidence is stored with immutable hashing for audit traceability and compliance verification.',
    control: 'Evidence is mapped to specific compliance controls across frameworks (ISO 27001, GDPR, NIST, etc.).',
    framework: 'Control compliance status is aggregated to calculate framework-level compliance scores.',
    report: 'Compliance data is compiled into audit-ready reports for executives and stakeholders.',
  };
  return descriptions[id] || '';
}
