# SEO + KI-Suche Content-Protokoll v1.0

> Abarbeitungsleitfaden für Content-Erstellung
> Ziel: Google-Ranking + KI-Zitation

---

## ⚙️ Abarbeitungsmodus: §5 Plan Execution Autonomy

Wenn ein Content-Plan finalisiert ist:
- ✅ **Chronologische Abarbeitung** – Phase für Phase in dieser Reihenfolge
- ✅ **Maximale Autonomie** – Alle Phasen automatisch durchlaufen
- ✅ **Nur Blocker eskalieren** – Nur bei echten Hindernissen unterbrechen
- 📚 **Siehe auch:** [RB-Protokoll §5](docs/_rb/01_PLAN_EXECUTION.md)

---

## PHASE 1: RECHERCHE & SETUP

### Schritt 1.1: Themenvalidierung
- [ ] **Wenn** Thema = Technisch/IT-spezifisch **dann** → Fokus auf "HowTo" + "Troubleshooting"
- [ ] **Wenn** Thema = Strategisch/Beratung **dann** → Fokus auf "Framework" + "Vergleich"
- [ ] **Wenn** Thema = Meinung/Trend **dann** → Fokus auf "Positionierung" + "Gegenposition"

**Ja/Nein Check:**
- [ ] Kann ich hierzu eine konkrete Nutzerfrage beantworten? (Ja/Nein)
- [ ] Hab ich hierzu eigene Erfahrung/Daten? (Ja/Nein → Wenn Nein, Recherche notwendig)
- [ ] Existiert dieser Content bereits 10x im Netz? (Ja → Einzigartigen Angle finden / Nein → Schnell sein)

---

### Schritt 1.2: Keyword-Matrix (Dual-Track)

| Typ | Beispiel | Verwendung |
|-----|----------|------------|
| **Primary** | "Proxmox VLAN einrichten" | H1, URL, Meta-Title |
| **Secondary** | "Proxmox Netzwerkkonfiguration" | H2, Absätze |
| **Long-tail** | "Proxmox VLAN Tagging Windows VM" | FAQ, Unterkapitel |
| **Frage-Keywords** | "Wie richte ich VLAN in Proxmox ein?" | TL;DR, FAQ |

- [ ] Primary Keyword identifiziert
- [ ] 3-5 Secondary Keywords identifiziert
- [ ] 3 Frage-Keywords für TL;DR extrahiert

---

## PHASE 2: CONTENT-STRUKTUR (Template)

### Schritt 2.1: Dokument-Setup
```markdown
---
title: "[Primary Keyword] - [Zusatznutzen]"
description: "[Primary Keyword]. [Sekundäres Keyword]. [Call to Action]."
date: YYYY-MM-DD
modified: YYYY-MM-DD
schema: [Article|HowTo|FAQPage]
author: Roy Bretfeld
expertise_level: [Anfänger|Fortgeschritten|Experte]
---
```

### Schritt 2.2: Pflicht-Abschnitte (In dieser Reihenfolge)

#### A. Hero-Block (Erste 150 Worte)
```
# [H1: Primary Keyword]

**TL;DR:** [Antwort in 1-2 Sätzen. Direkt. Ohne Füllwörter.]

- **Für wen:** [Zielgruppe in 5 Wörtern]
- **Zeitaufwand:** [X Minuten/Stunden]
- **Ergebnis:** [Konkretes Outcome]

**Inhalt:**
- [Thema 1]
- [Thema 2]  
- [Thema 3]
```
- [ ] TL;DR geschrieben (max. 50 Wörter)
- [ ] Meta-Info (Wer/Zeit/Ergebnis) ausgefüllt
- [ ] Inhaltsverzeichnis mit Ankern

#### B. Kontext-Block (Warum das wichtig ist)
```
## Warum das relevant ist

[Nutzerperspektive einnehmen]
[Problem beschreiben]
[Eigene Erfahrung einstreuen: "In 35 Jahren..." / "Bei Kunde X..."]
```
- [ ] Persönliche/Eigene Erfahrung erwähnt? (Ja/Nein)
- [ ] Problem → Lösung Struktur?

#### C. Hauptteil (Der Wert)
```
## [H2: Secondary Keyword 1]

### [H3: Konkreter Schritt/Aspekt]
[Erklärung]
```
**Regeln für jeden Absatz:**
- [ ] Max. 3 Sätze pro Absatz
- [ ] Bullet-Points für Listen
- [ ] Code-Beispiele oder Screenshots wo sinnvoll
- [ ] Interner Link zu verwandtem Content?

#### D. Edge Cases (Das unterscheidet dich)
```
## Häufige Fehler & Probleme

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| [X] | [Y] | [Z] |
```
- [ ] Mindestens 2 Fehler behandelt
- [ ] Troubleshooting-Szenario abgedeckt

#### E. FAQ (Für Featured Snippets & KI-Antworten)
```
## FAQ

### [Frage-Keyword 1]
[Antwort in 40-60 Wörtern]

### [Frage-Keyword 2]
[Antwort in 40-60 Wörtern]

### [Frage-Keyword 3]
[Antwort in 40-60 Wörtern]
```
- [ ] 3-5 Fragen beantwortet
- [ ] Jede Antwort < 60 Wörter
- [ ] Direkte Antwort am Anfang des Satzes

#### F. Verknüpfung (Interne Links)
```
## Weiterführende Ressourcen

- [Verwandter Artikel 1 mit Kontext]
- [Verwandter Artikel 2 mit Kontext]
- [Tool/Download falls vorhanden]
```
- [ ] Mindestens 2 interne Links gesetzt
- [ ] Links haben beschreibenden Anchor-Text (nicht "hier klicken")

---

## PHASE 3: TECHNISCHE OPTIMIERUNG

### Schritt 3.1: Schema.org Markup

**Wenn** Content = Tutorial/Anleitung **dann** → HowTo Schema
**Wenn** Content = Fragen & Antworten **dann** → FAQPage Schema
**Wenn** Content = Standard-Artikel **dann** → Article Schema

**JSON-LD Template (Kopieren & Anpassen):**
```json
{
  "@context": "https://schema.org",
  "@type": "[Article|HowTo|FAQPage]",
  "headline": "[H1 Titel]",
  "description": "[Meta Description]",
  "author": {
    "@type": "Person",
    "name": "Roy Bretfeld"
  },
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "mainEntityOfPage": {
    "@type": "WebPage"
  }
}
```
- [ ] Schema-Typ ausgewählt
- [ ] JSON-LD im `<head>` eingefügt
- [ ] Required Fields ausgefüllt (Test: validator.schema.org)

### Schritt 3.2: On-Page SEO Check

- [ ] URL slug = Primary Keyword (kurz, keine Stop-Wörter)
- [ ] Title Tag = Primary Keyword + Brand (max. 60 Zeichen)
- [ ] Meta Description = CTA + Keywords (max. 155 Zeichen)
- [ ] H1 = Primary Keyword (nur ein H1 pro Seite)
- [ ] Alt-Text für alle Bilder (deskriptiv, nicht keyword-gestopft)
- [ ] Canonical Tag gesetzt

### Schritt 3.3: KI-Optimierung (Neu)

- [ ] **Information Gain:** Enthält der Text Fakten, die ChatGPT nicht weiß? (Ja/Nein → Wenn Nein, ergänzen)
- [ ] **Quellenwürdigkeit:** Werden Behauptungen mit Quellen belegt?
- [ ] **Struktur:** Sind Antworten so klar formuliert, dass eine KI sie extrahieren könnte?
- [ ] **Eindeutigkeit:** Gibt es keine widersprüchlichen Aussagen?

---

## PHASE 4: PUBLIZIEREN & DISTRIBUTION

### Schritt 4.1: Pre-Publish

- [ ] Rechtschreibung & Grammatik geprüft
- [ ] Alle Links funktionieren?
- [ ] Mobile Ansicht getestet?
- [ ] Ladezeit akzeptabel (< 3s)?
- [ ] robots.txt erlaubt Crawling?

### Schritt 4.2: Post-Publish (First 48h)

**Sofort:**
- [ ] URL bei Google Search Console einreichen
- [ ] Social Share (LinkedIn, falls professioneller Content)
- [ ] Interne Verlinkung von bestehenden Artikeln zur neuen URL

**Nach 24h:**
- [ ] Index-Status prüfen (site:roy-bretfeld.de/url)
- [ ] Search Console: Impressions checken

**Nach 7 Tagen:**
- [ ] Performance analysieren (CTR, Position)
- [ ] Wenn CTR < 2% → Title/Description überarbeiten
- [ ] Wenn Bounce Rate > 80% → Content-Qualität prüfen

---

## PHASE 5: KONTINUIERLICHE OPTIMIERUNG

### Schritt 5.1: Update-Rhythmus

**Wenn** Content = Technische Dokumentation **dann** → Alle 6 Monate prüfen
**Wenn** Content = Grundlagen/Theory **dann** → Jährlich prüfen
**Wenn** Content = News/Trends **dann** → Nach 3 Monaten archivieren oder aktualisieren

### Schritt 5.2: Content-Auffrischung

Bei Update:
- [ ] Datum aktualisieren (`modified`)
- [ ] Neue Erkenntnisse/Erfahrungen hinzufügen
- [ ] Tote Links ersetzen
- [ ] Nummerierte Listen/Daten aktualisieren
- [ ] Absatz "Update [Datum]: [Was ist neu]" einfügen

---

## ENTSCHEIDUNGSBAUM

```
Start: Neuer Content
│
├─→ Thema ist Zeit-sensitiv (News/Trend)?
│   ├─ Ja → Schnell publizieren (innerhalb 24h), kurzer Lebenszyklus
│   └─ Nein → → 
│
├─→ Kann ich eigene Daten/Erfahrung beisteuern?
│   ├─ Ja → Experten-Content (langfristige Authority)
│   └─ Nein → Recherche notwendig oder Thema wechseln
│
├─→ Existiert der Content bereits oft?
│   ├─ Ja → Einzigartigen Angle finden (z.B. "Für Dresden", "Mit Proxmox 8")
│   └─ Nein → SEO-First, schnell ranken
│
└─→ Fertig → Publizieren → 48h Monitoring → Update nach 6-12 Monaten
```

---

## MESSGRÖSSEN (KPIs)

### Für traditionelles SEO:
- [ ] Organische Impressions (Search Console)
- [ ] Durchschnittliche Position für Primary Keyword
- [ ] Organische Klicks
- [ ] CTR (Ziel: > 3%)

### Für KI-Sichtbarkeit:
- [ ] Brand-Mentions in ChatGPT/Perplexity (manuell testen: "Wer ist Roy Bretfeld zu [Thema]?")
- [ ] Direkte Zitationen (wird deine URL in AI-Antworten genannt?)
- [ ] "People also ask" Einträge bei Google

---

## NOTIZEN & ANPASSUNGEN

**Protokoll-Version:** 1.0
**Letzte Aktualisierung:** 2026-03-10
**Nächste Review:** 2026-06-10

**Changelog:**
- v1.0 (2026-03-10): Initiale Erstellung

**Prozess-Optimierungen (Nach 5 Content-Stücken reviewen):**
- [ ] Was hat funktioniert?
- [ ] Was hat zu lange gedauert?
- [ ] Welche Schritte können wegfallen?

---

**Abarbeitungs-Status für aktuellen Content:**
- [ ] Phase 1 abgeschlossen
- [ ] Phase 2 abgeschlossen
- [ ] Phase 3 abgeschlossen
- [ ] Phase 4 abgeschlossen (Published am: ___)
- [ ] Phase 5 eingeplant für: ___
