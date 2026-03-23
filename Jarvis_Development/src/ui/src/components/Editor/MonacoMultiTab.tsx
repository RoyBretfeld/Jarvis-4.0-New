/**
 * AWP-051 – Monaco Multi-Tab Editor
 * Tab bar for multiple open files. Each tab has its own editor state.
 * AWP-028: GPU-accelerated, no layout-thrash animations.
 */
'use client';

import React, { useCallback, useRef, useState } from 'react';
import { JarvisMonacoEditor, type SupportedLanguage } from './MonacoEditor';

export interface EditorTab {
  id: string;
  fileName: string;
  content: string;
  language?: SupportedLanguage;
  isDirty: boolean;
}

interface MonacoMultiTabProps {
  initialTabs?: EditorTab[];
  onSave?: (tab: EditorTab) => Promise<void>;
}

let _tabCounter = 1;

function makeTab(fileName: string, content: string): EditorTab {
  return {
    id: `tab-${_tabCounter++}`,
    fileName,
    content,
    isDirty: false,
  };
}

export function MonacoMultiTab({
  initialTabs,
  onSave,
}: MonacoMultiTabProps) {
  const [tabs, setTabs] = useState<EditorTab[]>(
    initialTabs ?? [makeTab('untitled.py', '# New file\n')]
  );
  const [activeId, setActiveId] = useState(tabs[0]?.id ?? '');

  const activeTab = tabs.find((t) => t.id === activeId) ?? tabs[0];

  const openFile = useCallback((fileName: string, content: string) => {
    setTabs((prev) => {
      const existing = prev.find((t) => t.fileName === fileName);
      if (existing) { setActiveId(existing.id); return prev; }
      const tab = makeTab(fileName, content);
      setActiveId(tab.id);
      return [...prev, tab];
    });
  }, []);

  const closeTab = useCallback((id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setTabs((prev) => {
      const next = prev.filter((t) => t.id !== id);
      if (next.length === 0) return [makeTab('untitled.py', '')];
      if (activeId === id) setActiveId(next[next.length - 1].id);
      return next;
    });
  }, [activeId]);

  const handleChange = useCallback((content: string) => {
    setTabs((prev) =>
      prev.map((t) => t.id === activeId ? { ...t, content, isDirty: true } : t)
    );
  }, [activeId]);

  const handleSave = useCallback(async () => {
    if (!activeTab || !onSave) return;
    await onSave(activeTab);
    setTabs((prev) =>
      prev.map((t) => t.id === activeTab.id ? { ...t, isDirty: false } : t)
    );
  }, [activeTab, onSave]);

  // Ctrl+S
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.ctrlKey && e.key === 's') { e.preventDefault(); handleSave(); }
  }, [handleSave]);

  return (
    <div
      style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
      onKeyDown={handleKeyDown}
    >
      {/* Tab Bar */}
      <div style={{
        display: 'flex', overflowX: 'auto', flexShrink: 0,
        background: 'var(--color-bg-secondary)',
        borderBottom: '1px solid var(--color-border)',
        scrollbarWidth: 'none',
      }}>
        {tabs.map((tab) => (
          <TabItem
            key={tab.id}
            tab={tab}
            isActive={tab.id === activeId}
            onClick={() => setActiveId(tab.id)}
            onClose={(e) => closeTab(tab.id, e)}
          />
        ))}
        <button
          onClick={() => {
            const t = makeTab('untitled.py', '');
            setTabs((p) => [...p, t]);
            setActiveId(t.id);
          }}
          style={{
            padding: '0 10px', background: 'transparent', border: 'none',
            color: 'var(--color-text-muted)', cursor: 'pointer', fontSize: 16,
            flexShrink: 0,
          }}
          title="New tab"
        >
          +
        </button>
      </div>

      {/* Editor */}
      {activeTab && (
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <JarvisMonacoEditor
            key={activeTab.id}
            value={activeTab.content}
            onChange={handleChange}
            fileName={activeTab.fileName}
            language={activeTab.language}
          />
        </div>
      )}
    </div>
  );
}

function TabItem({
  tab, isActive, onClick, onClose,
}: {
  tab: EditorTab;
  isActive: boolean;
  onClick: () => void;
  onClose: (e: React.MouseEvent) => void;
}) {
  return (
    <div
      onClick={onClick}
      className="transition-aura"
      style={{
        display: 'flex', alignItems: 'center', gap: 4,
        padding: '0 12px',
        height: 32,
        cursor: 'pointer',
        flexShrink: 0,
        userSelect: 'none',
        borderRight: '1px solid var(--color-border)',
        background: isActive ? 'var(--color-bg-primary)' : 'transparent',
        borderBottom: isActive
          ? `2px solid var(--aura-primary)` : '2px solid transparent',
        color: isActive
          ? 'var(--color-text-primary)' : 'var(--color-text-muted)',
      }}
    >
      <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12 }}>
        {tab.isDirty && <span style={{ color: 'var(--aura-proc-primary)', marginRight: 3 }}>●</span>}
        {tab.fileName.split('/').pop()}
      </span>
      <span
        onClick={onClose}
        style={{
          fontSize: 14, lineHeight: 1, opacity: 0.5, cursor: 'pointer',
          padding: '0 2px', borderRadius: 2,
        }}
        onMouseEnter={(e) => (e.currentTarget.style.opacity = '1')}
        onMouseLeave={(e) => (e.currentTarget.style.opacity = '0.5')}
      >
        ×
      </span>
    </div>
  );
}

// Export openFile for external use (FileExplorer callback)
export type { MonacoMultiTabProps };
