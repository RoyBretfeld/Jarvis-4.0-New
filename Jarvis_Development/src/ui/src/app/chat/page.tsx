/**
 * JARVIS 4.0 – Chat View
 * Layout: identisch mit RAG-System (Die Intelligente Schicht)
 * Farben, Struktur, Nav – 1:1 übernommen
 */
'use client';

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';

// ── RAG-identische Farben ───────────────────────────────────
const BG          = '#060e20';
const SURF_LOW    = '#091328';
const SURF        = '#0f1930';
const SURF_HIGH   = '#141f38';
const SURF_HIGHEST= '#192540';
const PRIMARY     = '#78b0ff';
const PRIMARY_C   = '#5ba2ff';
const SECONDARY   = '#70fda7';
const TERTIARY    = '#8895ff';
const ON_SURF     = '#dee5ff';
const ON_SURF_V   = '#a3aac4';
const OUTLINE     = '#6d758c';
const OUTLINE_V   = '#40485d';
const ERROR       = '#ff716c';

interface Message { role: 'user' | 'assistant'; content: string; }
interface Conversation { id: string; title: string; ts: string; messages: Message[]; }

function stripMarkdown(t: string) {
  return t
    .replace(/```[\s\S]*?```/g, '[Code]')
    .replace(/`[^`]+`/g, '').replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/\*([^*]+)\*/g, '$1').replace(/#{1,6}\s/g, '')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1').trim();
}

let _audio: HTMLAudioElement | null = null;
async function speak(text: string) {
  if (typeof window === 'undefined') return;
  if (_audio) { _audio.pause(); _audio = null; }
  try {
    const res = await fetch('/api/tts', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: stripMarkdown(text).slice(0, 800) }),
    });
    if (!res.ok) throw new Error();
    const url = URL.createObjectURL(await res.blob());
    _audio = new Audio(url);
    _audio.onended = () => URL.revokeObjectURL(url);
    await _audio.play();
  } catch {
    window.speechSynthesis?.cancel();
    const u = new SpeechSynthesisUtterance(stripMarkdown(text));
    u.lang = 'de-DE'; window.speechSynthesis?.speak(u);
  }
}

const NAV_LINKS = [
  { label: 'Chat', href: '/chat', active: true  },
  { label: 'RAG',  href: '/rag',  active: false },
  { label: 'IDE',  href: '/',     active: false },
];

export default function ChatPage() {
  const [messages, setMessages]         = useState<Message[]>([]);
  const [input, setInput]               = useState('');
  const [streaming, setStreaming]        = useState(false);
  const [ttsEnabled, setTtsEnabled]      = useState(true);
  const [convs, setConvs]               = useState<Conversation[]>([
    { id: '0', title: 'Neue Konversation', ts: 'Jetzt', messages: [] },
  ]);
  const [activeConv, setActiveConv]      = useState('0');
  const [activeNav, setActiveNav]        = useState('Chat');
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  useEffect(() => { if (!ttsEnabled) { _audio?.pause(); _audio = null; window.speechSynthesis?.cancel(); } }, [ttsEnabled]);

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;
    window.speechSynthesis?.cancel();

    const next: Message[] = [...messages, { role: 'user', content: text }];
    setMessages(next);
    setInput('');
    setStreaming(true);
    setMessages(m => [...m, { role: 'assistant', content: '' }]);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: next }),
      });
      if (!res.body) throw new Error('No stream');
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let full = '';
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        const chunk = dec.decode(value, { stream: true });
        full += chunk;
        setMessages(m => { const u = [...m]; u[u.length - 1] = { role: 'assistant', content: u[u.length - 1].content + chunk }; return u; });
      }
      if (ttsEnabled && full) speak(full);

      // Konversation speichern
      const title = text.slice(0, 42) + (text.length > 42 ? '…' : '');
      const newId = Date.now().toString();
      const newConv: Conversation = { id: newId, title, ts: new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }), messages: [...next, { role: 'assistant', content: full }] };
      setConvs(p => [newConv, ...p.filter(c => c.id !== '0').slice(0, 8)]);
      setActiveConv(newId);
    } catch (err) {
      setMessages(m => { const u = [...m]; u[u.length - 1] = { role: 'assistant', content: `[Fehler: ${err instanceof Error ? err.message : String(err)}]` }; return u; });
    } finally {
      setStreaming(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  }

  function loadConv(c: Conversation) { setMessages(c.messages); setActiveConv(c.id); }

  const memPct = Math.min(30 + messages.length * 4, 92);

  const sideNavItems = [
    { icon: 'chat',          label: 'Chat',        active: activeNav === 'Chat' },
    { icon: 'history',       label: 'Verlauf',     active: activeNav === 'Verlauf' },
    { icon: 'tune',          label: 'Einstellungen',active: activeNav === 'Einstellungen' },
  ];

  return (
    <div style={{ background: BG, color: ON_SURF, fontFamily: "'Inter', sans-serif", minHeight: '100vh' }}>

      {/* ── Top Nav (RAG-identisch) ─────────────────────── */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: BG, borderBottom: `1px solid ${OUTLINE_V}33`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0 24px', height: 52,
      }}>
        <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em', color: ON_SURF }}>
          JARVIS Chat
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <div style={{ display: 'flex', gap: 24 }}>
            {NAV_LINKS.map(({ label, href, active }) => (
              <Link key={label} href={href} style={{
                padding: '4px 14px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                letterSpacing: '0.1em', textDecoration: 'none',
                background: active ? PRIMARY : 'transparent',
                color: active ? '#002f5c' : ON_SURF_V,
                transition: 'all 0.15s',
              }}>{label}</Link>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <button onClick={() => setTtsEnabled(v => !v)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: ON_SURF_V, fontSize: 16, opacity: ttsEnabled ? 1 : 0.4 }} title={ttsEnabled ? 'Stimme aus' : 'Stimme an'}>
              {ttsEnabled ? '🔊' : '🔇'}
            </button>
            {['settings', 'notifications', 'account_circle'].map(icon => (
              <span key={icon} className="material-symbols-outlined" style={{ color: ON_SURF_V, cursor: 'pointer', fontSize: 22 }}>{icon}</span>
            ))}
          </div>
        </div>
      </nav>

      {/* ── Left Sidebar (RAG-identisch) ───────────────── */}
      <aside style={{
        position: 'fixed', left: 0, top: 0, bottom: 0, width: 256,
        background: SURF_LOW, borderRight: `1px solid ${OUTLINE_V}1a`,
        display: 'flex', flexDirection: 'column', paddingTop: 72, paddingBottom: 24, zIndex: 40,
      }}>
        <div style={{ padding: '0 24px', marginBottom: 32 }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, color: ON_SURF, margin: 0 }}>Chat Engine</h2>
          <p style={{ fontSize: 10, color: SECONDARY, letterSpacing: '0.2em', textTransform: 'uppercase', opacity: 0.8, marginTop: 2 }}>
            {convs.length} KONVERSATION{convs.length !== 1 ? 'EN' : ''}
          </p>
        </div>

        {/* Nav Items */}
        <div style={{ marginBottom: 16 }}>
          {sideNavItems.map(item => (
            <div key={item.label} onClick={() => setActiveNav(item.label)} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '12px 24px', cursor: 'pointer',
              color: item.active ? SECONDARY : ON_SURF_V,
              borderRight: item.active ? `2px solid ${SECONDARY}` : '2px solid transparent',
              background: item.active ? `linear-gradient(to right, ${PRIMARY}1a, transparent)` : 'transparent',
              transition: 'all 0.15s',
            }}>
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>{item.icon}</span>
              {item.label}
            </div>
          ))}
        </div>

        {/* Conversation History */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '0 8px', display: 'flex', flexDirection: 'column', gap: 4 }}>
          {convs.map(c => (
            <div key={c.id} onClick={() => loadConv(c)} style={{
              padding: '10px 16px', borderRadius: 8, cursor: 'pointer',
              background: activeConv === c.id ? `${SURF_HIGHEST}80` : 'transparent',
              borderLeft: `2px solid ${activeConv === c.id ? SECONDARY : 'transparent'}`,
              transition: 'all 0.15s',
            }}>
              <p style={{ fontSize: 12, fontWeight: 600, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', color: activeConv === c.id ? ON_SURF : ON_SURF_V }}>{c.title}</p>
              <p style={{ fontSize: 10, color: OUTLINE, margin: '2px 0 0' }}>{c.ts}</p>
            </div>
          ))}
        </div>

        {/* Bottom */}
        <div style={{ padding: '0 16px' }}>
          <button onClick={() => { setMessages([]); setInput(''); const id = Date.now().toString(); setConvs(p => [{ id, title: 'Neue Konversation', ts: 'Jetzt', messages: [] }, ...p]); setActiveConv(id); }} style={{
            width: '100%', padding: '10px 0', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: `linear-gradient(to right, ${PRIMARY}, ${PRIMARY_C})`,
            color: '#002f5c', fontWeight: 700, fontSize: 13,
            boxShadow: `0 8px 24px ${PRIMARY}1a`,
          }}>
            + Neue Konversation
          </button>
          <div style={{ marginTop: 24, borderTop: `1px solid ${OUTLINE_V}1a`, paddingTop: 16 }}>
            {/* Memory */}
            <div style={{ marginBottom: 8 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.1em' }}>SPEICHERLIMIT</span>
                <span style={{ fontSize: 10, color: PRIMARY }}>{memPct}%</span>
              </div>
              <div style={{ height: 4, background: `${OUTLINE_V}33`, borderRadius: 999 }}>
                <div style={{ height: '100%', background: PRIMARY, width: `${memPct}%`, borderRadius: 999, transition: 'width 0.5s' }} />
              </div>
            </div>
            {[{ icon: 'help', label: 'Support' }, { icon: 'terminal', label: 'Protokolle' }].map(item => (
              <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 8px', color: ON_SURF_V, cursor: 'pointer', fontSize: 12 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{item.icon}</span>
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Main Content ────────────────────────────────── */}
      <main style={{ paddingLeft: 256, paddingTop: 52, minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>

        {/* Chat Card */}
        <section style={{
          margin: 24, flex: 1, background: SURF, borderRadius: 12,
          border: `1px solid ${OUTLINE_V}0d`,
          display: 'flex', flexDirection: 'column', overflow: 'hidden',
          minHeight: 'calc(100vh - 100px)',
        }}>

          {/* Card Header */}
          <div style={{ padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: `${SURF_HIGHEST}33`, borderBottom: `1px solid ${OUTLINE_V}1a`, flexShrink: 0 }}>
            <h3 style={{ fontWeight: 700, color: ON_SURF, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="material-symbols-outlined" style={{ color: PRIMARY, fontVariationSettings: "'FILL' 1", fontSize: 20 }}>smart_toy</span>
              JARVIS · llama-3.3-70b
            </h3>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: streaming ? SECONDARY : ON_SURF_V }}>
                <span style={{ width: 7, height: 7, borderRadius: '50%', background: streaming ? SECONDARY : OUTLINE_V, display: 'inline-block', animation: streaming ? 'pulse 1s infinite' : 'none' }} />
                {streaming ? 'Generiert…' : 'Bereit'}
              </div>
              <button style={{ fontSize: 10, padding: '4px 12px', background: SURF_HIGH, borderRadius: 999, border: `1px solid ${OUTLINE_V}33`, color: ON_SURF_V, cursor: 'pointer' }}>Verlauf löschen</button>
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '32px 24px', scrollbarWidth: 'thin', scrollbarColor: `${OUTLINE_V} transparent` }}>
            {messages.length === 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 300, gap: 16, opacity: 0.6 }}>
                <span className="material-symbols-outlined" style={{ fontSize: 48, color: PRIMARY }}>smart_toy</span>
                <p style={{ fontSize: 14, color: ON_SURF_V, margin: 0 }}>Stelle eine Frage oder starte eine neue Konversation.</p>
              </div>
            )}
            <div style={{ maxWidth: 860, margin: '0 auto', display: 'flex', flexDirection: 'column', gap: 32 }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start' }}>
                  {msg.role === 'assistant' && (
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: `${PRIMARY}1a`, border: `1px solid ${PRIMARY}33`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16, color: PRIMARY }}>smart_toy</span>
                    </div>
                  )}
                  <div style={{ maxWidth: '72%' }}>
                    {msg.role === 'assistant' && (
                      <p style={{ fontSize: 10, fontWeight: 900, color: PRIMARY, textTransform: 'uppercase', letterSpacing: '0.15em', margin: '0 0 8px' }}>JARVIS</p>
                    )}
                    <div style={{
                      padding: '12px 16px', borderRadius: msg.role === 'user' ? '12px 12px 2px 12px' : '2px 12px 12px 12px',
                      background: msg.role === 'user' ? `${PRIMARY}1a` : SURF_HIGH,
                      border: `1px solid ${msg.role === 'user' ? `${PRIMARY}33` : `${OUTLINE_V}1a`}`,
                      fontSize: 14, lineHeight: 1.7, color: ON_SURF,
                      whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                    }}>
                      {msg.content || <span style={{ opacity: 0.4 }}>▋</span>}
                    </div>
                  </div>
                  {msg.role === 'user' && (
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: `${SECONDARY}1a`, border: `1px solid ${SECONDARY}33`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <span className="material-symbols-outlined" style={{ fontSize: 16, color: SECONDARY }}>person</span>
                    </div>
                  )}
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          </div>

          {/* Input */}
          <div style={{ padding: 24, borderTop: `1px solid ${OUTLINE_V}1a`, flexShrink: 0, background: `${SURF_LOW}80` }}>
            <div style={{ maxWidth: 860, margin: '0 auto' }}>
              <div style={{ display: 'flex', gap: 12, alignItems: 'flex-end' }}>
                <div style={{ flex: 1, background: SURF_HIGHEST, borderRadius: 12, border: `1px solid ${streaming ? PRIMARY : OUTLINE_V}33`, transition: 'border-color 0.3s', overflow: 'hidden' }}>
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Nachricht an JARVIS… (Enter senden, Shift+Enter Zeilenumbruch)"
                    rows={2}
                    style={{
                      width: '100%', background: 'transparent', border: 'none', outline: 'none',
                      color: ON_SURF, fontFamily: "'Inter', sans-serif", fontSize: 14,
                      padding: '14px 16px', resize: 'none', boxSizing: 'border-box',
                    }}
                  />
                </div>
                <button
                  onClick={send}
                  disabled={streaming || !input.trim()}
                  style={{
                    padding: '14px 24px', borderRadius: 12, border: 'none', cursor: streaming || !input.trim() ? 'not-allowed' : 'pointer',
                    background: `linear-gradient(135deg, ${PRIMARY}, ${PRIMARY_C})`,
                    color: '#002f5c', fontWeight: 900, fontSize: 13,
                    opacity: streaming || !input.trim() ? 0.5 : 1,
                    display: 'flex', alignItems: 'center', gap: 8,
                    transition: 'opacity 0.2s',
                    flexShrink: 0,
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 18, fontVariationSettings: "'FILL' 1" }}>{streaming ? 'hourglass_empty' : 'send'}</span>
                  {streaming ? 'Lädt…' : 'Senden'}
                </button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Ambient glow */}
      <div style={{ position: 'fixed', top: '25%', right: 0, width: 384, height: 384, background: `${PRIMARY}0d`, filter: 'blur(120px)', pointerEvents: 'none', zIndex: -1 }} />
      <div style={{ position: 'fixed', bottom: 0, left: '25%', width: 500, height: 300, background: `${TERTIARY}0d`, filter: 'blur(150px)', pointerEvents: 'none', zIndex: -1 }} />
    </div>
  );
}
