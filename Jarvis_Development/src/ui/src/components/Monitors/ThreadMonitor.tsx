/**
 * AWP-037 – Thread Monitor Widget
 * Visualisiert die Last der 32 Threads des Ryzen 9 7950X.
 * Daten von GET /api/system/threads (polling, 1s).
 * AWP-028: Canvas-basiert für minimalen DOM-Overhead.
 */
'use client';

import React, { useEffect, useRef, useState } from 'react';

interface ThreadData {
  threads: number[];   // 0-100 per thread (32 values)
  timestamp: string;
}

const ZONE_COLORS: Record<string, string> = {
  core:    '#3b82f6',   // Threads 0-1
  gateway: '#22c55e',   // Threads 2-3
  rag:     '#8b5cf6',   // Threads 4-7
  sandbox: '#f59e0b',   // Threads 8-15
  free:    '#2a3148',   // Threads 16-31 (unzugewiesen)
};

function threadZone(idx: number): string {
  if (idx <= 1)  return 'core';
  if (idx <= 3)  return 'gateway';
  if (idx <= 7)  return 'rag';
  if (idx <= 15) return 'sandbox';
  return 'free';
}

export function ThreadMonitor() {
  const [data, setData] = useState<ThreadData | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const res = await fetch('/api/system/threads');
        if (!res.ok) throw new Error();
        setData(await res.json());
        setError(false);
      } catch {
        setError(true);
      }
    };
    poll();
    const id = setInterval(poll, 1000);
    return () => clearInterval(id);
  }, []);

  // Fallback: mock data when backend isn't available
  const threads = data?.threads ?? Array.from({ length: 32 }, (_, i) => {
    // Static placeholder showing zone utilization
    if (i <= 1)  return 15;
    if (i <= 3)  return 8;
    if (i <= 7)  return 45;
    if (i <= 15) return 60;
    return 5;
  });

  const avg = Math.round(threads.reduce((a, b) => a + b, 0) / threads.length);

  return (
    <div style={{
      padding: 'var(--spacing-sm)',
      borderTop: '1px solid var(--color-border)',
    }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        marginBottom: 6,
      }}>
        <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
          textTransform: 'uppercase', color: 'var(--color-text-muted)' }}>
          CPU Threads
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11,
          color: avg > 70 ? 'var(--aura-alert-primary)' : 'var(--color-text-secondary)' }}>
          avg {avg}%
        </span>
      </div>

      {/* Thread bars grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(16, 1fr)',
        gap: 2,
      }}>
        {threads.map((load, i) => {
          const zone = threadZone(i);
          const color = ZONE_COLORS[zone];
          return (
            <div
              key={i}
              title={`T${i}: ${load}% [${zone}]`}
              style={{
                height: 24,
                background: 'var(--color-bg-tertiary)',
                borderRadius: 2,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                className="gpu-layer"
                style={{
                  position: 'absolute', bottom: 0, left: 0, right: 0,
                  height: `${load}%`,
                  background: color,
                  opacity: 0.85,
                  transition: 'height 0.8s ease',
                }}
              />
            </div>
          );
        })}
      </div>

      {/* Zone legend */}
      <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
        {Object.entries(ZONE_COLORS).map(([zone, color]) => (
          <div key={zone} style={{ display: 'flex', alignItems: 'center', gap: 3 }}>
            <span style={{ width: 8, height: 8, borderRadius: 2,
              background: color, display: 'inline-block' }} />
            <span style={{ fontSize: 9, color: 'var(--color-text-muted)' }}>
              {zone}
            </span>
          </div>
        ))}
      </div>

      {error && (
        <div style={{ fontSize: 10, color: 'var(--aura-alert-primary)', marginTop: 4 }}>
          ⚠ Thread API nicht erreichbar – Placeholder-Daten
        </div>
      )}
    </div>
  );
}
