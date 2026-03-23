# 🎨 ARCHITEKT_THEME.md v1.0

**Subtitel:** Technische Spezifikation für visuelle Identität & UX-Implementierung

**Zielgruppe:** Jede KI-Agent (Claude, Gemini, Copilot, lokale Modelle) – unabhängig von Plattform

---

## 1️⃣ UX-FUNDAMENT (RB-PROTOKOLL)

Jede UI-Komponente muss folgende 4 Gesetze **technisch implementieren**:

### §1 Glass-Box: Transparenz durch Animation
**Technische Anforderung:** Rechenprozesse (z.B. Vektorsuche, Tokenizing) müssen sichtbar sein.

- **Vektorsuche**: Während das RAG-System ein Archiv durchsucht, pulst ein Glow an der `surface-glass`
- **LLM-Thinking**: Wenn der Orchestrator "denkt", zeigt ein gepulstes Icon die Latenz live
- **MCP-Calls**: Externe Tool-Aufrufe werden als Log-Stream im Forensic-Panel gezeichnet

**Code-Beispiel:**
```css
.vector-pulse {
  animation: glow 1.5s ease-in-out infinite;
  border: 2px solid var(--brand-orchestrator);
}

@keyframes glow {
  0%, 100% { box-shadow: 0 0 5px var(--brand-orchestrator); }
  50% { box-shadow: 0 0 20px var(--brand-orchestrator); }
}
```

### §2 Undo-First: Revidierbarkeit ist Default
**Technische Anforderung:** Jede kritische Aktion erzeugt einen "Checkpoint".

- **Checkpoint-Cards**: Dateiänderung → sofort eine Karte mit `[Show Diff] [Undo]`
- **Archive statt Delete**: Gelöschte Inhalte werden in `.archive/` verschoben (§2 Revidierbarkeit)
- **Commit-Safe**: Jede Code-Aktion ist mit einer Git-Commit-Message ausgestattet (für Rollback)

**Card-Format:**
```
┌─────────────────────────────────┐
│ ✓ File: src/app.py (modified)   │
│ [Show Diff]  [Undo]  [Archive]  │
└─────────────────────────────────┘
```

### §3 Progressive Disclosure: Clean Standard View
**Technische Anforderung:** Hauptview zeigt nur essenzielle Info. Details sind ausklappbar.

- **Standard-View**: User sieht Chat + aktuelle Antwort. Fertig.
- **Details-Panel (Rechts)**: Logs, Token-Count, Latenz, RAG-Quellen, MCP-Calls
- **Expandable Sections**: "Show Logs", "Show Metadata", "Show Sources"

**Layout:**
```
┌─────────────────────────────────────────────┐
│ CHAT (sauber) │ ⓘ DETAILS (einklappbar)     │
│               │ ▸ Logs                      │
│ KI: Antwort   │ ▸ Metadata                  │
│               │ ▸ RAG-Sources               │
│               │ ▸ Checkpoints               │
└─────────────────────────────────────────────┘
```

### §4 Menschliche Hoheit: Kritische Bestätigung
**Technische Anforderung:** System-verändernde Befehle benötigen einen physischen Button.

- **Action Amber**: Alle `delete`, `reset`, `deploy` Befehle sind Amber-farbig
- **Confirmation Modal**: Vor Ausführung wird ein Dialog mit klarem Text gezeigt
- **Audit Trail**: Jede Bestätigung wird geloggt (für forensische Nachverfolgung)

**Button-Standard:**
```html
<button class="action-confirm" style="background: var(--status-action)">
  ⚠️ DELETE (This cannot be undone) [CONFIRM]
</button>
```

---

## 2️⃣ VISUELLE IDENTITÄT (DESIGN TOKENS)

### Farbpalette – Semantisches Dark-Theme

| Token | Hex | RGB | Einsatzbereich | Semantik |
|-------|-----|-----|---|---|
| `surface-ground` | `#0A0E14` | 10, 14, 20 | Haupt-Hintergrund | Fokus, Ruhe |
| `surface-glass` | `rgba(20,26,35,0.7)` | mit Alpha | Panel-Hintergrund + Blur | Tiefe, Transparenz |
| `brand-orchestrator` | `#00F2FF` | 0, 242, 255 | Primär-Agent, pulsierend | Aktiv, Energisch |
| `brand-sentinel` | `#1A73E8` | 26, 115, 232 | Sicherheit, Validierung | Vertrauenswürdig |
| `status-action` | `#FFB000` | 255, 176, 0 | Bestätigungs-Button | Aufmerksamkeit, Hoheit |
| `status-trace` | `#4A5568` | 74, 85, 104 | Logs, Hintergrund | Neutral, Detail |
| `text-primary` | `#E2E8F0` | 226, 232, 240 | Haupttext | Lesbarkeit |
| `text-secondary` | `#A0AEC0` | 160, 174, 192 | Sekundär-Info | Hierarchie |

### Typografie – Semantische Wahl

| Kontext | Font | Größe | Gewicht | Grund |
|---------|------|-------|---------|-------|
| Buttons, Labels | Inter | 12px | Medium | Klarheit, schnelle Scannbarkeit |
| Überschriften | Inter | 18-24px | SemiBold | Hierarchie, visueller Anchor |
| Chat-Text | Inter | 14px | Regular | Lesbarkeit, Zugänglichkeit |
| Code-Blöcke | JetBrains Mono | 12px | Regular | Monospace für semantische Ausrichtung |
| Logs, Metadaten | JetBrains Mono | 11px | Regular | Dichte, Alignment in Listen |

**Grund für die Split:**
- **Inter**: Für Kommunikation (KI ↔ Mensch)
- **JetBrains Mono**: Für Maschinen-Semantik (Code, Logs, Token-Count)

---

## 3️⃣ LAYOUT-ARCHITEKTUR (3-PILLAR-SYSTEM)

```
┌────────────────────────────────────────────────────────────┐
│  LEFT PANEL            CENTER CHAT          RIGHT FORENSICS │
│  (Agent-Stack)         (Collaboration)       (Machine-Room) │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  • Coding-Agent  │  User: Was ist...     │  Logs:          │
│    ⚫ Working     │                       │  [15:23:45.123] │
│                  │  KI: [Thinking...]    │  RAG Hit found  │
│  • RAG-Agent     │
│    ⚫ Idle        │  [SOURCE-CARD: doc.md]│  Sources:       │
│                  │                       │  • doc.md       │
│  • Security-Agent│  KI: Here's the...    │  • wiki.md      │
│    ⚫ Idle        │  [1]                  │                 │
│                  │                       │  Token-Usage:   │
│  • Plan-Agent    │  [CHECKPOINT]         │  Input: 234     │
│    ⚫ Idle        │  ✓ Modified app.py    │  Output: 456    │
│                  │  [Show] [Undo]        │                 │
│                  │                       │  Latency:       │
│                  │                       │  223ms          │
└────────────────────────────────────────────────────────────┘
```

### LEFT: Agent-Stack (Navigation)
**Zeige:** Welche Sub-Agenten sind aktiv? Ihr Status?

- **Farbcode**: Grün (Idle), Cyan (Working), Amber (Waiting for Confirmation)
- **Icons**: Zeigen Agent-Typ (Coding 🖥️, RAG 📚, Security 🔒, Planning 📋)
- **Live-Pulse**: Wenn ein Agent arbeitet, pulsiert sein Icon in `brand-orchestrator`

### CENTER: Collaboration-Flow (Main)
**Zeige:** Die Konversation und die Ergebnisse.

- **User-Nachrichten**: Rechtsbündig, dunkler Hintergrund
- **KI-Antworten**: Linksbündig, sauberer Text mit Syntax-Highlighting
- **RAG-Ergebnisse**: Zwischen Nachrichten als **Source-Cards** eingeschaltet
- **Checkpoints**: Kleine Karten nach relevanten Aktionen
- **Citation-Links**: Im KI-Text als `[1]`, `[2]` (Hover zeigt Quelle)

### RIGHT: Forensic-Panel (Details)
**Zeige:** Der "Maschinenraum". Echtzeit-Telemetrie.

- **Logs**: Live-Stream von Systemereignissen (färbbar nach Level)
- **Metadata**: Token-Count, Latenz, Model-Name, Context-Length
- **RAG-Sources**: Welche Dokumente flossen ein? Mit Relevanz-Score
- **Checkpoints**: Alle Undo-fähigen Aktionen im Überblick
- **MCP-Calls**: Externe Integrations-Logs

---

## 4️⃣ RAG-SPEZIFISCHE UI-ELEMENTE

### Source-Cards
Wenn RAG ein Dokument findet, wird es als Karte zwischen den Chat-Nachrichten angezeigt.

**Format:**
```
┌─────────────────────────────────────┐
│ 📄 Document: architecture.md         │
│ Relevance: 92%                      │
│ From: /docs/design/               │
│                                     │
│ """                                 │
│ The system uses a 3-pillar layout │
│ for maximum information density... │
│ """                                 │
│                                     │
│ [Expand Full] [Copy Fragment]      │
└─────────────────────────────────────┘
```

**Farben:**
- `brand-sentinel` Rahmen (Validierung)
- `status-trace` Text (Detail-Info)
- Icons nach Dateityp (PDF, Markdown, JSON, Web)

### Citation-Links
Im KI-generierten Text werden Quellenangaben nicht als URLs, sondern als **Nummern mit Hover-Info** angezeigt.

**Beispiel:**
```
Die Architektur folgt einem 3-Säulen-Raster[1],
wie in der Design-Spec[2] definiert.

Hover über [1]:
↓
Popup: "architecture.md: The system uses
a 3-pillar layout..."
```

### Vektor-Pulse
Während das RAG-System das Archiv durchsucht, animiert sich ein dezenter Glow-Effekt.

**Technische Umsetzung:**
```css
.rag-search {
  border: 2px solid var(--brand-orchestrator);
  animation: vektor-pulse 1.2s ease-in-out infinite;
}

@keyframes vektor-pulse {
  0% { border-color: transparent; }
  50% { border-color: var(--brand-orchestrator); }
  100% { border-color: transparent; }
}
```

---

## 5️⃣ IMPLEMENTIERUNGS-ROADMAP

### Phase 1: Core Layout (MVP)
- [ ] 3-Säulen-Grid (Flexbox/CSS Grid)
- [ ] Farbpalette in CSS-Variablen
- [ ] `surface-glass` mit `backdrop-filter: blur(20px)`

### Phase 2: Interactive Elements
- [ ] Agent-Stack mit Live-Status
- [ ] Chat-Nachrichten (User ↔ KI)
- [ ] Checkpoint-Cards mit Undo

### Phase 3: RAG-Integration
- [ ] Source-Cards rendern
- [ ] Citation-Links mit Hover
- [ ] Vektor-Pulse Animation

### Phase 4: Forensic-Panel
- [ ] Live-Logs anzeigen
- [ ] Token-Metadata
- [ ] MCP-Call-History

### Phase 5: Polish & Accessibility
- [ ] WCAG AA Contrast-Check
- [ ] Dark-Mode Refinement
- [ ] Responsive Design (Mobile)

---

## 6️⃣ CSS-VARIABLEN-TEMPLATE

```css
:root {
  /* SURFACES */
  --surface-ground: #0A0E14;
  --surface-glass: rgba(20, 26, 35, 0.7);
  --surface-glass-blur: blur(20px);

  /* BRAND */
  --brand-orchestrator: #00F2FF;
  --brand-sentinel: #1A73E8;

  /* STATUS */
  --status-action: #FFB000;
  --status-trace: #4A5568;
  --status-success: #48BB78;
  --status-error: #F56565;

  /* TEXT */
  --text-primary: #E2E8F0;
  --text-secondary: #A0AEC0;

  /* TYPOGRAPHY */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'Courier New', monospace;

  /* SPACING */
  --space-xs: 4px;
  --space-sm: 8px;
  --space-md: 16px;
  --space-lg: 24px;
  --space-xl: 32px;

  /* SHADOWS & EFFECTS */
  --shadow-glass: 0 8px 32px rgba(0, 242, 255, 0.1);
  --shadow-elevation: 0 4px 12px rgba(0, 0, 0, 0.3);
}

/* COMPONENT: Glass Panel */
.glass-panel {
  background: var(--surface-glass);
  backdrop-filter: var(--surface-glass-blur);
  border: 1px solid rgba(0, 242, 255, 0.2);
  border-radius: 8px;
  box-shadow: var(--shadow-glass);
  padding: var(--space-md);
}

/* COMPONENT: Action Button */
.btn-action {
  background: var(--status-action);
  color: var(--surface-ground);
  font-family: var(--font-sans);
  font-weight: 500;
  padding: var(--space-sm) var(--space-md);
  border-radius: 4px;
  cursor: pointer;
}

.btn-action:hover {
  filter: brightness(1.1);
}

/* COMPONENT: Code Block */
pre, code {
  font-family: var(--font-mono);
  background: var(--surface-glass);
  border: 1px solid var(--status-trace);
  padding: var(--space-md);
  border-radius: 4px;
}
```

---

## 7️⃣ WARUM DAS FUNKTIONIERT

### Für KI-Agenten
Wenn du diesen Text in einen KI-Kontext kopierst (via Prompt oder Knowledge Base), "weiß" die KI sofort:

- **Bei Antwortgenerierung**: Quellen als Source-Cards formatieren
- **Bei Code-Output**: In `font-family: var(--font-mono)` rendern
- **Bei kritischen Operationen**: Action Amber Button + Confirmation Modal
- **Bei Metadaten-Anzeige**: In `status-trace` Farbe, JetBrains Mono Font

### Für Entwickler
Die CSS-Variablen sind **DRY** (Don't Repeat Yourself). Wenn die Brand-Farbe wechselt, änderst du eine Variable – alles andere folgt.

### Für Nutzer
Die UI ist:
- ✅ **Transparent** (Glass-Box Animationen zeigen Prozesse)
- ✅ **Revidierbar** (Undo überall, Archive statt Delete)
- ✅ **Fokussiert** (Details sind optional, nicht zwingend)
- ✅ **Respektvoll** (Kritische Aktionen brauchen Bestätigung)

---

## VERSION & GOVERNANCE

- **Version:** 1.0
- **Status:** Final Specification (Ready for Implementation)
- **Last Updated:** 2026-03-18
- **Design Authority:** RB-Protokoll Core Team
- **License:** Closed Source – Antigravity Project

---

## NÄCHSTE SCHRITTE

1. **Kopiere diese Datei** in dein Projekt: `/docs/ARCHITEKT_THEME.md`
2. **Nutze die CSS-Variablen** als globalen Stylesheet
3. **Implementiere die 3-Pillar-Layout** in deinem Framework (React, Vue, Svelte, etc.)
4. **Trainiere deine KI-Agenten** mit diesem Text – sie werden die Semantik verstehen

---

**Das ist dein Kompass für konsistentes Design, egal welche KI am Steuer sitzt.** 🎯
