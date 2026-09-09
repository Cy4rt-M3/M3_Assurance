'use client';

import { useState, useEffect, useCallback } from 'react';

export interface RealFramework {
  id: string;
  name: string;
  version: string | null;
  controlCount: number;
}

export interface RealControl {
  controlId: string;
  controlName: string;
  description: string | null;
  functionDomain: string | null;
  category: string | null;
  keywords: string[];
  source: string | null;
  status: string | null;
  priority: string | null;
  parentControlId: string | null;
  controlLevel: string | null;
  controlObjective: string | null;
  controlType: string | null;
  evidenceRequired: boolean | null;
  evidenceType: string[];
  evidenceSource: string[];
  equivalentControls: string[];
  evidenceLink: string | null;
  owner: string | null;
  lastReviewed: string | null;
  notes: string | null;
}

export function useRealFrameworks() {
  const [frameworks, setFrameworks] = useState<RealFramework[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');

  useEffect(() => {
    let cancelled = false;
    fetch('/api/frameworks')
      .then((r) => r.json())
      .then((data) => {
        if (cancelled) return;
        setFrameworks(data.frameworks ?? []);
        setStatus('ready');
      })
      .catch(() => !cancelled && setStatus('error'));
    return () => {
      cancelled = true;
    };
  }, []);

  return { frameworks, status };
}

export function useRealControls(frameworkId: string | null) {
  const [controls, setControls] = useState<RealControl[]>([]);
  const [total, setTotal] = useState(0);
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');

  const reload = useCallback(
    (search?: string) => {
      if (!frameworkId) return;
      setStatus('loading');
      const params = new URLSearchParams({ pageSize: '200' });
      if (search) params.set('search', search);
      fetch(`/api/frameworks/${frameworkId}/controls?${params}`)
        .then((r) => r.json())
        .then((data) => {
          setControls(data.controls ?? []);
          setTotal(data.pagination?.total ?? 0);
          setStatus('ready');
        })
        .catch(() => setStatus('error'));
    },
    [frameworkId]
  );

  useEffect(() => {
    reload();
  }, [reload]);

  return { controls, total, status, reload };
}