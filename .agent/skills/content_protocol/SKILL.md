---
name: Content Protocol
description: SEO + KI-Suche Content-Protokoll. Leitfaden für die Erstellung von Content, der sowohl bei Google rankt als auch von KI-Systemen zitiert wird.
author: Antigravity Core
version: 1.0.0
triggers:
  - "Content erstellen"
  - "SEO Content"
  - "/content"
---

# Content Protocol: SEO + KI-Optimierter Content

> Abarbeitungsleitfaden für Content-Erstellung
> Ziel: Google-Ranking + KI-Zitation

## 1. Prerequisites

- [ ] Thema ist validiert (Nutzerfrage beantwortbar)
- [ ] Eigene Erfahrung/Daten vorhanden (oder Recherche geplant)
- [ ] Zielgruppe definiert

## 2. Die 5 Phasen

### Phase 1: Recherche & Setup
1. **Themenvalidierung** durchführen:
   - Technisch/IT → Fokus auf "HowTo" + "Troubleshooting"
   - Strategisch/Beratung → Fokus auf "Framework" + "Vergleich"
   - Meinung/Trend → Fokus auf "Positionierung" + "Gegenposition"

2. **Keyword-Matrix** erstellen:
   | Typ | Verwendung |
   |---|---|
   | **Primary** | H1, URL, Meta-Title |
   | **Secondary** (3-5) | H2, Absätze |
   | **Long-tail** | FAQ, Unterkapitel |
   | **Frage-Keywords** (3) | TL;DR, FAQ |

### Phase 2: Content-Struktur

**Pflicht-Abschnitte (in dieser Reihenfolge):**

#### A. Hero-Block (Erste 150 Worte)
```markdown
# [H1: Primary Keyword]

**TL;DR:** [Antwort in 1-2 Sätzen. Direkt. Ohne Füllwörter.]

- **Für wen:** [Zielgruppe in 5 Wörtern]
- **Zeitaufwand:** [X Minuten/Stunden]
- **Ergebnis:** [Konkretes Outcome]
```
- [ ] TL;DR max. 50 Wörter
- [ ] Meta-Info ausgefüllt
- [ ] Inhaltsverzeichnis mit Ankern

#### B. Kontext-Block
- [ ] Persönliche/Eigene Erfahrung erwähnt
- [ ] Problem → Lösung Struktur

#### C. Hauptteil
- [ ] Max. 3 Sätze pro Absatz
- [ ] Bullet-Points für Listen
- [ ] Code-Beispiele oder Screenshots wo sinnvoll
- [ ] Interner Link zu verwandtem Content

#### D. Edge Cases / Häufige Fehler
```markdown
| Fehler | Ursache | Lösung |
|--------|---------|--------|
| [X] | [Y] | [Z] |
```
- [ ] Mindestens 2 Fehler behandelt

#### E. FAQ (3-5 Fragen)
- [ ] Jede Antwort < 60 Wörter
- [ ] Direkte Antwort am Satzanfang

#### F. Weiterführende Ressourcen
- [ ] Mindestens 2 interne Links
- [ ] Beschreibende Anchor-Texte

### Phase 3: Technische Optimierung

**Schema.org Markup:**
- Tutorial → HowTo Schema
- FAQ → FAQPage Schema
- Standard → Article Schema

**On-Page SEO:**
- [ ] URL slug = Primary Keyword
- [ ] Title Tag ≤ 60 Zeichen
- [ ] Meta Description ≤ 155 Zeichen
- [ ] Nur ein H1 pro Seite
- [ ] Alt-Text für alle Bilder
- [ ] Canonical Tag gesetzt

**KI-Optimierung:**
- [ ] Information Gain: Enthält Fakten, die KI nicht kennt
- [ ] Quellenwürdigkeit: Behauptungen mit Quellen belegt
- [ ] Struktur: Antworten klar extrahierbar
- [ ] Keine widersprüchlichen Aussagen

### Phase 4: Publizieren & Distribution

**Pre-Publish:**
- [ ] Rechtschreibung & Grammatik
- [ ] Alle Links funktionieren
- [ ] Mobile Ansicht getestet
- [ ] Ladezeit < 3s

**Post-Publish (48h):**
- [ ] URL bei Google Search Console einreichen
- [ ] Social Share (LinkedIn)
- [ ] Interne Verlinkung von bestehenden Artikeln

### Phase 5: Kontinuierliche Optimierung

**Update-Rhythmus:**
- Technische Docs → alle 6 Monate
- Grundlagen → jährlich
- News/Trends → nach 3 Monaten

**Bei Update:**
- [ ] Datum aktualisieren (`modified`)
- [ ] Neue Erkenntnisse hinzufügen
- [ ] Tote Links ersetzen

## 3. JSON-LD Template

```json
{
  "@context": "https://schema.org",
  "@type": "[Article|HowTo|FAQPage]",
  "headline": "[H1 Titel]",
  "description": "[Meta Description]",
  "author": {
    "@type": "Person",
    "name": "{{AUTHOR_NAME}}"
  },
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "mainEntityOfPage": {
    "@type": "WebPage"
  }
}
```

## 4. KPIs

### SEO:
- Organische Impressions, Position, Klicks, CTR (Ziel: > 3%)

### KI-Sichtbarkeit:
- Brand-Mentions in ChatGPT/Perplexity
- Direkte Zitationen (URL in AI-Antworten)
- "People also ask" Einträge

## 5. Constraints

- **IMMER** TL;DR als ersten Absatz
- **IMMER** FAQ-Section mit 3-5 Fragen
- **NIEMALS** Keyword-Stuffing (natürlich schreiben)
- **IMMER** eigene Erfahrung/Daten einbauen wenn vorhanden
- **IMMER** Schema.org Markup im `<head>`
