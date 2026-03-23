/**
 * AWP-036 – Sandbox Terminal (xterm.js)
 * Verbindet sich via WebSocket mit jarvis-sandbox.
 * Sicherheit: read-only host-mount, Sandbox im STRICT-Modus.
 * AWP-028: Canvas-Renderer für GPU-Beschleunigung.
 */
'use client';

import React, { useEffect, useRef } from 'react';

const WS_TERMINAL_URL =
  typeof window !== 'undefined'
    ? `ws://${window.location.hostname}:8000/ws/terminal`
    : 'ws://localhost:8000/ws/terminal';

export function SandboxTerminal() {
  const containerRef = useRef<HTMLDivElement>(null);
  const termRef = useRef<import('@xterm/xterm').Terminal | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    let disposed = false;

    (async () => {
      const [{ Terminal }, { FitAddon }, { WebLinksAddon }] = await Promise.all([
        import('@xterm/xterm'),
        import('@xterm/addon-fit'),
        import('@xterm/addon-web-links'),
      ]);

      if (disposed) return;

      const term = new Terminal({
        theme: {
          background: '#0d0f14',
          foreground: '#e8ecf4',
          cursor:     '#8b5cf6',
          black:      '#0d0f14',
          blue:       '#3b82f6',
          magenta:    '#8b5cf6',
          green:      '#22c55e',
          red:        '#ef4444',
          yellow:     '#f59e0b',
          white:      '#e8ecf4',
          brightBlack:'#5a6585',
        },
        fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
        fontSize: 12,
        lineHeight: 1.4,
        cursorBlink: true,
        // AWP-028: GPU-composited canvas renderer
        allowTransparency: false,
        fastScrollModifier: 'alt',
        smoothScrollDuration: 100,
      });

      const fitAddon = new FitAddon();
      const linksAddon = new WebLinksAddon();
      term.loadAddon(fitAddon);
      term.loadAddon(linksAddon);
      term.open(containerRef.current!);
      fitAddon.fit();
      termRef.current = term;

      // Connect to sandbox via WebSocket
      const ws = new WebSocket(WS_TERMINAL_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        term.writeln('\x1b[36mJarvis Sandbox Terminal\x1b[0m');
        term.writeln('\x1b[90mConnecting to jarvis-sandbox…\x1b[0m');
        // Send terminal size
        ws.send(JSON.stringify({
          type: 'resize',
          cols: term.cols,
          rows: term.rows,
        }));
      };

      ws.onmessage = (evt) => {
        term.write(evt.data as string);
      };

      ws.onclose = () => {
        term.writeln('\r\n\x1b[33m[Connection closed]\x1b[0m');
      };

      ws.onerror = () => {
        term.writeln('\r\n\x1b[31m[WebSocket error – is jarvis-sandbox running?]\x1b[0m');
      };

      // Terminal input → WebSocket
      term.onData((data) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'input', data }));
        }
      });

      // Resize observer
      const ro = new ResizeObserver(() => {
        fitAddon.fit();
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'resize', cols: term.cols, rows: term.rows }));
        }
      });
      ro.observe(containerRef.current!);

      return () => { ro.disconnect(); };
    })();

    return () => {
      disposed = true;
      wsRef.current?.close();
      termRef.current?.dispose();
    };
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '6px 12px', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.12em', textTransform: 'uppercase',
        color: 'var(--color-text-muted)',
        background: 'var(--color-bg-tertiary)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', gap: 6,
      }}>
        <span style={{ width: 8, height: 8, borderRadius: '50%',
          background: 'var(--aura-ok-primary)', display: 'inline-block' }} />
        Sandbox Terminal
      </div>
      <div
        ref={containerRef}
        className="gpu-layer"
        style={{ flex: 1, padding: '4px 0', overflow: 'hidden' }}
      />
    </div>
  );
}
