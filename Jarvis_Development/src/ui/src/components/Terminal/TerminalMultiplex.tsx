/**
 * AWP-052 – Terminal Multiplexer
 * Mehrere Terminal-Instanzen in der UI:
 *   - Logs tab:    Read-only WebSocket log stream
 *   - Shell tab:   Interactive jarvis-sandbox xterm.js
 *   - Custom tabs: User-defined
 * AWP-028: GPU-composited containers per tab.
 */
'use client';

import React, { useCallback, useState } from 'react';
import { SandboxTerminal } from './SandboxTerminal';
import type { LogLine } from '@/hooks/useWebSocket';

type TerminalType = 'shell' | 'logs';

interface TerminalInstance {
  id: string;
  label: string;
  type: TerminalType;
}

interface TerminalMultiplexProps {
  logLines?: LogLine[];
  wsConnected?: boolean;
}

let _instCounter = 0;
function mkInstance(type: TerminalType): TerminalInstance {
  return { id: `term-${_instCounter++}`, label: type === 'shell' ? 'Shell' : 'Logs', type };
}

const LOG_LEVEL_COLOR: Record<string, string> = {
  ERROR:   'var(--aura-alert-primary)',
  WARNING: 'var(--aura-proc-primary)',
  INFO:    'var(--color-text-secondary)',
  DEBUG:   'var(--color-text-muted)',
};

export function TerminalMultiplex({ logLines = [], wsConnected = false }: TerminalMultiplexProps) {
  const [instances, setInstances] = useState<TerminalInstance[]>([
    mkInstance('logs'),
    mkInstance('shell'),
  ]);
  const [activeId, setActiveId] = useState(instances[0].id);

  const addShell = useCallback(() => {
    const inst = mkInstance('shell');
    inst.label = `Shell ${instances.filter(i => i.type === 'shell').length + 1}`;
    setInstances((p) => [...p, inst]);
    setActiveId(inst.id);
  }, [instances]);

  const close = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setInstances((prev) => {
      const next = prev.filter((t) => t.id !== id);
      if (next.length === 0) return [mkInstance('logs')];
      if (activeId === id) setActiveId(next[0].id);
      return next;
    });
  }, [activeId]);

  const active = instances.find((i) => i.id === activeId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex', alignItems: 'center', flexShrink: 0,
        background: 'var(--color-bg-tertiary)',
        borderBottom: '1px solid var(--color-border)',
        overflowX: 'auto',
      }}>
        {instances.map((inst) => (
          <div
            key={inst.id}
            onClick={() => setActiveId(inst.id)}
            style={{
              display: 'flex', alignItems: 'center', gap: 5,
              padding: '0 10px', height: 30, cursor: 'pointer',
              flexShrink: 0, userSelect: 'none', fontSize: 11,
              fontFamily: 'var(--font-mono)',
              background: inst.id === activeId ? 'var(--color-bg-secondary)' : 'transparent',
              color: inst.id === activeId ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
              borderRight: '1px solid var(--color-border)',
              borderBottom: inst.id === activeId
                ? '2px solid var(--aura-primary)' : '2px solid transparent',
            }}
          >
            <span>{inst.type === 'shell' ? '⌨' : '📋'}</span>
            <span>{inst.label}</span>
            {instances.length > 1 && (
              <span
                onClick={(e) => close(inst.id, e)}
                style={{ opacity: 0.5, fontSize: 13, cursor: 'pointer' }}
                onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
                onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.5')}
              >
                ×
              </span>
            )}
          </div>
        ))}
        <button
          onClick={addShell}
          title="New shell"
          style={{
            padding: '0 8px', background: 'transparent', border: 'none',
            color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 14,
          }}
        >
          +
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflow: 'hidden', position: 'relative' }}>
        {instances.map((inst) => (
          <div
            key={inst.id}
            className="gpu-layer"
            style={{
              position: 'absolute', inset: 0,
              // Use opacity + pointer-events instead of display:none
              // to avoid destroying xterm.js canvas on tab switch
              opacity: inst.id === activeId ? 1 : 0,
              pointerEvents: inst.id === activeId ? 'auto' : 'none',
            }}
          >
            {inst.type === 'shell'
              ? <SandboxTerminal />
              : <LogView lines={logLines} connected={wsConnected} />
            }
          </div>
        ))}
      </div>
    </div>
  );
}

function LogView({ lines, connected }: { lines: LogLine[]; connected: boolean }) {
  const logEndRef = React.useRef<HTMLDivElement>(null);
  React.useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [lines.length]);

  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: 4 }}>
      {lines.length === 0 && (
        <div style={{ padding: 8, color: 'var(--color-text-muted)', fontSize: 11 }}>
          {connected ? 'No logs yet…' : '⚠ WebSocket disconnected'}
        </div>
      )}
      {lines.map((line, i) => (
        <div key={i} style={{
          fontFamily: 'var(--font-mono)', fontSize: 11, padding: '1px 4px',
          borderLeft: '2px solid',
          borderLeftColor: LOG_LEVEL_COLOR[line.level] ?? 'transparent',
        }}>
          <span style={{ color: 'var(--color-text-muted)' }}>{line.ts.slice(11, 19)} </span>
          <span style={{ color: LOG_LEVEL_COLOR[line.level], fontSize: 9 }}>{line.level} </span>
          <span style={{ color: 'var(--aura-primary)', fontSize: 9 }}>[{line.service}] </span>
          <span style={{ color: 'var(--color-text-primary)' }}>{line.message}</span>
        </div>
      ))}
      <div ref={logEndRef} />
    </div>
  );
}
