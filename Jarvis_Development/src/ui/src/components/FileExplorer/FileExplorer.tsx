/**
 * AWP-029 – File Explorer
 * Interaktiver Datei-Browser für das Jarvis-Projektverzeichnis.
 * Daten kommen von GET /api/files?path=... (Backend-seitig path-restricted).
 * Öffnet Dateien im Monaco Editor via onFileSelect Callback.
 */
'use client';

import React, { useCallback, useEffect, useState } from 'react';

export interface FileNode {
  name: string;
  path: string;
  type: 'file' | 'directory';
  children?: FileNode[];
  size?: number;
  modified?: string;
}

interface FileExplorerProps {
  onFileSelect?: (path: string, content: string) => void;
}

const ICON: Record<string, string> = {
  py: '🐍', ts: '🔷', tsx: '🔷', js: '🟨', jsx: '🟨',
  md: '📄', json: '{}', yml: '⚙', yaml: '⚙', txt: '📝',
  directory: '📁', directory_open: '📂',
};

function fileIcon(node: FileNode, open?: boolean): string {
  if (node.type === 'directory') return open ? ICON.directory_open : ICON.directory;
  const ext = node.name.split('.').pop() ?? '';
  return ICON[ext] ?? '📄';
}

function FileNodeRow({
  node,
  depth = 0,
  onSelect,
}: {
  node: FileNode;
  depth?: number;
  onSelect: (path: string) => void;
}) {
  const [open, setOpen] = useState(false);

  const handleClick = useCallback(() => {
    if (node.type === 'directory') {
      setOpen((v) => !v);
    } else {
      onSelect(node.path);
    }
  }, [node, onSelect]);

  return (
    <>
      <div
        onClick={handleClick}
        style={{
          display: 'flex', alignItems: 'center', gap: 4,
          padding: `3px 8px 3px ${8 + depth * 12}px`,
          cursor: 'pointer',
          userSelect: 'none',
          fontSize: 12,
          color: node.type === 'directory'
            ? 'var(--color-text-secondary)'
            : 'var(--color-text-primary)',
          borderRadius: 3,
          transition: 'background var(--transition-fast)',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--color-bg-elevated)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      >
        {node.type === 'directory' && (
          <span style={{ fontSize: 8, color: 'var(--color-text-muted)', width: 8 }}>
            {open ? '▾' : '▸'}
          </span>
        )}
        <span style={{ fontSize: 12 }}>{fileIcon(node, open)}</span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: 11, flex: 1 }}>
          {node.name}
        </span>
        {node.type === 'file' && node.size !== undefined && (
          <span style={{ fontSize: 10, color: 'var(--color-text-muted)' }}>
            {formatSize(node.size)}
          </span>
        )}
      </div>
      {node.type === 'directory' && open && node.children?.map((child) => (
        <FileNodeRow key={child.path} node={child} depth={depth + 1} onSelect={onSelect} />
      ))}
    </>
  );
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}K`;
  return `${(bytes / 1024 / 1024).toFixed(1)}M`;
}

export function FileExplorer({ onFileSelect }: FileExplorerProps) {
  const [tree, setTree] = useState<FileNode[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/api/files')
      .then((r) => r.json())
      .then((data: FileNode[]) => { setTree(data); setLoading(false); })
      .catch((e) => { setError(String(e)); setLoading(false); });
  }, []);

  const handleSelect = useCallback(
    async (path: string) => {
      try {
        const res = await fetch(`/api/files/content?path=${encodeURIComponent(path)}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const { content } = await res.json() as { content: string };
        onFileSelect?.(path, content);
      } catch (e) {
        console.error('File load error:', e);
      }
    },
    [onFileSelect]
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <div style={{
        padding: '6px var(--spacing-md)',
        fontSize: 10, fontWeight: 700, letterSpacing: '0.12em',
        textTransform: 'uppercase', color: 'var(--color-text-muted)',
        background: 'var(--color-bg-tertiary)',
        borderBottom: '1px solid var(--color-border)',
      }}>
        File Explorer
      </div>
      <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
        {loading && <Msg text="Loading…" />}
        {error && <Msg text={`Error: ${error}`} danger />}
        {!loading && !error && tree.length === 0 && <Msg text="Empty" />}
        {tree.map((node) => (
          <FileNodeRow key={node.path} node={node} onSelect={handleSelect} />
        ))}
      </div>
    </div>
  );
}

function Msg({ text, danger }: { text: string; danger?: boolean }) {
  return (
    <div style={{ padding: '8px 12px', fontSize: 11,
      color: danger ? 'var(--aura-alert-primary)' : 'var(--color-text-muted)' }}>
      {text}
    </div>
  );
}
