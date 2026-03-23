# 🎨 Sovereign Glass Design System v1.0

**Subheading:** Dark-Mode UI mit leuchtenden Akzentfarben für maximale Transparenz und Kontrolle

---

## 1️⃣ Farbpalette – Functional Glow

Ein dunkelbasiertes System, das Bedeutung durch Farbe trägt (nicht nur Ästhetik):

| Farbe | Hex | Funktion | Gesetz |
|-------|-----|----------|--------|
| **Deep Obsidian** | `#0A0E14` | Hintergrund (Fokus pur) | - |
| **Cyber Cyan** | `#00F2FF` | Haupt-Orchestrator, aktive Denkprozesse | §1 Transparenz |
| **Sentinel Blue** | `#1A73E8` | Sicherheits-Layer, verifizierte Verbindungen | §1 Transparenz |
| **Action Amber** | `#FFB000` | Bestätigungen, Menschliche Hoheit | §4 Menschliche Hoheit |
| **Trace Grey** | `#4A5568` | Logs, Metadaten, Details | §3 Progressive Offenlegung |

---

## 2️⃣ Layout-Raster – The 3-Column Grid

Ein 3-Säulen-System für Informationsdichte ohne Clutter:

```
┌─────────────────────────────────────────────────────────────┐
│ LINKE SIDEBAR           │ ZENTRALE SÄULE    │ RECHTE SIDEBAR │
├─────────────────────────┼───────────────────┼────────────────┤
│ Agent-Orchestration     │ Chat-Stream       │ Context-Pane   │
│ • Wer arbeitet?         │ • Konversation    │ • Logs         │
│ • Coding-Agent?         │ • Ergebnisse      │ • MCP-Metadaten│
│ • RAG-Agent?            │ • Streaming-Text  │ • Vektor-Quellen
│                         │                   │ • Checkpoints  │
│ (§1 Transparenz)        │ (§1 Fokus)        │ (§3 Offenlegung)
└─────────────────────────┴───────────────────┴────────────────┘
```

### Linke Sidebar – Agent-Orchestration
**Zweck:** Zeige aktive Agenten und deren State
- Welcher Agent läuft gerade? (farbcodiert)
- Denkprozess-Meter (Pulsing-Animation)
- Abort-Button immer sichtbar (§2 Revidierbarkeit)

### Zentrale Säule – Chat-Stream
**Zweck:** Die Konversation und finalen Lösungen
- User-Input oben
- Agent-Antwort (Streaming-Text)
- Code-Blöcke mit Syntax-Highlight
- Checkpoint-Marker bei kritischen Aktionen

### Rechte Sidebar – Context-Pane
**Zweck:** Deep-Dive ohne Main-Stream zu unterbrechen (§3)
- Live-Logs (färbbar nach Log-Level)
- MCP-Metadaten (welche Tools geladen?)
- RAG-Quellen (welche Dokumente flossen ein?)
- Checkpoint-Cards (Undo-Buttons für Gesetz §2)

---

## 3️⃣ UI-Elemente & Effekte

### Glassmorphism
Alle Panel-Grenzen nutzen Transparenz + Blur:
```css
backdrop-filter: blur(20px);
background: rgba(10, 14, 20, 0.7);
border: 1px solid rgba(0, 242, 255, 0.2);
```

**Effekt:** Tiefe-Illusion. Dahinter liegende Inhalte sind sichtbar, aber der Panel hat seinen eigenen Fokus.

### Streaming-Indikatoren
Nicht nur "KI schreibt...", sondern:
- **Pulsing Line**: Dünne Linie pulsiert von links nach rechts (Cyber Cyan) während der LLM schreibt
- **RAG-Animation**: Wenn RAG einen Hit findet, "fliegt" ein Vektor-Symbol von rechts in den Context-Pane
- **Checkpoint-Flash**: Kurzes Amber-Flash wenn kritische Aktion ausgeführt wurde

### Checkpoint-Cards
Jede kritische Aktion (Datei geschrieben, API aufgerufen, Commit erstellt) erscheint als:
```
┌─────────────────────────────┐
│ ✓ File written: app.py      │
│ [Show Diff] [Undo]          │
└─────────────────────────────┘
```
- Icon zeigt Action-Typ (Datei, API, Git, etc.)
- "Show Diff" für §2 Revidierbarkeit
- "Undo" für sofortige Korrektur

---

## 4️⃣ Typografie

| Einsatz | Font | Gewicht | Größe | Grund |
|---------|------|---------|-------|-------|
| Code-Blöcke | JetBrains Mono | Regular | 12-14px | Technischer Charakter, Monospace für Alignment |
| Metadaten/Logs | JetBrains Mono | Regular | 11px | Dichte, Lesbarkeit bei Scrolling |
| Primary Text | Inter | Regular | 14px | Klarheit, Zugänglichkeit |
| Headings | Inter | SemiBold | 18-24px | Hierarchie, Scanbarkeit |
| Labels | Inter | Medium | 12px | UI-Konsistenz |

---

## 5️⃣ Warum dieses Design?

### Problem: Black-Box Effect
Bisherige KI-Tools verstecken den Denkprozess. Du siehst nur Input → Output, aber nicht warum.

### Lösung: Animated Transparency
- **RAG-Agent findet Dokument** → Symbol "fliegt" in Context-Pane
- **LLM kommt zu Entscheidung** → Denkprozess wird im Orchestrator visualisiert
- **Kritische Aktion passiert** → Checkpoint-Card mit Undo-Option
- **User möchte Details** → Ein Klick in die rechte Sidebar, alles wird forensisch sichtbar

### Design-Principles
1. **§1 Transparenz**: Jede Aktion ist sichtbar (Farben + Animationen)
2. **§2 Revidierbarkeit**: Undo-Buttons überall (Checkpoint-Cards)
3. **§3 Progressive Offenlegung**: Main-Stream sauber, Details rechts
4. **§4 Menschliche Hoheit**: Action Amber für "Bestätigung nötig" Flows

---

## 6️⃣ Implementierungs-Roadmap

### Phase 1: Core Layout (MVP)
- [ ] 3-Säulen-Grid (CSS Grid oder Flexbox)
- [ ] Farbpalette in CSS-Variablen
- [ ] Glassmorphism-Panels

### Phase 2: Streaming & Animation
- [ ] Pulsing-Line beim Streaming
- [ ] RAG-Icon Flying Animation
- [ ] Checkpoint-Flash-Effect

### Phase 3: Checkpoint-System
- [ ] Checkpoint-Card Rendering
- [ ] Undo-Mechanik
- [ ] Diff-Viewer Integration

### Phase 4: Dark-Mode Refinement
- [ ] Contrast-Prüfung (WCAG AA)
- [ ] Accessibility-Tests
- [ ] Light-Mode Alternative (wenn nötig)

---

## 7️⃣ Code-Snippet: CSS-Variablen

```css
:root {
  --color-bg-deep: #0A0E14;
  --color-accent-cyan: #00F2FF;
  --color-accent-blue: #1A73E8;
  --color-accent-amber: #FFB000;
  --color-text-grey: #4A5568;

  --glass-blur: blur(20px);
  --glass-opacity: rgba(10, 14, 20, 0.7);
  --glass-border: 1px solid rgba(0, 242, 255, 0.2);

  --font-mono: 'JetBrains Mono', monospace;
  --font-sans: 'Inter', sans-serif;
}

.glass-panel {
  backdrop-filter: var(--glass-blur);
  background: var(--glass-opacity);
  border: var(--glass-border);
  border-radius: 8px;
  padding: 16px;
}
```

---

## Version & Status

- **Version:** 1.0
- **Status:** Design Specification (Ready for Implementation)
- **Last Updated:** 2026-03-18
- **Design Authority:** Sovereign Glass System (RB-Protokoll v3.1+)

---

## Lizenz

Closed Source – Antigravity Project
