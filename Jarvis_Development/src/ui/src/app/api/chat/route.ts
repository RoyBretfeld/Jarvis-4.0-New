/**
 * JARVIS 4.0 – Chat API Route
 * Streamt Antworten von Groq (llama-3.3-70b-versatile) ans Frontend.
 */
import Groq from 'groq-sdk';
import { NextRequest } from 'next/server';

const groq = new Groq({ apiKey: process.env.GROQ_API_KEY });
const MODEL = process.env.GROQ_MODEL ?? 'llama-3.3-70b-versatile';

const BASE_SYSTEM_PROMPT = `Du bist JARVIS 4.0, ein lokaler KI-Assistent für Softwareentwicklung.
Du hilfst dem Entwickler mit Code, Architektur, Debugging und Projektplanung.
Antworte präzise, technisch korrekt und auf Deutsch wenn der User Deutsch schreibt.`;

export async function POST(req: NextRequest) {
  const { messages, activeFile, activeContent } = await req.json() as {
    messages: Array<{ role: 'user' | 'assistant'; content: string }>;
    activeFile?: string;
    activeContent?: string;
  };

  let systemPrompt = BASE_SYSTEM_PROMPT;
  if (activeFile && activeContent) {
    systemPrompt += `\n\nAktuell geöffnete Datei: ${activeFile}\n\`\`\`\n${activeContent}\n\`\`\``;
  } else if (activeFile) {
    systemPrompt += `\n\nAktuell geöffnete Datei: ${activeFile}`;
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

  return new Response(readable, {
    headers: { 'Content-Type': 'text/plain; charset=utf-8' },
  });
}
