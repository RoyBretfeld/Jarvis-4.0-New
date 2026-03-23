/**
 * AWP-027 – Command Bar
 * Eingabezeile mit Autocomplete für /-Befehle.
 * Befehle: /refactor /test /overdrive /ingest /search /status /clear
 */
'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';

export interface JarvisCommand {
  name: string;         // e.g. "refactor"
  description: string;
  icon: string;
  handler: (args: string) => void | Promise<void>;
}

interface CommandBarProps {
  commands: JarvisCommand[];
  onSubmit?: (raw: string) => void;
  disabled?: boolean;
}

const BUILTIN_PREFIXES = ['refactor', 'test', 'overdrive', 'ingest', 'search',
                          'status', 'clear', 'help', 'security', 'agent'];

export function CommandBar({ commands, onSubmit, disabled }: CommandBarProps) {
  const [input, setInput] = useState('');
  const [suggestions, setSuggestions] = useState<JarvisCommand[]>([]);
  const [selectedIdx, setSelectedIdx] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Build suggestion list whenever input changes
  useEffect(() => {
    if (!input.startsWith('/')) { setSuggestions([]); return; }
    const query = input.slice(1).toLowerCase();
    const matches = commands.filter((c) => c.name.toLowerCase().startsWith(query));
    setSuggestions(matches);
    setSelectedIdx(0);
  }, [input, commands]);

  const executeCommand = useCallback(
    async (raw: string) => {
      const trimmed = raw.trim();
      if (!trimmed) return;
      if (trimmed.startsWith('/')) {
        const [cmdPart, ...argParts] = trimmed.slice(1).split(' ');
        const cmd = commands.find((c) => c.name === cmdPart);
        if (cmd) {
          await cmd.handler(argParts.join(' '));
        } else {
          onSubmit?.(trimmed);
        }
      } else {
        onSubmit?.(trimmed);
      }
      setInput('');
      setSuggestions([]);
    },
    [commands, onSubmit]
  );

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (suggestions.length > 0) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSelectedIdx((i) => Math.min(i + 1, suggestions.length - 1)); return; }
      if (e.key === 'ArrowUp') { e.preventDefault(); setSelectedIdx((i) => Math.max(i - 1, 0)); return; }
      if (e.key === 'Tab') { e.preventDefault(); setInput('/' + suggestions[selectedIdx].name + ' '); return; }
      if (e.key === 'Enter' && suggestions[selectedIdx]) {
        e.preventDefault();
        setInput('/' + suggestions[selectedIdx].name + ' ');
        return;
      }
    }
    if (e.key === 'Enter') { e.preventDefault(); executeCommand(input); }
    if (e.key === 'Escape') { setInput(''); setSuggestions([]); }
  };

  return (
    <div style={{ position: 'relative', height: '100%' }}>
      {/* Autocomplete dropdown */}
      {suggestions.length > 0 && (
        <div style={{
          position: 'absolute', bottom: '100%', left: 0, right: 0,
          background: 'var(--color-bg-elevated)',
          border: '1px solid var(--color-border)',
          borderBottom: 'none',
          borderRadius: '6px 6px 0 0',
          maxHeight: 200, overflowY: 'auto',
          zIndex: 50,
        }}>
          {suggestions.map((cmd, i) => (
            <div
              key={cmd.name}
              onClick={() => { setInput('/' + cmd.name + ' '); inputRef.current?.focus(); }}
              style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '6px 12px',
                cursor: 'pointer',
                background: i === selectedIdx ? 'var(--aura-pulse)' : 'transparent',
                borderLeft: i === selectedIdx
                  ? '2px solid var(--aura-primary)' : '2px solid transparent',
              }}
            >
              <span style={{ fontSize: 14 }}>{cmd.icon}</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 12,
                color: 'var(--aura-primary)' }}>
                /{cmd.name}
              </span>
              <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
                {cmd.description}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Input */}
      <div style={{
        display: 'flex', alignItems: 'center', height: '100%',
        padding: '0 var(--spacing-md)', gap: 8,
      }}>
        <span style={{ color: 'var(--aura-primary)', fontFamily: 'var(--font-mono)',
          fontSize: 14, userSelect: 'none' }}>
          ❯
        </span>
        <input
          ref={inputRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Type a message or /command…"
          autoComplete="off"
          spellCheck={false}
          style={{
            flex: 1, background: 'transparent', border: 'none', outline: 'none',
            fontFamily: 'var(--font-mono)', fontSize: 13,
            color: 'var(--color-text-primary)',
          }}
        />
        <span style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
          Tab to complete · Enter to send · Esc to clear
        </span>
      </div>
    </div>
  );
}
