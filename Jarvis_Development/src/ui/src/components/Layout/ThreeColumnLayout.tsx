/**
 * AWP-022 – Three-Column Layout
 * Left:   System-Status + File-Explorer + Skills
 * Center: Monaco Editor
 * Right:  Chat / Logs (resizable via drag handle)
 *
 * AWP-028: GPU-beschleunigt – keine layout-triggernden Animations-Props.
 */
'use client';

import React, { useCallback, useRef, useState } from 'react';
import Link from 'next/link';

const MIN_CHAT_WIDTH = 240;
const MAX_CHAT_WIDTH = 900;
const DEFAULT_CHAT_WIDTH = 340;

interface ThreeColumnLayoutProps {
  left: React.ReactNode;
  center: React.ReactNode;
  right: React.ReactNode;
  commandBar: React.ReactNode;
}

export function ThreeColumnLayout({
  left,
  center,
  right,
  commandBar,
}: ThreeColumnLayoutProps) {
  const [chatWidth, setChatWidth] = useState(DEFAULT_CHAT_WIDTH);
  const [statusInfo] = useState({ branch: 'main', line: 1, col: 1, encoding: 'UTF-8', version: 'v4.0-SOVEREIGN' });
  const dragging = useRef(false);
  const startX = useRef(0);
  const startWidth = useRef(0);

  const onMouseDown = useCallback((e: React.MouseEvent) => {
    dragging.current = true;
    startX.current = e.clientX;
    startWidth.current = chatWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      if (!dragging.current) return;
      const delta = startX.current - ev.clientX; // drag left = wider
      const next = Math.min(MAX_CHAT_WIDTH, Math.max(MIN_CHAT_WIDTH, startWidth.current + delta));
      setChatWidth(next);
    };

    const onMouseUp = () => {
      dragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  }, [chatWidth]);

  return (
    <div
      className="gpu-layer"
      style={{
        display: 'grid',
        gridTemplateRows: `var(--header-height) 1fr var(--commandbar-height) 24px`,
        gridTemplateColumns: `var(--sidebar-width) 1fr ${chatWidth}px`,
        gridTemplateAreas: `
          "header  header  header"
          "left    center  right"
          "cmdbar  cmdbar  cmdbar"
          "status  status  status"
        `,
        height: '100vh',
        overflow: 'hidden',
        background: 'var(--color-bg-primary)',
      }}
    >
      {/* Header */}
      <header
        style={{
          gridArea: 'header',
          display: 'flex',
          alignItems: 'center',
          padding: '0 var(--spacing-md)',
          gap: 'var(--spacing-md)',
          background: 'var(--color-bg-secondary)',
          borderBottom: '1px solid var(--color-border)',
          zIndex: 10,
        }}
      >
        <span
          style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 700,
            fontSize: 15,
            color: 'var(--aura-primary)',
            letterSpacing: '0.05em',
            transition: 'color var(--transition-normal)',
          }}
        >
          JARVIS 4.0
        </span>
        <AuraIndicator />

        {/* View Navigation */}
        <div style={{ display: 'flex', gap: 4, marginLeft: 'auto' }}>
          {[
            { label: 'Chat', href: '/chat', active: false },
            { label: 'RAG',  href: '/rag',  active: false },
            { label: 'IDE',  href: '/',     active: true  },
          ].map(({ label, href, active }) => (
            <Link key={label} href={href} style={{
              padding: '3px 12px', borderRadius: 3,
              fontSize: 10, fontWeight: 700, letterSpacing: '0.1em',
              textDecoration: 'none',
              background: active ? 'var(--aura-primary)' : 'transparent',
              color: active ? '#000' : 'var(--color-text-muted)',
              border: active ? 'none' : '1px solid var(--color-border)',
              transition: 'all 0.15s',
            }}>{label}</Link>
          ))}
        </div>
      </header>

      {/* Left Column */}
      <aside
        className="transition-aura"
        style={{
          gridArea: 'left',
          overflowY: 'auto',
          borderRight: '1px solid var(--color-border)',
          background: 'var(--color-bg-secondary)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {left}
      </aside>

      {/* Center Column – Monaco Editor */}
      <main
        style={{
          gridArea: 'center',
          overflow: 'hidden',
          background: 'var(--color-bg-primary)',
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {center}
      </main>

      {/* Right Column – Chat / Logs */}
      <aside
        className="transition-aura"
        style={{
          gridArea: 'right',
          overflowY: 'auto',
          borderLeft: '1px solid var(--color-border)',
          background: 'var(--color-bg-secondary)',
          display: 'flex',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* Drag Handle */}
        <div
          onMouseDown={onMouseDown}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: 5,
            cursor: 'col-resize',
            zIndex: 20,
          }}
          title="Spalte verbreitern"
        />
        {right}
      </aside>

      {/* Command Bar */}
      <footer
        style={{
          gridArea: 'cmdbar',
          borderTop: '1px solid var(--color-border)',
          background: 'var(--color-bg-tertiary)',
          zIndex: 10,
        }}
      >
        {commandBar}
      </footer>

      {/* IDE Status Bar */}
      <div
        style={{
          gridArea: 'status',
          display: 'flex', justifyContent: 'space-between', alignItems: 'center',
          padding: '0 12px',
          background: '#080f18',
          borderTop: '1px solid var(--color-border)',
          fontFamily: 'var(--font-ui)', fontSize: 11, fontWeight: 500,
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {[
            { icon: 'terminal', label: 'Ollama' },
            { icon: 'hub',      label: 'Qdrant' },
            { icon: 'memory',   label: 'ChromaDB' },
          ].map(item => (
            <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--aura-ok-primary)', cursor: 'pointer' }}>
              <span className="material-symbols-outlined" style={{ fontSize: 13 }}>{item.icon}</span>
              <span>{item.label}</span>
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span style={{ color: 'var(--color-text-muted)', cursor: 'pointer' }}>Ln {statusInfo.line}, Col {statusInfo.col}</span>
          <span style={{ color: 'var(--color-text-muted)', cursor: 'pointer' }}>{statusInfo.encoding}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: 4, color: 'var(--aura-ok-primary)', fontWeight: 700 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--aura-ok-primary)', display: 'inline-block', animation: 'pulse 2s infinite' }} />
            <span>{statusInfo.version}</span>
          </div>
        </div>
      </div>
    </div>
  );
}

/** Pulsierender Statusindikator in der Header-Leiste */
function AuraIndicator() {
  return (
    <div
      className="aura-active gpu-layer"
      style={{
        width: 10,
        height: 10,
        borderRadius: '50%',
        background: 'var(--aura-primary)',
        transition: 'background var(--transition-normal)',
        flexShrink: 0,
      }}
      title="System Aura Status"
    />
  );
}
