/**
 * Jarvis 4.0 – Main Page
 * Assembles the 3-column layout with all components.
 */
'use client';

import React, { useCallback, useState } from 'react';
import { ThreeColumnLayout } from '@/components/Layout/ThreeColumnLayout';
import { JarvisMonacoEditor } from '@/components/Editor/MonacoEditor';
import { SkillsSidebar } from '@/components/Sidebar/SkillsSidebar';
import { FileExplorer } from '@/components/FileExplorer/FileExplorer';
import { CommandBar, type JarvisCommand } from '@/components/CommandBar/CommandBar';
import { SandboxTerminal } from '@/components/Terminal/SandboxTerminal';
import { ThreadMonitor } from '@/components/Monitors/ThreadMonitor';
import { useWebSocket } from '@/hooks/useWebSocket';
import { ChatPanel } from '@/components/Chat/ChatPanel';
import { UploadPanel } from '@/components/Upload/UploadPanel';

const INITIAL_CODE = `# Jarvis 4.0 – Ready
# Open a file from the explorer or use /search to find code.

print("Hello from Jarvis 4.0")
`;

export default function Home() {
  const [editorContent, setEditorContent] = useState(INITIAL_CODE);
  const [activeFile, setActiveFile] = useState<string | undefined>(undefined);
  const [showTerminal, setShowTerminal] = useState(false);
  const [showFileExplorer, setShowFileExplorer] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [rightTab, setRightTab] = useState<'chat' | 'logs'>('chat');
  const [injectMessage, setInjectMessage] = useState<string | undefined>(undefined);
  const { lines, connected, clear } = useWebSocket();

  const handleFileSelect = useCallback((path: string, content: string) => {
    setActiveFile(path);
    setEditorContent(content);
  }, []);

  const COMMANDS: JarvisCommand[] = [
    {
      name: 'refactor',
      description: 'Apply refactor_logic_v1 to active file',
      icon: '♻',
      handler: async () => {
        const res = await fetch('/api/agent/refactor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ file: activeFile, content: editorContent }),
        });
        if (res.ok) { const d = await res.json(); setEditorContent(d.result); }
      },
    },
    {
      name: 'test',
      description: 'Run pytest on current project',
      icon: '🧪',
      handler: async () => {
        await fetch('/api/agent/test', { method: 'POST' });
      },
    },
    {
      name: 'security',
      description: 'Run OWASP scan on active file',
      icon: '🔒',
      handler: async () => {
        await fetch('/api/agent/security', {
          method: 'POST',
          body: JSON.stringify({ content: editorContent }),
          headers: { 'Content-Type': 'application/json' },
        });
      },
    },
    {
      name: 'overdrive',
      description: 'Start next AWP batch',
      icon: '⚡',
      handler: async () => {
        await fetch('/api/agent/overdrive', { method: 'POST' });
      },
    },
    {
      name: 'ingest',
      description: 'Ingest /strategy/ docs into RAG',
      icon: '📥',
      handler: async () => {
        await fetch('/api/ingest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ target_dir: 'strategy' }),
        });
      },
    },
    {
      name: 'search',
      description: 'Semantic search in RAG memory',
      icon: '🔍',
      handler: async (args) => {
        if (!args) return;
        const res = await fetch('http://localhost:8000/search', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ query: args, top_k: 5 }),
        });
        const data = await res.json();
        const summary = data.results?.length
          ? `RAG-Suche: "${args}" → ${data.count} Treffer\n\n` +
            data.results.map((r: { score: number; source: string; text: string }, i: number) =>
              `**[${i + 1}] Score: ${r.score.toFixed(2)} | ${r.source.split('::')[0].split(/[\\/]/).pop()}**\n${r.text.slice(0, 300)}…`
            ).join('\n\n')
          : `RAG-Suche: "${args}" → Keine Ergebnisse.`;
        setInjectMessage(summary);
        setRightTab('chat');
      },
    },
    {
      name: 'terminal',
      description: 'Toggle sandbox terminal',
      icon: '⌨',
      handler: () => { setShowTerminal((v) => !v); },
    },
    {
      name: 'clear',
      description: 'Clear log stream',
      icon: '🗑',
      handler: () => { clear(); },
    },
  ];

  return (
    <ThreeColumnLayout
      commandBar={<CommandBar commands={COMMANDS} />}
      left={
        <>
          <SkillsSidebar />
          <CollapsibleSection
            title="File Explorer"
            open={showFileExplorer}
            onToggle={() => setShowFileExplorer((v) => !v)}
          >
            <FileExplorer onFileSelect={handleFileSelect} />
          </CollapsibleSection>
          <CollapsibleSection
            title="RAG Upload"
            open={showUpload}
            onToggle={() => setShowUpload((v) => !v)}
          >
            <UploadPanel />
          </CollapsibleSection>
          <ThreadMonitor />
        </>
      }
      center={
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
          <JarvisMonacoEditor
            value={editorContent}
            onChange={setEditorContent}
            fileName={activeFile}
          />
          {showTerminal && (
            <div style={{ height: 260, borderTop: '1px solid var(--color-border)', flexShrink: 0 }}>
              <SandboxTerminal />
            </div>
          )}
        </div>
      }
      right={
        <RightPanel
          tab={rightTab}
          onTabChange={setRightTab}
          lines={lines}
          connected={connected}
          activeFile={activeFile}
          activeContent={editorContent}
          injectMessage={injectMessage}
          onInjectConsumed={() => setInjectMessage(undefined)}
        />
      }
    />
  );
}

function CollapsibleSection({
  title, open, onToggle, children,
}: {
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: open ? 1 : 'none', minHeight: 0 }}>
      <div
        onClick={onToggle}
        style={{
          padding: '6px var(--spacing-md)',
          fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
          textTransform: 'uppercase', color: 'var(--color-text-muted)',
          background: 'var(--color-bg-tertiary)',
          borderBottom: '1px solid var(--color-border)',
          cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6,
          userSelect: 'none',
        }}
      >
        <span style={{ fontSize: 8 }}>{open ? '▾' : '▸'}</span>
        {title}
      </div>
      {open && (
        <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          {children}
        </div>
      )}
    </div>
  );
}

function RightPanel({
  tab, onTabChange, lines, connected, activeFile, activeContent, injectMessage, onInjectConsumed,
}: {
  tab: 'chat' | 'logs';
  onTabChange: (t: 'chat' | 'logs') => void;
  lines: Array<{ ts: string; level: string; service: string; message: string }>;
  connected: boolean;
  activeFile?: string;
  activeContent?: string;
  injectMessage?: string;
  onInjectConsumed?: () => void;
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Tab bar */}
      <div style={{
        display: 'flex', flexShrink: 0,
        borderBottom: '1px solid var(--color-border)',
        background: 'var(--color-bg-tertiary)',
      }}>
        {(['chat', 'logs'] as const).map((t) => (
          <button
            key={t}
            onClick={() => onTabChange(t)}
            style={{
              flex: 1, padding: '6px 0',
              fontSize: 10, fontWeight: 700,
              letterSpacing: '0.12em', textTransform: 'uppercase',
              border: 'none', cursor: 'pointer',
              background: tab === t ? 'var(--color-bg-secondary)' : 'transparent',
              color: tab === t ? 'var(--aura-primary)' : 'var(--color-text-muted)',
              borderBottom: tab === t ? '2px solid var(--aura-primary)' : '2px solid transparent',
              transition: 'color 0.15s',
            }}
          >
            {t === 'chat' ? 'Chat' : 'Live Logs'}
          </button>
        ))}
      </div>
      <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        {tab === 'chat'
          ? <ChatPanel
              activeFile={activeFile}
              activeContent={activeContent}
              injectMessage={injectMessage}
              onInjectConsumed={onInjectConsumed}
            />
          : <LogPanel lines={lines} connected={connected} />}
      </div>
    </div>
  );
}

function LogPanel({
  lines,
  connected,
}: {
  lines: Array<{ ts: string; level: string; service: string; message: string }>;
  connected: boolean;
}) {
  const levelColor: Record<string, string> = {
    ERROR: 'var(--aura-alert-primary)',
    WARNING: 'var(--aura-proc-primary)',
    INFO: 'var(--color-text-secondary)',
    DEBUG: 'var(--color-text-muted)',
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '6px 12px', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.12em', textTransform: 'uppercase',
        color: 'var(--color-text-muted)',
        background: 'var(--color-bg-tertiary)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
      }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%',
          background: connected ? 'var(--aura-ok-primary)' : 'var(--aura-alert-primary)' }} />
        Live Logs
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: 4 }}>
        {lines.length === 0 && (
          <div style={{ padding: 12, fontSize: 11, color: 'var(--color-text-muted)' }}>
            Waiting for log stream…
          </div>
        )}
        {lines.map((line, i) => (
          <div key={i} style={{
            padding: '1px 6px',
            fontFamily: 'var(--font-mono)', fontSize: 11,
            borderLeft: '2px solid transparent',
            borderLeftColor: levelColor[line.level] ?? 'transparent',
          }}>
            <span style={{ color: 'var(--color-text-muted)', marginRight: 4 }}>
              {line.ts.slice(11, 19)}
            </span>
            <span style={{ color: levelColor[line.level], marginRight: 4, fontSize: 10 }}>
              {line.level}
            </span>
            <span style={{ color: 'var(--aura-primary)', marginRight: 4, fontSize: 10 }}>
              [{line.service}]
            </span>
            <span style={{ color: 'var(--color-text-primary)' }}>{line.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
