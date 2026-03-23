/**
 * AWP-030 – useJarvisState
 * Polling-Hook: ruft GET /status alle N Sekunden ab und hält state.json live.
 */
'use client';

import { useEffect, useRef, useState } from 'react';

export type AuraState = 'idle' | 'processing' | 'alert' | 'success';

export interface WorkPackage {
  status: 'COMPLETED' | 'IN_PROGRESS' | 'SKIPPED' | 'PENDING';
  artifact?: string;
  note?: string;
}

export interface JarvisState {
  project: string;
  version: string;
  current_phase: string;
  last_updated: string;
  workpackages: Record<string, WorkPackage>;
  security: { owasp_scan: string; critical_findings: number; warnings: number };
}

interface UseJarvisStateOptions {
  pollIntervalMs?: number;
}

interface UseJarvisStateResult {
  state: JarvisState | null;
  aura: AuraState;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

function deriveAura(state: JarvisState | null, error: string | null): AuraState {
  if (error) return 'alert';
  if (!state) return 'idle';
  if (state.current_phase.includes('IN_PROGRESS')) return 'processing';
  if (state.security?.critical_findings > 0) return 'alert';
  if (state.current_phase.includes('COMPLETED')) return 'success';
  return 'idle';
}

export function useJarvisState({
  pollIntervalMs = 5000,
}: UseJarvisStateOptions = {}): UseJarvisStateResult {
  const [state, setState] = useState<JarvisState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const counterRef = useRef(0);

  const fetchState = async () => {
    try {
      const res = await fetch('/api/status');
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data: JarvisState = await res.json();
      setState(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
    const id = setInterval(fetchState, pollIntervalMs);
    return () => clearInterval(id);
  }, [pollIntervalMs]);

  // Apply aura class to <html> element
  const aura = deriveAura(state, error);
  useEffect(() => {
    document.documentElement.dataset.aura = aura;
  }, [aura]);

  return { state, aura, loading, error, refresh: fetchState };
}
