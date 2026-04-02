/**
 * JARVIS 4.0 – Chat Panel
 * AWP-101: Büroklammer-Upload + Drag-and-Drop
 * AWP-107: Fortschrittsanzeige beim Dokument-Upload
 * AWP-108: RAG-Kontext automatisch eingebunden (via route.ts)
 * AWP-115: Vektor-Pulse (Glow) während RAG-Suche
 * AWP-116: Source-Cards mit Relevanz-Score
 * AWP-117: Zitat-Links [1][2] mit Hover-Details
 * AWP-110: Dokument aus RAG löschen
 */
'use client';

import React, { useCallback, useEffect, useRef, useState } from 'react';

// AWP-116: Typdefinition für Source-Karten (muss mit route.ts übereinstimmen)
interface SourceInfo {
  id: number;
  file: string;
  source: string;
  score: number;
}

interface Message {
  role: 'user' | 'assistant';
  content: string;
  ragContext?: SourceInfo[];   // AWP-116: ersetzt sources?: string[]
}

interface IngestDoc {
  filename: string;
  chunks: number;
  size_mb: number;
  pages: number;
  uploaded_at: string;
}

type UploadStatus =
  | { state: 'idle' }
  | { state: 'uploading'; filename: string }
  | { state: 'processing'; filename: string }
  | { state: 'done'; filename: string; chunks: number }
  | { state: 'error'; message: string };

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
    window.speechSynthesis?.cancel();
    const utt = new SpeechSynthesisUtterance(stripMarkdown(text));
    utt.lang = 'de-DE';
    utt.rate = 1.05;
    window.speechSynthesis?.speak(utt);
  }
}

const BACKEND = 'http://127.0.0.1:8000';

export function ChatPanel({
  activeFile, activeContent, injectMessage, onInjectConsumed,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [streaming, setStreaming] = useState(false);
  const [ragSearching, setRagSearching] = useState(false);   // AWP-115
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [uploadStatus, setUploadStatus] = useState<UploadStatus>({ state: 'idle' });
  const [ingestDocs, setIngestDocs] = useState<IngestDoc[]>([]);
  const [showDocs, setShowDocs] = useState(false);
  const [dragging, setDragging] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!injectMessage) return;
    setMessages((m) => [...m, { role: 'assistant', content: injectMessage }]);
    onInjectConsumed?.();
  }, [injectMessage]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!ttsEnabled) {
      if (_currentAudio) { _currentAudio.pause(); _currentAudio = null; }
      window.speechSynthesis?.cancel();
    }
  }, [ttsEnabled]);

  // ── AWP-110: Dokumente laden ──────────────────────────────────────────────
  const loadDocs = useCallback(async () => {
    try {
      const res = await fetch(`${BACKEND}/ingest/documents`);
      if (res.ok) setIngestDocs(await res.json());
    } catch { /* offline */ }
  }, []);

  useEffect(() => { loadDocs(); }, [loadDocs]);

  // ── AWP-101/107: Upload-Handler ───────────────────────────────────────────
  const uploadFile = useCallback(async (file: File) => {
    const allowed = ['.pdf', '.txt', '.md'];
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowed.includes(ext)) {
      setUploadStatus({ state: 'error', message: `Nicht unterstützt: ${ext}` });
      return;
    }

    setUploadStatus({ state: 'uploading', filename: file.name });

    const formData = new FormData();
    formData.append('file', file);

    try {
      setUploadStatus({ state: 'processing', filename: file.name });
      const res = await fetch(`${BACKEND}/ingest/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? res.statusText);
      }

      const data = await res.json() as {
        filename: string; chunks: number; pages: number; size_mb: number;
      };
      setUploadStatus({
        state: 'done',
        filename: data.filename,
        chunks: data.chunks,
      });

      // Dokument-Liste aktualisieren
      await loadDocs();

      // Feedback als System-Nachricht im Chat
      setMessages((m) => [...m, {
        role: 'assistant',
        content: `Dokument im Gedächtnis gespeichert: **${data.filename}** (${data.pages} Seite(n), ${data.chunks} Chunks). Du kannst jetzt Fragen dazu stellen.`,
      }]);

      // Status nach 4s zurücksetzen
      setTimeout(() => setUploadStatus({ state: 'idle' }), 4000);
    } catch (err) {
      setUploadStatus({
        state: 'error',
        message: err instanceof Error ? err.message : String(err),
      });
      setTimeout(() => setUploadStatus({ state: 'idle' }), 5000);
    }
  }, [loadDocs]);

  // ── Drag & Drop ────────────────────────────────────────────────────────────
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  // ── AWP-110: Dokument löschen ──────────────────────────────────────────────
  const deleteDoc = useCallback(async (filename: string) => {
    try {
      await fetch(`${BACKEND}/ingest/document?filename=${encodeURIComponent(filename)}`, {
        method: 'DELETE',
      });
      await loadDocs();
      setMessages((m) => [...m, {
        role: 'assistant',
        content: `Dokument **${filename}** aus dem Gedächtnis entfernt.`,
      }]);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  }, [loadDocs]);

  // ── Chat Send ──────────────────────────────────────────────────────────────
  async function send() {
    const text = input.trim();
    if (!text || streaming) return;

    window.speechSynthesis?.cancel();

    const next: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setStreaming(true);
    setRagSearching(true);  // AWP-115: Glow startet während RAG-Suche
    setMessages((m) => [...m, { role: 'assistant', content: '' }]);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: next.map(({ role, content }) => ({ role, content })),
          activeFile,
          activeContent: activeContent?.slice(0, 8000),
        }),
      });

      // AWP-115: RAG-Phase abgeschlossen, sobald Response-Headers vorliegen
      setRagSearching(false);

      if (!res.body) throw new Error('No stream');

      // AWP-116: Quellen-Karten aus JSON-Header lesen
      let ragContext: SourceInfo[] = [];
      const ctxHeader = res.headers.get('X-RAG-Context');
      if (ctxHeader) {
        try { ragContext = JSON.parse(ctxHeader) as SourceInfo[]; } catch { /* ignore */ }
      }

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
              ragContext: ragContext.length ? ragContext : undefined,
            };
            return updated;
          });
        }
      }

      if (ttsEnabled && fullResponse) speak(fullResponse);
    } catch (err) {
      setRagSearching(false);
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

  // ── Upload-Status-Badge ───────────────────────────────────────────────────
  const statusBadge = (() => {
    if (uploadStatus.state === 'uploading')
      return <span style={{ fontSize: 9, color: 'var(--aura-proc-primary)' }}>Uploading {uploadStatus.filename}…</span>;
    if (uploadStatus.state === 'processing')
      return <span style={{ fontSize: 9, color: 'var(--aura-proc-primary)' }}>Verarbeite {uploadStatus.filename}…</span>;
    if (uploadStatus.state === 'done')
      return <span style={{ fontSize: 9, color: 'var(--aura-ok-primary)' }}>{uploadStatus.filename} ({uploadStatus.chunks} Chunks)</span>;
    if (uploadStatus.state === 'error')
      return <span style={{ fontSize: 9, color: 'var(--aura-alert-primary)' }}>{uploadStatus.message}</span>;
    return null;
  })();

  return (
    <div
      className={ragSearching ? 'rag-searching' : undefined}
      style={{ display: 'flex', flexDirection: 'column', height: '100%' }}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
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

        {/* AWP-101: Büroklammer + Docs-Count */}
        <button
          onClick={() => setShowDocs((v) => !v)}
          title={`${ingestDocs.length} Dokument(e) im Gedächtnis`}
          style={{
            background: showDocs ? 'var(--color-bg-elevated)' : 'none',
            border: showDocs ? '1px solid var(--color-border)' : 'none',
            cursor: 'pointer', fontSize: 13, padding: '0 4px',
            borderRadius: 3,
            color: ingestDocs.length ? 'var(--aura-primary)' : 'var(--color-text-muted)',
          }}
        >
          📎{ingestDocs.length > 0 && <span style={{ fontSize: 9, marginLeft: 1 }}>{ingestDocs.length}</span>}
        </button>

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

      {/* AWP-101: Ingest-Dokumente Panel */}
      {showDocs && (
        <div style={{
          background: 'var(--color-bg-elevated)',
          borderBottom: '1px solid var(--color-border)',
          padding: '6px 8px',
          flexShrink: 0,
          maxHeight: 160,
          overflowY: 'auto',
        }}>
          <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: '0.1em',
            textTransform: 'uppercase', color: 'var(--color-text-muted)', marginBottom: 4 }}>
            Gedächtnis-Dokumente
          </div>
          {ingestDocs.length === 0 ? (
            <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>
              Noch keine Dokumente. Lade eine PDF/TXT/MD-Datei hoch.
            </div>
          ) : (
            ingestDocs.map((doc) => (
              <div key={doc.filename} style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '2px 0', fontSize: 11,
              }}>
                <span style={{ flex: 1, color: 'var(--color-text-secondary)',
                  fontFamily: 'var(--font-mono)', overflow: 'hidden',
                  textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {doc.filename}
                </span>
                <span style={{ fontSize: 9, color: 'var(--color-text-muted)', flexShrink: 0 }}>
                  {doc.chunks} Chunks
                </span>
                <button
                  onClick={() => deleteDoc(doc.filename)}
                  title="Aus Gedächtnis entfernen"
                  style={{
                    background: 'none', border: 'none', cursor: 'pointer',
                    fontSize: 11, color: 'var(--aura-alert-primary)',
                    padding: '0 2px', flexShrink: 0,
                  }}
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {/* AWP-107: Upload-Progress-Bar */}
      {uploadStatus.state !== 'idle' && (
        <div style={{
          background: 'var(--color-bg-elevated)',
          borderBottom: '1px solid var(--color-border)',
          padding: '4px 10px',
          display: 'flex', alignItems: 'center', gap: 6,
          flexShrink: 0,
        }}>
          {(uploadStatus.state === 'uploading' || uploadStatus.state === 'processing') && (
            <div style={{
              width: 12, height: 12, borderRadius: '50%',
              border: '2px solid var(--color-border)',
              borderTopColor: 'var(--aura-proc-primary)',
              animation: 'spin 0.8s linear infinite',
              flexShrink: 0,
            }} />
          )}
          {statusBadge}
        </div>
      )}

      {/* Drag-over Overlay */}
      {dragging && (
        <div style={{
          position: 'absolute', inset: 0, zIndex: 20,
          background: 'rgba(0,200,100,0.08)',
          border: '2px dashed var(--aura-ok-primary)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          pointerEvents: 'none',
        }}>
          <span style={{ fontSize: 13, color: 'var(--aura-ok-primary)', fontWeight: 700 }}>
            Datei hier ablegen
          </span>
        </div>
      )}

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '8px 4px', position: 'relative' }}>
        {messages.length === 0 && (
          <div style={{ padding: 16, fontSize: 12, color: 'var(--color-text-muted)',
            textAlign: 'center', marginTop: 24, lineHeight: 1.8 }}>
            Frag JARVIS etwas… oder lade ein Dokument hoch (📎)
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
        {/* AWP-101: Büroklammer-Button */}
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          style={{ display: 'none' }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) { uploadFile(f); e.target.value = ''; }
          }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={uploadStatus.state === 'uploading' || uploadStatus.state === 'processing'}
          title="Dokument hochladen (PDF, TXT, MD)"
          style={{
            background: 'none',
            border: '1px solid var(--color-border)',
            borderRadius: 4,
            cursor: 'pointer',
            fontSize: 16,
            padding: '4px 6px',
            color: 'var(--color-text-muted)',
            flexShrink: 0,
            opacity: (uploadStatus.state === 'uploading' || uploadStatus.state === 'processing') ? 0.4 : 1,
          }}
        >
          📎
        </button>

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

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }

        /* AWP-115: Vektor-Pulse Glow während RAG-Suche */
        @keyframes rag-border-glow {
          0%, 100% { box-shadow: inset 0 0 0 1px rgba(139,92,246,0.3), 0 0 8px rgba(139,92,246,0.1); }
          50%       { box-shadow: inset 0 0 0 1px rgba(139,92,246,0.9), 0 0 24px rgba(139,92,246,0.35); }
        }
        .rag-searching {
          animation: rag-border-glow 1.1s ease-in-out infinite;
        }

        /* AWP-117: Citation-Badge */
        .citation-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 16px; height: 16px;
          border-radius: 50%;
          background: var(--aura-proc-primary, #8b5cf6);
          color: #fff;
          font-size: 9px;
          font-weight: 700;
          vertical-align: super;
          margin: 0 1px;
          cursor: default;
          position: relative;
        }
        .citation-badge:hover .citation-tooltip {
          display: block;
        }
        .citation-tooltip {
          display: none;
          position: absolute;
          bottom: calc(100% + 4px);
          left: 50%;
          transform: translateX(-50%);
          background: #1a1e28;
          border: 1px solid #2a3148;
          border-radius: 6px;
          padding: 6px 8px;
          white-space: nowrap;
          font-size: 10px;
          color: #e8ecf4;
          z-index: 100;
          box-shadow: 0 4px 12px rgba(0,0,0,0.5);
          pointer-events: none;
        }
      `}</style>
    </div>
  );
}

// AWP-117: Zitat-Rendering — ersetzt [1] durch hoverable Citation-Badges
function renderWithCitations(text: string, sources?: SourceInfo[]): React.ReactNode {
  if (!sources?.length || !text) return text || <span style={{ opacity: 0.4 }}>▋</span>;

  const parts = text.split(/(\[\d+\])/g);
  return (
    <>
      {parts.map((part, i) => {
        const match = part.match(/^\[(\d+)\]$/);
        if (!match) return <React.Fragment key={i}>{part}</React.Fragment>;
        const num = parseInt(match[1]);
        const src = sources.find((s) => s.id === num);
        if (!src) return <React.Fragment key={i}>{part}</React.Fragment>;
        return (
          <span key={i} className="citation-badge">
            {num}
            <span className="citation-tooltip">
              {src.file} · {Math.round(src.score * 100)}%
            </span>
          </span>
        );
      })}
    </>
  );
}

// AWP-116: Source-Card mit Relevanz-Score-Balken
function SourceCard({ src }: { src: SourceInfo }) {
  const pct = Math.round(src.score * 100);
  const barColor = pct >= 75 ? 'var(--aura-ok-primary)'
    : pct >= 50 ? 'var(--aura-primary)'
    : 'var(--aura-proc-primary)';

  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '3px 6px',
      background: 'var(--color-bg-tertiary)',
      border: '1px solid var(--color-border)',
      borderRadius: 5,
      minWidth: 0,
    }}>
      <span style={{
        fontSize: 8, fontWeight: 700, letterSpacing: '0.1em',
        color: 'var(--aura-primary)',
        flexShrink: 0,
      }}>
        [{src.id}]
      </span>
      <span style={{
        fontSize: 9, color: 'var(--color-text-secondary)',
        fontFamily: 'var(--font-mono)',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        flex: 1,
      }}>
        {src.file}
      </span>
      {/* Score-Balken */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 3, flexShrink: 0 }}>
        <div style={{ width: 28, height: 3, background: 'var(--color-border)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ width: `${pct}%`, height: '100%', background: barColor, borderRadius: 2 }} />
        </div>
        <span style={{ fontSize: 8, color: 'var(--color-text-muted)', width: 24, textAlign: 'right' }}>
          {pct}%
        </span>
      </div>
    </div>
  );
}

// AWP-116/117: Message-Bubble mit Source-Cards und Citation-Links
function MessageBubble({ msg }: { msg: Message }) {
  const isUser = msg.role === 'user';
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
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
        {isUser
          ? (msg.content || <span style={{ opacity: 0.4 }}>▋</span>)
          : renderWithCitations(msg.content, msg.ragContext)
        }
      </div>

      {/* AWP-116: Source-Cards mit Score */}
      {!isUser && msg.ragContext && msg.ragContext.length > 0 && (
        <div style={{
          marginTop: 4,
          display: 'flex', flexWrap: 'wrap', gap: 3,
          maxWidth: '88%',
        }}>
          {msg.ragContext.map((src) => (
            <SourceCard key={src.id} src={src} />
          ))}
        </div>
      )}
    </div>
  );
}
