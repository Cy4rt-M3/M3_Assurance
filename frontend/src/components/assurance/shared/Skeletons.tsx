'use client';

import React from 'react';
import { Skeleton } from '@/components/ui/skeleton';
import { cn } from '@/lib/utils';

/**
 * ShimmerSkeleton — wraps the shadcn Skeleton component and applies the
 * `.shimmer` CSS class (defined in globals.css). The shimmer class overrides
 * the default `bg-accent` / `animate-pulse` styles with an animated gradient
 * background for a more premium loading feel.
 */
function ShimmerSkeleton({ className, ...props }: React.ComponentProps<'div'>) {
  return (
    <Skeleton
      className={cn('shimmer border-0', className)}
      {...props}
    />
  );
}

// KPI Card Skeleton
export function KpiCardSkeleton() {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-3">
      <ShimmerSkeleton className="h-3 w-24" />
      <ShimmerSkeleton className="h-8 w-16" />
      <ShimmerSkeleton className="h-2 w-32" />
    </div>
  );
}

// Chart Skeleton
export function ChartSkeleton({ height = 'h-64' }: { height?: string }) {
  return (
    <div className="bg-card border border-border rounded-xl p-5 space-y-4">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <ShimmerSkeleton className="h-4 w-40" />
          <ShimmerSkeleton className="h-3 w-56" />
        </div>
        <ShimmerSkeleton className="h-8 w-8 rounded-lg" />
      </div>
      <ShimmerSkeleton className={`${height} w-full rounded-lg`} />
    </div>
  );
}

// Table Row Skeleton
export function TableRowSkeleton({ columns = 6 }: { columns?: number }) {
  return (
    <tr className="border-b border-border/50">
      {Array.from({ length: columns }).map((_, i) => (
        <td key={i} className="px-4 py-3">
          <ShimmerSkeleton
            className="h-4 w-full"
            style={{ maxWidth: `${100 / columns}%` }}
          />
        </td>
      ))}
    </tr>
  );
}

// Table Skeleton
export function TableSkeleton({
  rows = 5,
  columns = 6,
}: {
  rows?: number;
  columns?: number;
}) {
  return (
    <div className="bg-card border border-border rounded-xl overflow-hidden">
      <div className="border-b border-border p-4 flex items-center justify-between">
        <ShimmerSkeleton className="h-4 w-32" />
        <ShimmerSkeleton className="h-8 w-24 rounded-lg" />
      </div>
      <table className="w-full">
        <tbody>
          {Array.from({ length: rows }).map((_, i) => (
            <TableRowSkeleton key={i} columns={columns} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

// Dashboard Skeleton (full page)
export function DashboardSkeleton() {
  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <ShimmerSkeleton className="h-6 w-48" />
          <ShimmerSkeleton className="h-4 w-64" />
        </div>
        <ShimmerSkeleton className="h-8 w-32 rounded-lg" />
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <KpiCardSkeleton key={i} />
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartSkeleton />
        <ChartSkeleton />
      </div>
    </div>
  );
}

// List Item Skeleton
export function ListItemSkeleton() {
  return (
    <div className="flex items-center justify-between p-3 rounded-lg bg-surface border border-border/50">
      <div className="space-y-2 flex-1">
        <ShimmerSkeleton className="h-3 w-48" />
        <ShimmerSkeleton className="h-2 w-32" />
      </div>
      <ShimmerSkeleton className="h-6 w-12" />
    </div>
  );
}
