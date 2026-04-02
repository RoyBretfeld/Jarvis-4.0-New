/**
 * JARVIS 4.0 – Chat API Route
 * AWP-108: RAG-Kontext vor dem LLM-Call.
 * AWP-116: Quellen-Karten mit Relevanz-Score (X-RAG-Context JSON).
 * AWP-117: Nummerierte Zitate [1], [2] im System-Prompt.
 * AWP-118: Fehler-Keyword-Erkennung → Error-DB-Boost.
 */
import Groq from 'groq-sdk';
import { NextRequest } from 'next/server';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const MODEL   = process.env.GROQ_MODEL        ?? 'llama-3.3-70b-versatile';
const BACKEND = process.env.JARVIS_BACKEND_URL ?? 'http://127.0.0.1:8000';

const BASE_SYSTEM_PROMPT = `Du bist JARVIS 4.0, ein lokaler KI-Assistent für Softwareentwicklung.
Du hilfst dem Entwickler mit Code, Architektur, Debugging und Projektplanung.
Antworte präzise, technisch korrekt und auf Deutsch wenn der User Deutsch schreibt.`;

// AWP-116: Typdefinition für Source-Karten
export interface SourceInfo {
  id: number;
  file: string;    // Anzeigename (z.B. "Projektplan.pdf")
  source: string;  // Vollständige Source-ID (z.B. "upload::Projektplan.pdf")
  score: number;   // Relevanz 0.0–1.0
}

// AWP-118: Error-Pattern für automatischen DB-Boost
const ERROR_PATTERN = /fehler|error|bug|exception|crash|traceback|fix|reparier|kaputt|problem|issue|stacktrace/i;

// ── AWP-108/116/117/118: RAG-Suche ────────────────────────────────────────────
async function fetchRagContext(query: string): Promise<{
  contextBlock: string;
  sources: SourceInfo[];
}> {
  // AWP-118: Fehler-Queries bekommen mehr Ergebnisse → höhere Trefferwahrscheinlichkeit für 03_ERROR_DB
  const isErrorQuery = ERROR_PATTERN.test(query);
  const top_k = isErrorQuery ? 6 : 4;

  try {
    const res = await fetch(`${BACKEND}/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k, mode: 'hybrid', score_threshold: 0.30 }),
      signal: AbortSignal.timeout(4000),
    });
    if (!res.ok) return { contextBlock: '', sources: [] };

    const data = await res.json() as {
      results: Array<{ text: string; score: number; metadata: Record<string, string> }>;
    };

    if (!data.results?.length) return { contextBlock: '', sources: [] };

    const sources: SourceInfo[] = [];

    // AWP-117: Nummerierte Blöcke für LLM-Zitate [1], [2], ...
    const contextBlock = data.results
      .map((r, i) => {
        const rawSource = r.metadata?.source ?? r.metadata?.filename ?? '';
        const file = (r.metadata?.filename ?? rawSource)
          .split('/').pop()?.split('\\').pop() ?? 'Unbekannt';
        const scoreLabel = (r.score * 100).toFixed(0);

        // Nur Upload-Dokumente als attributierbare Quellen tracken
        if (rawSource.includes('upload::')) {
          sources.push({
            id: i + 1,
            file,
            source: rawSource,
            score: Math.round(r.score * 100) / 100,
          });
        }

        return `[${i + 1}] ${file} | Relevanz: ${scoreLabel}%\n${r.text.slice(0, 800)}`;
      })
      .join('\n\n---\n\n');

    // Deduplizieren nach file-Name (gleiche Datei, verschiedene Chunks)
    const seen = new Set<string>();
    const uniqueSources = sources.filter((s) => {
      if (seen.has(s.file)) return false;
      seen.add(s.file);
      return true;
    });

    return { contextBlock, sources: uniqueSources };
  } catch {
    return { contextBlock: '', sources: [] };
  }
}

export async function POST(req: NextRequest) {
  const { messages, activeFile, activeContent } = await req.json() as {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    activeFile?: string;
    activeContent?: string;
  };

  const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user')?.content ?? '';

  // RAG parallel zur Prompt-Vorbereitung
  const { contextBlock: ragContext, sources } = await fetchRagContext(lastUserMsg);

  let systemPrompt = BASE_SYSTEM_PROMPT;

  if (activeFile && activeContent) {
    systemPrompt += `\n\nAktuell geöffnete Datei: ${activeFile}\n\`\`\`\n${activeContent}\n\`\`\``;
  } else if (activeFile) {
    systemPrompt += `\n\nAktuell geöffnete Datei: ${activeFile}`;
  }

  // AWP-117: Zitate aktivieren wenn RAG-Kontext vorhanden
  if (ragContext) {
    systemPrompt += `\n\n## Dokument-Gedächtnis (Zitiere mit [1], [2], ...):\n${ragContext}\n\nNutze diese Quellen wenn sie relevant sind. Referenziere sie als [1], [2] etc. Halluziniere NICHT über Inhalte aus Quellen.`;
  }

  const stream = await groq.chat.completions.create({
    model: MODEL,
    messages: [{ role: 'system', content: systemPrompt }, ...messages],
    stream: true,
    temperature: 0.7,
    max_tokens: 4096,
  });

  const encoder = new TextEncoder();
  const readable = new ReadableStream({
    async start(controller) {
      for await (const chunk of stream) {
        const delta = chunk.choices[0]?.delta?.content ?? '';
        if (delta) controller.enqueue(encoder.encode(delta));
      }
      controller.close();
    },
  });

  // AWP-116: Quellen als JSON im Header (Score + Dateipfad)
  const headers: Record<string, string> = {
    'Content-Type': 'text/plain; charset=utf-8',
  };
  if (sources.length > 0) {
    // JSON in Header: max ~1KB bei 4 Quellen, sicher unter 8KB-Limit
    headers['X-RAG-Context'] = JSON.stringify(sources);
    // Backwards-compat für alten ChatPanel-Code
    headers['X-RAG-Sources'] = sources.map((s) => s.file).join(',');
  }

  return new Response(readable, { headers });
}
