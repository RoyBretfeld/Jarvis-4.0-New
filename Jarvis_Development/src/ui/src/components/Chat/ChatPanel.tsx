/**
 * JARVIS 4.0 – Chat Panel
 * Konversation mit llama-3.3-70b-versatile via Groq (Streaming).
 * - TTS via Web Speech API (mute-toggle)
 * - Datei-Kontext: aktive Datei wird als System-Kontext mitgeschickt
 */
'use client';

import React, { useEffect, useRef, useState } from 'react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatPanelProps {
  activeFile?: string;
  activeContent?: string;
  injectMessage?: string;
  onInjectConsumed?: () => void;
}

function stripMarkdown(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, '[Code-Block]')
    .replace(/`[^`]+`/g, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1')
    .replace(/#{1,6}\s/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .trim();
}

let _currentAudio: HTMLAudioElement | null = null;

async function speak(text: string) {
  if (typeof window === 'undefined') return;
  // Stop any running audio
  if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }

  try {
    const res = await fetch('/api/tts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: stripMarkdown(text).slice(0, 800) }),
    });
    if (!res.ok) throw new Error(`TTS HTTP ${res.status}`);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    _currentAudio = new Audio(url);
    _currentAudio.onended = () => URL.revokeObjectURL(url);
    await _currentAudio.play();
  } catch {
    // Fallback: Browser Web Speech API
    window.speechSynthesis?.cancel();
    const utt = new SpeechSynthesisUtterance(stripMarkdown(text));
    utt.lang = 'de-DE';
    utt.rate = 1.05;
    window.speechSynthesis?.speak(utt);
  }
}

export function ChatPanel({
  activeFile, activeContent, injectMessage, onInjectConsumed,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Inject external message (z.B. Search-Ergebnisse) als assistant-Nachricht
  useEffect(() => {
    if (!injectMessage) return;
    setMessages((m) => [...m, { role: 'assistant', content: injectMessage }]);
    onInjectConsumed?.();
  }, [injectMessage]); // eslint-disable-line react-hooks/exhaustive-deps

  // Stimme stoppen wenn Mute aktiviert wird
  useEffect(() => {
    if (!ttsEnabled) {
      if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
      window.speechSynthesis?.cancel();
    }
  }, [ttsEnabled]);

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;

    window.speechSynthesis?.cancel();

    const next: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setStreaming(true);
    setMessages((m) => [...m, { role: 'assistant', content: '' }]);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: next,
          activeFile,
          activeContent: activeContent?.slice(0, 8000), // max 8k Zeichen
        }),
      });
      if (!res.body) throw new Error('No stream');

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let done = false;
      let fullResponse = '';

      while (!done) {
        const { value, done: d } = await reader.read();
        done = d;
        if (value) {
          const chunk = decoder.decode(value, { stream: true });
          fullResponse += chunk;
          setMessages((m) => {
            const updated = [...m];
            updated[updated.length - 1] = {
              role: 'assistant',
              content: updated[updated.length - 1].content + chunk,
            };
            return updated;
          });
        }
      }

      if (ttsEnabled && fullResponse) speak(fullResponse);
    } catch (err) {
      setMessages((m) => {
        const updated = [...m];
        updated[updated.length - 1] = {
          role: 'assistant',
          content: `[Fehler: ${err instanceof Error ? err.message : String(err)}]`,
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div style={{
        padding: '4px 10px', fontSize: 10, fontWeight: 700,
        letterSpacing: '0.12em', textTransform: 'uppercase',
        color: 'var(--color-text-muted)',
        background: 'var(--color-bg-tertiary)',
        borderBottom: '1px solid var(--color-border)',
        display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0,
      }}>
        <span style={{ width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
          background: streaming ? 'var(--aura-proc-primary)' : 'var(--aura-ok-primary)' }} />
        <span style={{ flex: 1 }}>Chat · llama-3.3-70b</span>

        {/* Datei-Kontext-Indikator */}
        {activeFile && (
          <span style={{
            fontSize: 9, padding: '1px 5px',
            background: 'var(--color-bg-elevated)',
            border: '1px solid var(--color-border)',
            borderRadius: 3, color: 'var(--aura-primary)',
            fontFamily: 'var(--font-mono)',
            maxWidth: 100, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
          }} title={activeFile}>
            {activeFile.split(/[\\/]/).pop()}
          </span>
        )}

        {/* TTS Mute Toggle */}
        <button
          onClick={() => setTtsEnabled((v) => !v)}
          title={ttsEnabled ? 'Stimme ausschalten' : 'Stimme einschalten'}
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 14, padding: '0 2px',
            opacity: ttsEnabled ? 1 : 0.35,
            color: 'var(--color-text-muted)',
          }}
        >
          {ttsEnabled ? '🔊' : '🔇'}
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 4px' }}>
        {messages.length === 0 && (
          <div style={{ padding: 16, fontSize: 12, color: 'var(--color-text-muted)',
            textAlign: 'center', marginTop: 24, lineHeight: 1.8 }}>
            Frag JARVIS etwas…
            {activeFile && (
              <div style={{ marginTop: 8, fontSize: 10, color: 'var(--aura-primary)' }}>
                Kontext: {activeFile.split(/[\\/]/).pop()}
              </div>
            )}
          </div>
        )}
        {messages.map((msg, i) => (
          <MessageBubble key={i} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        borderTop: '1px solid var(--color-border)',
        padding: '6px 8px',
        display: 'flex', gap: 6, alignItems: 'flex-end', flexShrink: 0,
      }}>
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nachricht… (Enter senden, Shift+Enter Zeilenumbruch)"
          rows={2}
          style={{
            flex: 1, resize: 'none',
            background: 'var(--color-bg-primary)',
            border: '1px solid var(--color-border)',
            borderRadius: 4,
            color: 'var(--color-text-primary)',
            fontFamily: 'var(--font-mono)',
            fontSize: 12,
            padding: '6px 8px',
            outline: 'none',
          }}
        />
        <button
          onClick={send}
          disabled={streaming || !input.trim()}
          style={{
            padding: '6px 12px',
            background: streaming ? 'var(--color-bg-tertiary)' : 'var(--aura-primary)',
            color: streaming ? 'var(--color-text-muted)' : '#000',
            border: 'none', borderRadius: 4, cursor: streaming ? 'not-allowed' : 'pointer',
            fontSize: 12, fontWeight: 700, flexShrink: 0,
            transition: 'background 0.2s',
          }}
        >
          {streaming ? '…' : 'Send'}
        </button>
      </div>
    </div>
  );
}

function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 8,
      padding: '0 6px',
    }}>
      <div style={{
        maxWidth: '88%',
        padding: '6px 10px',
        borderRadius: isUser ? '10px 10px 2px 10px' : '10px 10px 10px 2px',
        background: isUser ? 'var(--aura-primary)' : 'var(--color-bg-elevated)',
        border: isUser ? 'none' : '1px solid var(--color-border)',
        color: isUser ? '#000' : 'var(--color-text-primary)',
        fontFamily: 'var(--font-mono)',
        fontSize: 12,
        lineHeight: 1.5,
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
      }}>
        {msg.content || <span style={{ opacity: 0.4 }}>▋</span>}
      </div>
    </div>
  );
}
