/**
 * AWP-084 – Thought Overlay
 * Live-Stream des reasoning.log via WebSocket /ws/reasoning
 * Zeigt die 3-Satz-Strategie jedes Agenten als Overlay im Dashboard.
 *
 * Erscheint als semi-transparentes Panel über dem Editor,
 * verschwindet 8s nach dem letzten Eintrag.
 */

"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";

interface ReasoningEntry {
  id: number;
  timestamp: string;
  agent: string;
  task: string;
  sentences: string[];
  raw: string;
}

const AGENT_COLORS: Record<string, string> = {
  coder:     "var(--aura-processing)",
  tester:    "var(--aura-success)",
  security:  "var(--aura-alert)",
  architect: "#FFD700",
  system:    "var(--aura-idle)",
};

const FADE_DELAY_MS = 8000;

function parseReasoningLine(raw: string): ReasoningEntry | null {
  // Format: [ISO] @agent | task=...
  //   1. sentence
  //   2. sentence
  //   3. sentence
  const lines = raw.trim().split("\n");
  if (lines.length < 2) return null;

  const header = lines[0];
  const tsMatch = header.match(/\[(.+?)\]/);
  const agentMatch = header.match(/@(\w+)/);
  const taskMatch = header.match(/task=(.+)/);

  const sentences = lines
    .slice(1)
    .map((l) => l.replace(/^\s+\d+\.\s+/, "").trim())
    .filter(Boolean);

  return {
    id: Date.now() + Math.random(),
    timestamp: tsMatch?.[1] ?? new Date().toISOString(),
    agent: agentMatch?.[1] ?? "system",
    task: taskMatch?.[1] ?? "",
    sentences,
    raw,
  };
}

export default function ThoughtOverlay() {
  const [entries, setEntries] = useState<ReasoningEntry[]>([]);
  const [visible, setVisible] = useState(false);
  const fadeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const bufferRef = useRef("");

  const { lines } = useWebSocket({ url: `ws://${typeof window !== 'undefined' ? window.location.hostname : 'localhost'}:8000/ws/reasoning`, maxLines: 100 });
  const messages = lines.map((l) => l.message);

  // Parse incoming lines into reasoning entries
  useEffect(() => {
    if (!messages.length) return;
    const latest = messages[messages.length - 1];

    // Buffer multi-line entries (delimited by blank line or new header)
    if (latest.startsWith("[") && bufferRef.current) {
      const entry = parseReasoningLine(bufferRef.current);
      if (entry) {
        setEntries((prev) => [...prev.slice(-19), entry]);
        setVisible(true);
      }
      bufferRef.current = latest;
    } else if (latest.startsWith("[")) {
      bufferRef.current = latest;
    } else if (bufferRef.current) {
      bufferRef.current += "\n" + latest;
      // Flush if we have 3+ sentence lines
      const sentenceCount = (bufferRef.current.match(/^\s+\d+\./gm) || []).length;
      if (sentenceCount >= 3) {
        const entry = parseReasoningLine(bufferRef.current);
        if (entry) {
          setEntries((prev) => [...prev.slice(-19), entry]);
          setVisible(true);
          bufferRef.current = "";
        }
      }
    }

    // Reset fade timer
    if (fadeTimer.current) clearTimeout(fadeTimer.current);
    fadeTimer.current = setTimeout(() => setVisible(false), FADE_DELAY_MS);
  }, [messages]);

  if (!visible || entries.length === 0) return null;

  const latest = entries[entries.length - 1];
  const color = AGENT_COLORS[latest.agent] ?? AGENT_COLORS.system;

  return (
    <div
      style={{
        position: "fixed",
        bottom: "80px",
        right: "16px",
        width: "360px",
        background: "rgba(10,10,20,0.92)",
        border: `1px solid ${color}`,
        borderRadius: "8px",
        padding: "12px 16px",
        backdropFilter: "blur(8px)",
        zIndex: 1000,
        fontFamily: "var(--font-mono, monospace)",
        fontSize: "12px",
        color: "var(--color-text, #e0e0e0)",
        boxShadow: `0 0 20px ${color}44`,
        animation: "fadeInUp 0.3s ease",
        maxHeight: "200px",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
        <span style={{ color, fontWeight: 700, fontSize: "11px", textTransform: "uppercase" }}>
          🧠 @{latest.agent} — Reasoning
        </span>
        <span style={{ color: "#666", fontSize: "10px" }}>
          {new Date(latest.timestamp).toLocaleTimeString()}
        </span>
      </div>

      {/* Task */}
      {latest.task && (
        <div style={{ color: "#888", marginBottom: "6px", fontSize: "11px" }}>
          Task: <em>{latest.task.slice(0, 60)}</em>
        </div>
      )}

      {/* 3-sentence strategy */}
      <ol style={{ margin: 0, paddingLeft: "20px", lineHeight: 1.6 }}>
        {latest.sentences.map((s, i) => (
          <li key={i} style={{ color: i === 2 ? "#aaa" : "#e0e0e0", marginBottom: "2px" }}>
            {s}
          </li>
        ))}
      </ol>

      {/* Entry count badge */}
      {entries.length > 1 && (
        <div style={{ marginTop: "8px", color: "#555", fontSize: "10px", textAlign: "right" }}>
          +{entries.length - 1} weitere im Log
        </div>
      )}

      <style>{`
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(12px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  );
}
