/**
 * JARVIS 4.0 – Upload Panel
 * Drag & Drop Upload von PDFs (bis 200MB), MD und TXT ins RAG.
 * PDFs werden serverseitig mit VLM (llava) gescannt.
 */
'use client';

import React, { useCallback, useRef, useState } from 'react';

const BACKEND = '/api';
const ALLOWED = ['.pdf', '.md', '.txt'];
const MAX_MB = 200;

interface UploadResult {
  filename: string;
  status: string;
  chunks?: number;
  size_mb?: number;
  error?: string;
}

export function UploadPanel() {
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<UploadResult[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadFile = useCallback(async (file: File) => {
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!ALLOWED.includes(ext)) {
      setResults((r) => [{
        filename: file.name,
        status: 'error',
        error: `Nicht erlaubt: ${ext}. Erlaubt: ${ALLOWED.join(', ')}`,
      }, ...r]);
      return;
    }
    if (file.size > MAX_MB * 1024 * 1024) {
      setResults((r) => [{
        filename: file.name,
        status: 'error',
        error: `Zu groß: ${(file.size / 1024 / 1024).toFixed(1)}MB (max ${MAX_MB}MB)`,
      }, ...r]);
      return;
    }

    setUploading(true);
    setProgress(0);

    const form = new FormData();
    form.append('file', file);

    return new Promise<void>((resolve) => {
      const xhr = new XMLHttpRequest();
      xhr.open('POST', `${BACKEND}/upload`);

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) setProgress(Math.round((e.loaded / e.total) * 100));
      };

      xhr.onload = () => {
        setUploading(false);
        setProgress(0);
        try {
          const data = JSON.parse(xhr.responseText);
          if (xhr.status === 200) {
            setResults((r) => [{
              filename: file.name,
              status: data.status,
              chunks: data.chunks,
              size_mb: data.size_mb,
            }, ...r]);
          } else {
            setResults((r) => [{
              filename: file.name,
              status: 'error',
              error: data.detail ?? `HTTP ${xhr.status}`,
            }, ...r]);
          }
        } catch {
          setResults((r) => [{
            filename: file.name, status: 'error', error: 'Parse error',
          }, ...r]);
        }
        resolve();
      };

      xhr.onerror = () => {
        setUploading(false);
        setProgress(0);
        setResults((r) => [{
          filename: file.name, status: 'error', error: 'Netzwerkfehler',
        }, ...r]);
        resolve();
      };

      xhr.send(form);
    });
  }, []);

  const handleFiles = useCallback(async (files: FileList | File[]) => {
    const arr = Array.from(files);
    for (const f of arr) await uploadFile(f);
  }, [uploadFile]);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    if (e.dataTransfer.files.length > 0) handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {/* Drop Zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !uploading && inputRef.current?.click()}
        style={{
          margin: '8px',
          padding: '14px 8px',
          borderRadius: 6,
          border: `2px dashed ${dragging ? 'var(--aura-primary)' : 'var(--color-border)'}`,
          background: dragging ? 'var(--color-bg-elevated)' : 'transparent',
          cursor: uploading ? 'not-allowed' : 'pointer',
          textAlign: 'center',
          transition: 'border-color 0.2s, background 0.2s',
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.md,.txt"
          multiple
          style={{ display: 'none' }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
        />
        <div style={{ fontSize: 20, marginBottom: 4 }}>
          {uploading ? '⏳' : '📂'}
        </div>
        <div style={{ fontSize: 11, color: 'var(--color-text-muted)', lineHeight: 1.6 }}>
          {uploading
            ? `Wird verarbeitet… ${progress}%`
            : 'PDF / MD / TXT hierher ziehen'}
          <br />
          <span style={{ fontSize: 10 }}>max {MAX_MB}MB · PDFs werden mit VLM gescannt</span>
        </div>

        {/* Progress Bar */}
        {uploading && (
          <div style={{
            marginTop: 8, height: 3, borderRadius: 2,
            background: 'var(--color-border)', overflow: 'hidden',
          }}>
            <div style={{
              height: '100%', width: `${progress}%`,
              background: 'var(--aura-primary)',
              transition: 'width 0.3s ease',
            }} />
          </div>
        )}
      </div>

      {/* Results */}
      {results.length > 0 && (
        <div style={{ padding: '0 8px 8px' }}>
          {results.slice(0, 8).map((r, i) => (
            <div key={i} style={{
              fontSize: 11, padding: '4px 6px', marginBottom: 3,
              borderRadius: 4,
              background: r.status === 'error'
                ? 'rgba(255,60,60,0.08)'
                : 'var(--color-bg-elevated)',
              border: `1px solid ${r.status === 'error'
                ? 'var(--aura-alert-primary)'
                : 'var(--color-border)'}`,
            }}>
              <div style={{
                fontFamily: 'var(--font-mono)',
                color: r.status === 'error'
                  ? 'var(--aura-alert-primary)'
                  : 'var(--color-text-primary)',
                fontWeight: 600,
                overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
              }}>
                {r.filename}
              </div>
              {r.status === 'error'
                ? <div style={{ color: 'var(--aura-alert-primary)', marginTop: 2 }}>{r.error}</div>
                : (
                  <div style={{ color: 'var(--color-text-muted)', marginTop: 2 }}>
                    {r.chunks} Chunks · {r.size_mb?.toFixed(1)}MB · eingebettet ✓
                  </div>
                )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
