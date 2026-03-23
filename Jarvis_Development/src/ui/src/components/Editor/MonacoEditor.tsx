/**
 * AWP-023 – Monaco Editor Component
 * Syntax-Highlighting für Python, JavaScript, TypeScript, Markdown.
 * Lazy-loaded (dynamic import), damit der initiale Bundle klein bleibt.
 * AWP-028: Editor nutzt GPU-composited Layer.
 */
'use client';

import React, { useCallback, useRef, useState } from 'react';
import type * as Monaco from 'monaco-editor';

// Dynamic import – Monaco ist ~3 MB, wird erst bei Bedarf geladen
const Editor = React.lazy(() =>
  import('@monaco-editor/react').then((m) => ({ default: m.Editor }))
);

export type SupportedLanguage = 'python' | 'javascript' | 'typescript' | 'markdown' | 'json' | 'yaml';

interface MonacoEditorProps {
  value: string;
  onChange?: (value: string) => void;
  language?: SupportedLanguage;
  readOnly?: boolean;
  fileName?: string;
}

const JARVIS_THEME: Monaco.editor.IStandaloneThemeData = {
  base: 'vs-dark',
  inherit: true,
  rules: [
    { token: 'comment',   foreground: '5a6585', fontStyle: 'italic' },
    { token: 'keyword',   foreground: '8b5cf6' },
    { token: 'string',    foreground: '22c55e' },
    { token: 'number',    foreground: 'f59e0b' },
    { token: 'type',      foreground: '3b82f6' },
    { token: 'function',  foreground: '60a5fa' },
    { token: 'variable',  foreground: 'e8ecf4' },
  ],
  colors: {
    'editor.background':           '#0d0f14',
    'editor.foreground':           '#e8ecf4',
    'editor.lineHighlightBackground': '#1a1e28',
    'editorLineNumber.foreground': '#5a6585',
    'editorLineNumber.activeForeground': '#9aa5c4',
    'editor.selectionBackground':  '#2a3148',
    'editorCursor.foreground':     '#8b5cf6',
    'scrollbar.shadow':            '#00000000',
    'scrollbarSlider.background':  '#2a3148aa',
    'scrollbarSlider.hoverBackground': '#3b82f6aa',
  },
};

function detectLanguage(fileName?: string): SupportedLanguage {
  if (!fileName) return 'python';
  if (fileName.endsWith('.py')) return 'python';
  if (fileName.endsWith('.ts') || fileName.endsWith('.tsx')) return 'typescript';
  if (fileName.endsWith('.js') || fileName.endsWith('.jsx')) return 'javascript';
  if (fileName.endsWith('.md')) return 'markdown';
  if (fileName.endsWith('.json')) return 'json';
  if (fileName.endsWith('.yml') || fileName.endsWith('.yaml')) return 'yaml';
  return 'python';
}

export function JarvisMonacoEditor({
  value,
  onChange,
  language,
  readOnly = false,
  fileName,
}: MonacoEditorProps) {
  const editorRef = useRef<Monaco.editor.IStandaloneCodeEditor | null>(null);
  const resolvedLang = language ?? detectLanguage(fileName);

  const handleMount = useCallback(
    (editor: Monaco.editor.IStandaloneCodeEditor, monaco: typeof Monaco) => {
      editorRef.current = editor;
      monaco.editor.defineTheme('jarvis-dark', JARVIS_THEME);
      monaco.editor.setTheme('jarvis-dark');

      // Performance: disable expensive features we don't need yet
      editor.updateOptions({
        minimap: { enabled: false },
        scrollBeyondLastLine: false,
        renderWhitespace: 'none',
        // AWP-028: GPU compositing
        renderValidationDecorations: 'on',
        smoothScrolling: true,
        cursorSmoothCaretAnimation: 'on',
        fastScrollSensitivity: 10,
      });
    },
    []
  );

  return (
    <div
      className="gpu-layer"
      style={{ flex: 1, overflow: 'hidden', position: 'relative' }}
    >
      {/* File tab bar */}
      {fileName && (
        <div
          style={{
            padding: '0 var(--spacing-md)',
            height: 32,
            display: 'flex',
            alignItems: 'center',
            borderBottom: '1px solid var(--color-border)',
            background: 'var(--color-bg-secondary)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            color: 'var(--color-text-secondary)',
            gap: 6,
          }}
        >
          <LanguageBadge language={resolvedLang} />
          {fileName}
        </div>
      )}

      <React.Suspense
        fallback={
          <div
            style={{
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              height: '100%', color: 'var(--color-text-muted)',
              fontFamily: 'var(--font-mono)',
            }}
          >
            Loading editor…
          </div>
        }
      >
        <Editor
          height="100%"
          language={resolvedLang}
          value={value}
          theme="jarvis-dark"
          onChange={(v) => onChange?.(v ?? '')}
          onMount={handleMount}
          options={{ readOnly }}
        />
      </React.Suspense>
    </div>
  );
}

function LanguageBadge({ language }: { language: string }) {
  const colors: Record<string, string> = {
    python: '#3b82f6', javascript: '#f59e0b', typescript: '#3b82f6',
    markdown: '#9aa5c4', json: '#22c55e', yaml: '#8b5cf6',
  };
  return (
    <span
      style={{
        fontSize: 10,
        padding: '1px 5px',
        borderRadius: 3,
        background: colors[language] ?? '#5a6585',
        color: '#0d0f14',
        fontWeight: 700,
        textTransform: 'uppercase',
      }}
    >
      {language}
    </span>
  );
}
