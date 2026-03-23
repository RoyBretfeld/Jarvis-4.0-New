# §5 Plan Execution Autonomy

**Version:** 1.0
**Status:** Active
**Priority:** CRITICAL

---

## Zweck

Dieses Protokoll definiert den Betriebsmodus für die autonome Ausführung genehmigter Pläne. Nach Planfinalisierung wird maximale Autonomie gewährt, um effiziente und zielgerichtete Umsetzung zu ermöglichen.

---

## Die Regel

Sobald ein Plan fertiggestellt und vom Nutzer genehmigt ist:

### 1. Strikte Einhaltung des Plans
- Der Ablaufplan wird exakt wie dokumentiert umgesetzt
- Abweichungen nur bei kritischen Blockern mit Benachrichtigung
- Keine spontanen Änderungen oder "Verbesserungen"

### 2. Chronologische Reihenfolge
- Alle Schritte werden in der festgelegten Reihenfolge abgearbeitet
- Abhängigkeiten respektieren (nicht überspringen)
- Eine Aufgabe nach der anderen, nicht durcheinander

### 3. Maximale Autonomie
- **Proaktiv vorangehen** – nicht bei jedem Schritt nachfragen
- **Eigenständig entscheiden** bei erwarteten Szenarien
- **Keine unnötigen Pausen** zwischen Schritten

### 4. Selektive Eskalation
- Nur echte Blocker → sofortige Benachrichtigung
- Nicht für normale Entscheidungen fragen
- Nicht für bekannte Fehler/Lösungen eskalieren
- Nur wenn Richtung unklar ist

---

## Beispiel: Guter Plan

```
📋 PLAN: Datenbankmigrationen durchführen
├── 1. Backup erstellen
├── 2. Schema-Update ausführen
├── 3. Daten-Migrationen laufen
├── 4. Tests starten
├── 5. Rollout verifizieren
```

**Erwartetes Verhalten:**
- ✅ Alle 5 Schritte automatisch ausführen
- ✅ Fehler bei Step 3? Blockereskalation
- ✅ Test-Fehler bei Step 4? Mit Diagnostik-Info berichten
- ✅ Kein "Sollen wir Step 2 machen?" – nur machen

---

## Wann NICHT anwendbar

Diese Regel gilt **nicht** für:
- Ad-hoc Fragen oder Recherchen
- Unstrukturierte, offene Tasks
- One-off Debugging-Sessions
- Explorative Codebase-Analysen

**Trigger:** `EnterPlanMode` + User-Genehmigung mit `ExitPlanMode`

---

## Integration in Workflows

Alle Workflows unter `.agent/workflows/` folgen dieser Regel automatisch:

```yaml
# .agent/workflows/pack.md
---
description: Context-Dump für LLM/Debugging
turbo-all: true              ← Maximale Autonomie
---

1. Workspace-State scannen
2. Fehler-Kontext sammeln
3. Dump generieren
4. Erfolg melden
```

Das `turbo-all: true` Flag aktiviert §5-Modus explizit.

---

## Best Practice für Pläne

Damit diese Regel optimal funktioniert:

1. **Klar strukturieren** – Jeder Schritt sollte atomar und verständlich sein
2. **Dependencies markieren** – Wenn Step B auf Step A wartet
3. **Fehlerbehandlung definieren** – Was passiert wenn X fehlschlägt?
4. **Erfolgs-Kriterium** – Wann ist ein Schritt "fertig"?

**Beispiel:**
```
📋 Schritt 2: Dependencies installieren
   └─ Command: npm install
   └─ Success: package-lock.json updated
   └─ Blocker: Network-Fehler → eskalieren
   └─ Retry: 2x automatisch
```

---

## Autonomie-Grenzen

Agent respektiert diese Grenzen auch im §5-Modus:

- ❌ Keine `git push --force`
- ❌ Keine Datenlöschungen ohne Backup
- ❌ Keine breaking changes ohne Review
- ❌ Keine Credentials/Secrets in Code
- ✅ Alle anderen Operationen → voll autonom

---

## Siehe auch

- [RB-Protokoll Hauptseite (Hauptinstallation)](../README.md)
- [SYSTEM_FACTS.md](02_SYSTEM_FACTS.md)
- [ERROR_DB.md](03_ERROR_DB.md)
