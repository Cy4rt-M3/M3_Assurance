// Shared chart theme constants for consistent dark-theme visualizations

export const CHART_THEME = {
  // Axis & grid
  axis: '#94A3B8',
  axisLine: '#475569',
  grid: '#283448',
  tooltipBg: '#1E293B',
  tooltipBorder: '#334155',
  tooltipText: '#F1F5F9',

  // Data colors
  primary: '#2563EB',
  success: '#22C55E',
  warning: '#F59E0B',
  danger: '#EF4444',
  purple: '#8B5CF6',
  cyan: '#06B6D4',
  pink: '#EC4899',
  muted: '#64748B',
};

// Color palette for multi-series charts
export const CHART_PALETTE = [
  CHART_THEME.primary,
  CHART_THEME.success,
  CHART_THEME.warning,
  CHART_THEME.danger,
  CHART_THEME.purple,
  CHART_THEME.cyan,
];

export const TOOLTIP_STYLE = {
  backgroundColor: CHART_THEME.tooltipBg,
  border: `1px solid ${CHART_THEME.tooltipBorder}`,
  borderRadius: '8px',
  color: CHART_THEME.tooltipText,
  fontSize: 12,
  boxShadow: '0 4px 12px rgba(0, 0, 0, 0.3)',
};

export const AXIS_PROPS = {
  tick: { fill: CHART_THEME.axis, fontSize: 11 },
  axisLine: { stroke: CHART_THEME.axisLine },
  tickLine: { stroke: CHART_THEME.axisLine },
};

export const GRID_PROPS = {
  strokeDasharray: '3 3' as const,
  stroke: CHART_THEME.grid,
  vertical: false,
};
