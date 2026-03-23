/**
 * JARVIS 4.0 – RAG View
 * Design: "Die Intelligente Schicht" (system/rag/DESIGN.md)
 * Layout: Left sidebar | File Upload + Pipeline Tabelle + Crawler
 */
'use client';

import React, { useCallback, useRef, useState } from 'react';
import Link from 'next/link';

const BG       = '#060e20';
const SURF_LOW  = '#091328';
const SURF      = '#0f1930';
const SURF_HIGH = '#141f38';
const SURF_HIGHEST = '#192540';
const PRIMARY   = '#78b0ff';
const PRIMARY_C = '#5ba2ff';
const SECONDARY = '#70fda7';
const TERTIARY  = '#8895ff';
const ON_SURF   = '#dee5ff';
const ON_SURF_V = '#a3aac4';
const OUTLINE   = '#6d758c';
const OUTLINE_V = '#40485d';
const ERROR     = '#ff716c';
const ERROR_DIM = '#d7383b';

const BACKEND = '/api';
const ALLOWED = ['.pdf', '.md', '.txt'];
const MAX_MB  = 200;

type FileStatus = 'pending' | 'processing' | 'done' | 'error';
type IngestMethod = 'LLM Engine' | 'VLM Vision' | 'SQL Parser';

interface PipelineFile {
  id: string;
  filename: string;
  type: 'DOCUMENT' | 'IMAGE' | 'DATABASE' | 'TEXT';
  size_mb: number;
  method: IngestMethod;
  status: FileStatus;
  chunks?: number;
  error?: string;
}

interface CrawlLog {
  ts: string;
  level: 'INIT' | 'SUCCESS' | 'PARSING' | 'EXTRACT' | 'EMBEDDING' | 'WARNING';
  message: string;
}

const TYPE_COLOR: Record<string, string> = {
  DOCUMENT: TERTIARY,
  IMAGE:    PRIMARY,
  DATABASE: TERTIARY,
  TEXT:     SECONDARY,
};

const STATUS_ICON: Record<FileStatus, React.ReactNode> = {
  pending:    <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: OUTLINE }} />,
  processing: <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: SECONDARY, animation: 'pulse 1s infinite' }} />,
  done:       <span className="material-symbols-outlined" style={{ fontSize: 16, color: SECONDARY }}>check_circle</span>,
  error:      <span className="material-symbols-outlined" style={{ fontSize: 16, color: ERROR }}>error</span>,
};

const LOG_COLOR: Record<string, string> = {
  INIT:      PRIMARY,
  SUCCESS:   SECONDARY,
  PARSING:   TERTIARY,
  EXTRACT:   PRIMARY,
  EMBEDDING: ON_SURF,
  WARNING:   ERROR,
};

export default function RagPage() {
  const [dragging, setDragging] = useState(false);
  const [pipeline, setPipeline] = useState<PipelineFile[]>([]);
  const [logs, setLogs] = useState<CrawlLog[]>([]);
  const [crawlUrl, setCrawlUrl] = useState('');
  const [crawlDepth, setCrawlDepth] = useState<1 | 2 | 'MAX'>(1);
  const [crawling, setCrawling] = useState(false);
  const [storageUsed] = useState(64);
  const [activeNav, setActiveNav] = useState('Explorer');
  const inputRef = useRef<HTMLInputElement>(null);

  const addLog = useCallback((level: CrawlLog['level'], message: string) => {
    const ts = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [...prev.slice(-50), { ts, level, message }]);
  }, []);

  const uploadFile = useCallback(async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    const type: PipelineFile['type'] =
      ext === '.pdf' ? 'DOCUMENT' :
      ext === '.md'  ? 'TEXT' :
      ext === '.txt' ? 'TEXT' : 'DOCUMENT';

    if (!ALLOWED.includes(ext)) {
      const entry: PipelineFile = { id: Date.now().toString(), filename: file.name, type, size_mb: file.size / 1024 / 1024, method: 'LLM Engine', status: 'error', error: `Nicht erlaubt: ${ext}` };
      setPipeline(p => [entry, ...p]);
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      const entry: PipelineFile = { id: Date.now().toString(), filename: file.name, type, size_mb: file.size / 1024 / 1024, method: 'LLM Engine', status: 'error', error: `Zu groß (max ${MAX_MB}MB)` };
      setPipeline(p => [entry, ...p]);
      return;
    }

    const id = Date.now().toString();
    const entry: PipelineFile = { id, filename: file.name, type, size_mb: file.size / 1024 / 1024, method: 'LLM Engine', status: 'processing' };
    setPipeline(p => [entry, ...p]);
    addLog('INIT', `Upload gestartet: ${file.name}`);

    const form = new FormData();
    form.append('file', file);

    try {
      const xhr = new XMLHttpRequest();
      await new Promise<void>((resolve) => {
        xhr.open('POST', `${BACKEND}/upload`);
        xhr.onload = () => {
          try {
            const data = JSON.parse(xhr.responseText);
            if (xhr.status === 200) {
              setPipeline(p => p.map(e => e.id === id ? { ...e, status: 'done', chunks: data.chunks } : e));
              addLog('SUCCESS', `${file.name} → ${data.chunks} Chunks eingebettet`);
            } else {
              setPipeline(p => p.map(e => e.id === id ? { ...e, status: 'error', error: data.detail ?? `HTTP ${xhr.status}` } : e));
              addLog('WARNING', `Fehler bei ${file.name}: ${data.detail}`);
            }
          } catch {
            setPipeline(p => p.map(e => e.id === id ? { ...e, status: 'error', error: 'Parse error' } : e));
          }
          resolve();
        };
        xhr.onerror = () => {
          setPipeline(p => p.map(e => e.id === id ? { ...e, status: 'error', error: 'Netzwerkfehler' } : e));
          addLog('WARNING', `Netzwerkfehler bei ${file.name}`);
          resolve();
        };
        xhr.send(form);
      });
    } catch { /* already handled */ }
  }, [addLog]);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    for (const f of Array.from(files)) await uploadFile(f);
  }, [uploadFile]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  async function startCrawler() {
    if (!crawlUrl.trim() || crawling) return;
    setCrawling(true);
    addLog('INIT', `crawler_node_01 startet für ${crawlUrl}`);
    try {
      const res = await fetch(`${BACKEND}/crawl`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: crawlUrl, depth: crawlDepth === 'MAX' ? 5 : crawlDepth }),
      });
      if (res.ok) {
        addLog('SUCCESS', `Crawl abgeschlossen: ${crawlUrl}`);
      } else {
        addLog('WARNING', `Crawl fehlgeschlagen: HTTP ${res.status}`);
      }
    } catch {
      addLog('WARNING', `Crawler: Verbindung zu Backend nicht möglich`);
    } finally {
      setCrawling(false);
    }
  }

  const navItems = [
    { icon: 'folder_open', label: 'Explorer', active: true },
    { icon: 'database',    label: 'Abfrage' },
    { icon: 'language',    label: 'Scraping' },
    { icon: 'memory',      label: 'Verarbeitung' },
    { icon: 'settings',    label: 'Einstellungen' },
  ];

  return (
    <div style={{ background: BG, color: ON_SURF, fontFamily: "'Inter', sans-serif", minHeight: '100vh' }}>

      {/* Top Nav */}
      <nav style={{
        position: 'fixed', top: 0, left: 0, right: 0, zIndex: 50,
        background: BG, borderBottom: `1px solid ${OUTLINE_V}33`,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '0 24px', height: 52,
      }}>
        <div style={{ fontSize: 18, fontWeight: 900, letterSpacing: '-0.02em', color: ON_SURF }}>
          Die Intelligente Schicht
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
          <div style={{ display: 'flex', gap: 24 }}>
            {[
              { label: 'Chat', href: '/chat' },
              { label: 'RAG',  href: '/rag', active: true },
              { label: 'IDE',  href: '/' },
            ].map(({ label, href, active }) => (
              <Link key={label} href={href} style={{
                padding: '4px 14px', borderRadius: 4, fontSize: 11, fontWeight: 700,
                letterSpacing: '0.1em', textDecoration: 'none',
                background: active ? PRIMARY : 'transparent',
                color: active ? '#000' : ON_SURF_V,
                transition: 'all 0.15s',
              }}>{label}</Link>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 16 }}>
            {['settings', 'notifications', 'account_circle'].map(icon => (
              <span key={icon} className="material-symbols-outlined" style={{ color: ON_SURF_V, cursor: 'pointer', fontSize: 22, transition: 'color 0.2s' }}>{icon}</span>
            ))}
          </div>
        </div>
      </nav>

      {/* Left Sidebar */}
      <aside style={{
        position: 'fixed', left: 0, top: 0, bottom: 0, width: 256,
        background: SURF_LOW, borderRight: `1px solid ${OUTLINE_V}1a`,
        display: 'flex', flexDirection: 'column', paddingTop: 72, paddingBottom: 24, zIndex: 40,
      }}>
        <div style={{ padding: '0 24px', marginBottom: 32 }}>
          <h2 style={{ fontSize: 17, fontWeight: 900, color: ON_SURF }}>RAG Ökosystem</h2>
          <p style={{ fontSize: 10, color: SECONDARY, letterSpacing: '0.2em', textTransform: 'uppercase', opacity: 0.8, marginTop: 2 }}>
            AKTIVE KNOTEN: {pipeline.filter(f => f.status === 'done').length + 3}
          </p>
        </div>

        <div style={{ flex: 1 }}>
          {navItems.map(item => (
            <div
              key={item.label}
              onClick={() => setActiveNav(item.label)}
              style={{
                display: 'flex', alignItems: 'center', gap: 12,
                padding: '12px 24px', cursor: 'pointer',
                color: activeNav === item.label ? SECONDARY : ON_SURF_V,
                borderRight: activeNav === item.label ? `2px solid ${SECONDARY}` : '2px solid transparent',
                background: activeNav === item.label ? `linear-gradient(to right, ${PRIMARY}1a, transparent)` : 'transparent',
                transition: 'all 0.15s',
              }}
            >
              <span className="material-symbols-outlined" style={{ fontSize: 20 }}>{item.icon}</span>
              {item.label}
            </div>
          ))}
        </div>

        <div style={{ padding: '0 16px' }}>
          <button style={{
            width: '100%', padding: '10px 0', borderRadius: 12, border: 'none', cursor: 'pointer',
            background: `linear-gradient(to right, ${PRIMARY}, ${PRIMARY_C})`,
            color: '#002f5c', fontWeight: 700, fontSize: 13,
            boxShadow: `0 8px 24px ${PRIMARY}1a`,
          }}>
            Neue Abfrage
          </button>
          <div style={{ marginTop: 24, borderTop: `1px solid ${OUTLINE_V}1a`, paddingTop: 16, display: 'flex', flexDirection: 'column', gap: 4 }}>
            {[{ icon: 'help', label: 'Support' }, { icon: 'terminal', label: 'Protokolle' }].map(item => (
              <div key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '8px 8px', color: ON_SURF_V, cursor: 'pointer', fontSize: 12, transition: 'color 0.15s' }}>
                <span className="material-symbols-outlined" style={{ fontSize: 16 }}>{item.icon}</span>
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main style={{ paddingLeft: 256, paddingTop: 72, padding: '72px 24px 24px 280px', display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 24 }}>

        {/* Left Card: File Upload */}
        <section style={{ gridColumn: 'span 3', background: SURF_LOW, borderRadius: 12, border: `1px solid ${OUTLINE_V}0d`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          <div style={{ padding: '20px 20px 16px', borderBottom: `1px solid ${OUTLINE_V}1a` }}>
            <h3 style={{ fontWeight: 700, color: ON_SURF, margin: 0 }}>Wissensressourcen</h3>
            <p style={{ fontSize: 12, color: ON_SURF_V, margin: '4px 0 0' }}>Vektorquellen verwalten</p>
          </div>

          <div style={{ flex: 1, padding: 20, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Dropzone */}
            <div
              onDragOver={e => { e.preventDefault(); setDragging(true); }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              onClick={() => inputRef.current?.click()}
              style={{
                border: `2px dashed ${dragging ? PRIMARY : `${OUTLINE_V}4d`}`,
                borderRadius: 12, padding: '32px 16px', textAlign: 'center',
                background: dragging ? `${SURF}` : SURF,
                cursor: 'pointer', transition: 'all 0.2s',
              }}
            >
              <input ref={inputRef} type="file" accept=".pdf,.md,.txt" multiple style={{ display: 'none' }} onChange={e => e.target.files && handleFiles(e.target.files)} />
              <span className="material-symbols-outlined" style={{ fontSize: 36, color: dragging ? PRIMARY : OUTLINE_V, display: 'block', marginBottom: 12, transition: 'color 0.2s' }}>cloud_upload</span>
              <p style={{ fontSize: 12, fontWeight: 500, color: ON_SURF_V, marginBottom: 4 }}>PDF oder Ordner hierher ziehen</p>
              <p style={{ fontSize: 10, color: OUTLINE, fontStyle: 'italic' }}>Bis zu 200MB / Datei</p>
            </div>

            {/* File list */}
            {pipeline.slice(0, 8).map(f => (
              <div key={f.id} style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: 8,
                borderRadius: 8, background: `${SURF_HIGHEST}80`,
                transition: 'background 0.15s', cursor: 'default',
              }}>
                <span className="material-symbols-outlined" style={{ fontSize: 20, color: TYPE_COLOR[f.type] }}>
                  {f.type === 'DOCUMENT' ? 'picture_as_pdf' : f.type === 'IMAGE' ? 'image' : f.type === 'DATABASE' ? 'storage' : 'article'}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ fontSize: 12, fontWeight: 500, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{f.filename}</p>
                  <p style={{ fontSize: 10, color: ON_SURF_V, margin: 0 }}>
                    {f.size_mb.toFixed(1)} MB{f.chunks ? ` · ${f.chunks} Chunks` : ''}
                  </p>
                </div>
                <div style={{ flexShrink: 0 }}>{STATUS_ICON[f.status]}</div>
              </div>
            ))}
          </div>

          {/* Storage */}
          <div style={{ padding: 16, background: `${SURF_HIGHEST}4d`, borderTop: `1px solid ${OUTLINE_V}1a` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.1em' }}>SPEICHERLIMIT</span>
              <span style={{ fontSize: 10, color: PRIMARY }}>{storageUsed}% Belegt</span>
            </div>
            <div style={{ height: 4, background: `${OUTLINE_V}33`, borderRadius: 999, overflow: 'hidden' }}>
              <div style={{ height: '100%', background: PRIMARY, width: `${storageUsed}%`, borderRadius: 999 }} />
            </div>
          </div>
        </section>

        <div style={{ gridColumn: 'span 9', display: 'flex', flexDirection: 'column', gap: 24 }}>

          {/* Top Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24, minHeight: 380 }}>

            {/* Processing Pipeline Table */}
            <section style={{ background: SURF, borderRadius: 12, border: `1px solid ${OUTLINE_V}0d`, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
              <div style={{ padding: '20px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: `${SURF_HIGHEST}33` }}>
                <h3 style={{ fontWeight: 700, color: ON_SURF, margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span className="material-symbols-outlined" style={{ color: PRIMARY, fontVariationSettings: "'FILL' 1", fontSize: 20 }}>dataset</span>
                  Verarbeitungs-Pipeline
                </h3>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={() => {}} style={{ fontSize: 10, padding: '4px 12px', background: SURF_HIGH, borderRadius: 999, border: `1px solid ${OUTLINE_V}33`, color: ON_SURF_V, cursor: 'pointer' }}>Aktualisieren</button>
                  <button style={{ fontSize: 10, padding: '4px 12px', background: `${PRIMARY}1a`, borderRadius: 999, color: PRIMARY, border: 'none', cursor: 'pointer', fontWeight: 700 }}>Stapelverarbeitung</button>
                </div>
              </div>
              <div style={{ flex: 1, overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: `${SURF_LOW}80` }}>
                      {['DATEINAME', 'TYP', 'GRÖSSE', 'METHODE', 'STATUS'].map((col, i) => (
                        <th key={col} style={{ padding: '12px 24px', fontSize: 10, fontWeight: 900, color: OUTLINE, textTransform: 'uppercase', letterSpacing: '0.15em', textAlign: i >= 4 ? 'center' : i === 2 ? 'right' : 'left', whiteSpace: 'nowrap' }}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {pipeline.length === 0 ? (
                      <tr><td colSpan={5} style={{ padding: '32px 24px', textAlign: 'center', color: ON_SURF_V, fontSize: 13 }}>Noch keine Dateien verarbeitet. Datei hochladen oder Crawler starten.</td></tr>
                    ) : (
                      pipeline.map(f => (
                        <tr key={f.id} style={{ borderTop: `1px solid ${OUTLINE_V}1a`, transition: 'background 0.15s' }}>
                          <td style={{ padding: '16px 24px', fontSize: 12, fontWeight: 600 }}>{f.filename}</td>
                          <td style={{ padding: '16px 24px' }}>
                            <span style={{ padding: '2px 8px', borderRadius: 4, background: SURF_HIGHEST, fontSize: 10, color: TYPE_COLOR[f.type] }}>{f.type}</span>
                          </td>
                          <td style={{ padding: '16px 24px', fontSize: 12, textAlign: 'right', color: ON_SURF_V, fontVariantNumeric: 'tabular-nums' }}>{f.size_mb.toFixed(1)} MB</td>
                          <td style={{ padding: '16px 24px' }}>
                            <span style={{ fontSize: 10, fontWeight: 700, color: f.method === 'VLM Vision' ? SECONDARY : f.method === 'SQL Parser' ? TERTIARY : PRIMARY }}>{f.method}</span>
                          </td>
                          <td style={{ padding: '16px 24px', textAlign: 'center' }}>{STATUS_ICON[f.status]}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </section>

            {/* Neural Controller */}
            <section style={{ background: `${SURF_HIGHEST}66`, borderRadius: 12, padding: 24, border: `1px solid ${PRIMARY}1a`, display: 'flex', flexDirection: 'column' }}>
              <h3 style={{ fontSize: 11, fontWeight: 900, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: 24 }}>Neuronaler Controller</h3>

              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 16 }}>
                {/* LLM Active */}
                <div style={{ padding: 16, borderRadius: 12, background: `rgba(25,37,64,0.6)`, backdropFilter: 'blur(12px)', border: `1px solid ${PRIMARY}33`, position: 'relative', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ width: 40, height: 40, borderRadius: '50%', background: `${PRIMARY}1a`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span className="material-symbols-outlined" style={{ color: PRIMARY, fontVariationSettings: "'FILL' 1" }}>neurology</span>
                      </div>
                      <div>
                        <p style={{ fontSize: 12, fontWeight: 700, margin: 0 }}>LLM Aktiv</p>
                        <p style={{ fontSize: 10, color: ON_SURF_V, margin: 0 }}>llama-3.3-70b (Groq)</p>
                      </div>
                    </div>
                    <div style={{ display: 'flex', gap: 3, alignItems: 'flex-end' }}>
                      {[3, 5, 4].map((h, i) => (
                        <div key={i} style={{ width: 4, height: `${h * 4}px`, background: SECONDARY, borderRadius: 2, animation: `pulse ${0.8 + i * 0.2}s ease-in-out infinite` }} />
                      ))}
                    </div>
                  </div>
                </div>

                {/* VLM Idle */}
                <div style={{ padding: 16, borderRadius: 12, background: SURF_LOW, border: `1px solid ${OUTLINE_V}1a`, opacity: 0.6 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                      <div style={{ width: 40, height: 40, borderRadius: '50%', background: SURF_HIGHEST, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <span className="material-symbols-outlined" style={{ color: ON_SURF_V }}>visibility</span>
                      </div>
                      <div>
                        <p style={{ fontSize: 12, fontWeight: 700, color: ON_SURF_V, margin: 0 }}>VLM Leerlauf</p>
                        <p style={{ fontSize: 10, color: OUTLINE, margin: 0 }}>llava:13b (Ollama)</p>
                      </div>
                    </div>
                    <span className="material-symbols-outlined" style={{ color: OUTLINE_V }}>power_settings_new</span>
                  </div>
                </div>

                {/* Stats */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginTop: 'auto' }}>
                  <div style={{ padding: 12, background: SURF_LOW, borderRadius: 8, border: `1px solid ${OUTLINE_V}1a` }}>
                    <p style={{ fontSize: 9, fontWeight: 700, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>LATENZ</p>
                    <p style={{ fontSize: 20, fontWeight: 900, color: SECONDARY, margin: 0 }}>214<span style={{ fontSize: 10, fontWeight: 400, marginLeft: 4 }}>ms</span></p>
                  </div>
                  <div style={{ padding: 12, background: SURF_LOW, borderRadius: 8, border: `1px solid ${OUTLINE_V}1a` }}>
                    <p style={{ fontSize: 9, fontWeight: 700, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 4 }}>TOKEN/SEK</p>
                    <p style={{ fontSize: 20, fontWeight: 900, color: PRIMARY, margin: 0 }}>82<span style={{ fontSize: 10, fontWeight: 400, marginLeft: 4 }}>tk</span></p>
                  </div>
                </div>
              </div>
            </section>
          </div>

          {/* Crawler Section */}
          <section style={{ background: SURF_LOW, borderRadius: 12, border: `1px solid ${OUTLINE_V}1a`, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '16px 24px', borderBottom: `1px solid ${OUTLINE_V}1a`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: SURF_LOW }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span className="material-symbols-outlined" style={{ color: TERTIARY }}>language</span>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: ON_SURF, margin: 0 }}>Universelle Crawler-Engine</h3>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 24 }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: ON_SURF_V, textTransform: 'uppercase' }}>CRAWLER-TIEFE</span>
                <div style={{ display: 'flex', background: SURF_HIGHEST, padding: 2, borderRadius: 999, border: `1px solid ${OUTLINE_V}33`, gap: 2 }}>
                  {([1, 2, 'MAX'] as const).map(d => (
                    <button key={d} onClick={() => setCrawlDepth(d)} style={{
                      padding: '4px 12px', fontSize: 10, borderRadius: 999, border: 'none', cursor: 'pointer',
                      background: crawlDepth === d ? PRIMARY : 'transparent',
                      color: crawlDepth === d ? '#002f5c' : ON_SURF_V,
                      fontWeight: crawlDepth === d ? 700 : 400,
                      transition: 'all 0.15s',
                    }}>{d}</button>
                  ))}
                </div>
              </div>
            </div>

            <div style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 16 }}>
              <div>
                <label style={{ display: 'block', fontSize: 10, fontWeight: 900, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.2em', marginBottom: 8 }}>Ziel-URL</label>
                <input
                  value={crawlUrl}
                  onChange={e => setCrawlUrl(e.target.value)}
                  placeholder="https://docs.example.com/api/v1"
                  style={{
                    width: '100%', background: SURF_HIGHEST, border: 'none', outline: 'none',
                    fontSize: 12, borderRadius: 12, padding: '12px 16px',
                    color: ON_SURF, fontFamily: "'Inter', sans-serif",
                    boxSizing: 'border-box',
                  }}
                />
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
                <button
                  onClick={startCrawler}
                  disabled={crawling || !crawlUrl.trim()}
                  style={{
                    marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8,
                    background: `linear-gradient(135deg, ${TERTIARY}, ${TERTIARY}bb)`,
                    color: '#000e6e', fontWeight: 900, padding: '12px 24px',
                    borderRadius: 12, border: 'none', cursor: crawling || !crawlUrl.trim() ? 'not-allowed' : 'pointer',
                    fontSize: 12, opacity: crawling || !crawlUrl.trim() ? 0.6 : 1,
                    transition: 'all 0.15s',
                  }}
                >
                  <span className="material-symbols-outlined" style={{ fontSize: 20 }}>{crawling ? 'hourglass_empty' : 'play_arrow'}</span>
                  {crawling ? 'CRAWLT…' : 'CRAWLER STARTEN'}
                </button>
              </div>
            </div>

            {/* Logs */}
            <div style={{ flex: 1, background: `${BG}80`, borderTop: `1px solid ${OUTLINE_V}1a`, display: 'flex', flexDirection: 'column', minHeight: 160 }}>
              <div style={{ padding: '8px 16px', borderBottom: `1px solid ${OUTLINE_V}08`, display: 'flex', justifyContent: 'space-between', background: `${SURF_LOW}4d` }}>
                <span style={{ fontSize: 9, fontWeight: 900, color: ON_SURF_V, textTransform: 'uppercase', letterSpacing: '0.1em' }}>CHROMA DB AUFNAHME-PROTOKOLLE</span>
                <span style={{ fontSize: 9, color: SECONDARY, fontVariantNumeric: 'tabular-nums' }}>
                  {logs.length > 0 ? 'LIVE' : 'BEREIT'}
                </span>
              </div>
              <div style={{ flex: 1, padding: 16, fontFamily: "'Fira Code', monospace", fontSize: 10, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 4, maxHeight: 180 }}>
                {logs.length === 0 ? (
                  <span style={{ color: ON_SURF_V, opacity: 0.5 }}>Warte auf Aktivität…</span>
                ) : (
                  logs.map((log, i) => (
                    <p key={i} style={{ margin: 0 }}>
                      <span style={{ color: OUTLINE }}>[{log.ts}]</span>{' '}
                      <span style={{ color: LOG_COLOR[log.level] }}>{log.level}</span>{' '}
                      <span style={{ color: ON_SURF_V }}>{log.message}</span>
                    </p>
                  ))
                )}
              </div>
            </div>
          </section>

        </div>
      </main>

      {/* Ambient glow */}
      <div style={{ position: 'fixed', top: '25%', right: 0, width: 384, height: 384, background: `${PRIMARY}0d`, filter: 'blur(120px)', pointerEvents: 'none', zIndex: -1 }} />
      <div style={{ position: 'fixed', bottom: 0, left: '25%', width: 500, height: 300, background: `${TERTIARY}0d`, filter: 'blur(150px)', pointerEvents: 'none', zIndex: -1 }} />
    </div>
  );
}
