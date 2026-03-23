# 📦 Dump Automation: Automatische Context-Snapshots

**Status:** Spezifikation für automatische Dump-Erstellung

---

## Trigger-Events für automatische Dumps

Ein Dump sollte automatisch erstellt werden bei folgenden **Meilensteinen & Dokumentations-Events**:

### 1️⃣ Feature / Sprint Completion

**Trigger:** Feature ist fertig, dokumentiert, getestet

```bash
# Nach /flow-close erfolg → automatisch:
PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py

# Oder via Hook:
echo "[MILESTONE] Feature X completed" → packer ausführen
```

**Zeitpunkt:** Nach Feature-Validierung, vor Merge

### 2️⃣ Documentation Updates

**Trigger:** `.md` Dateien wurden hinzugefügt/geändert

```bash
# Nach README.md, ARCHITECTURE.md, oder docs/ Update:
→ Dump erstellen

# Grund: Neue Dokumentation sollte im Kontext-Snapshot abbildbar sein
```

**Zeitpunkt:** Direkt nach Dokumentations-Commit

### 3️⃣ Session-Ende / Checkpoint

**Trigger:** End-of-Session oder natürlicher Breakpoint

```bash
# Am Ende einer produktiven Coding-Session:
/pack  oder  PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py

# Grund: Snapshot für nächste Session als Baseline
```

**Zeitpunkt:** Vor Session-Ende, nach größeren Änderungen

### 4️⃣ Error/Incident Response

**Trigger:** Nach Fehlerfix oder Security-Incident

```bash
# Nach ERR-* Eintrag in Error-DB:
→ Sofort Dump erstellen

# Grund: Forensic-Analysis, Rollback-Baseline
```

**Zeitpunkt:** Unmittelbar nach Fix-Commit

### 5️⃣ Pre-Deployment

**Trigger:** Vor Production-Deployment

```bash
# Vor git push → production:
/pack

# Grund: Baseline für Incident-Investigation im Prod
```

**Zeitpunkt:** Last check vor Deploy

---

## Dump-Dateiname & Speicherverwaltung

### Format
```
PROJECT-NAME_DUMP_YYYY-MM-DD_HH-MM.txt
```

**Beispiel:**
```
antigravity-rb_DUMP_2026-03-18_17-30.txt
```

### Speicherorte
```
Lokal:  ./_rb-dump/PROJECT_DUMP_YYYY-MM-DD_HH-MM.txt
Zentral: E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps/PROJECT_DUMP_YYYY-MM-DD_HH-MM.txt
```

### Cleanup-Policy
```
✅ NUR EINER PRO PROJEKT bleibt erhalten
   └─ Der neueste (nach Timestamp)

⏰ Automatisches Löschen:
   └─ Alte Dateien werden bei der nächsten /pack gelöscht
   └─ Keine manuelle Verwaltung nötig
```

---

## Implementierungs-Methoden

### Methode 1: Git Hooks (Automatisch)

**Pre-commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Vor jedem Commit prüfen: Dokumentation geändert?
if git diff --cached --name-only | grep -E "\.md$|docs/"; then
    echo "📦 Dokumentation geändert → Dump wird erstellt..."
    PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py
fi
```

**Post-commit Hook** (`.git/hooks/post-commit`):
```bash
#!/bin/bash
# Nach bestimmten Commits (Feature-Fertig-Marker)
# Wenn Commit-Message "[MILESTONE]" enthält:
if git log -1 --pretty=%B | grep -q "\[MILESTONE\]"; then
    echo "🎯 Meilenstein erreicht → Context-Dump..."
    PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py
fi
```

### Methode 2: Agent Workflow Integration

In `.agent/workflows/flow-close.md`:
```yaml
---
description: Feature abschließen + Context-Dump
---

1. UX Guardian Audit (§1-4)
2. Feature-Dokumentation
3. **→ Automatischer Dump**
   └─ packer.py ausführen
   └─ Zentral speichern
```

### Methode 3: CI/CD Pipeline

In `.github/workflows/ci.yml`:
```yaml
- name: Create Context Dump on Success
  if: success()
  run: |
    PYTHONIOENCODING=utf-8 python .agent/skills/rb_packer/scripts/packer.py
```

### Methode 4: Manual Triggers (Slash-Commands)

```bash
/pack              # Standard Context-Dump
/pack-milestone    # Mit Meilenstein-Marker
/pack-session-end  # Session-Abschluss-Dump
```

---

## Dump-Inhalt nach Trigger

### Feature Completion Dump
```
- Neuer Code (src/)
- Tests
- Dokumentation
- Error-DB Updates
- Timestamp: [FEATURE_COMPLETE]
```

### Documentation Dump
```
- Alle .md Dateien
- Updated CHANGELOG
- Timestamp: [DOCS_UPDATE]
```

### Session-End Dump
```
- Kompletter Project-State
- Alle Änderungen seit Session-Start
- Timestamp: [SESSION_END]
```

### Pre-Deploy Dump
```
- Vollständiger Production-Baseline
- Alle Tests passing
- Timestamp: [PRE_DEPLOY]
```

---

## Cleanup-Automatik (im packer.py)

Die Cleanup-Logik ist bereits **implementiert**:

```python
# Zeile 135-140 (Lokal)
for old_dump in dump_dir.glob("*.txt"):
    try:
        old_dump.unlink()  # Löschen
    except OSError:
        pass

# Zeile 200-205 (Zentral)
for old_central in central_dumps_dir.glob(f"{project_name}_DUMP_*.txt"):
    try:
        old_central.unlink()  # Löschen
    except OSError:
        pass
```

**Ergebnis:**
```
Nach /pack:
_rb-dump/
└── project_DUMP_2026-03-18_17-30.txt  (← einzige Datei)

E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps/
└── project_DUMP_2026-03-18_17-30.txt  (← einzige Kopie)
```

---

## Best Practice: Dump-Integration ins Workflow

### Szenario: Feature fertig machen

```bash
# 1. Feature entwickelt
git add . && git commit -m "[MILESTONE] User Auth Feature Complete"
→ Post-Commit Hook aktiviert
→ Dump erstellt ✅

# 2. Dokumentation aktualisiert
git add docs/ && git commit -m "Docs: User Auth API"
→ Pre-Commit Hook erkennt .md Änderung
→ Dump erstellt ✅

# 3. Session endet
/pack  (oder Script)
→ Final Context-Dump für nächste Session ✅

# Ergebnis im _rb-dump/:
project_DUMP_2026-03-18_17-30.txt  (← einzige Datei, der neueste)
```

---

## Monitoring & Audit

### Wie man sieht, dass Dumps erstellt wurden

```bash
# Lokal prüfen
ls -lh _rb-dump/

# Zentral prüfen
ls -lh E:\_____1111____Projekte-Programmierung\Antigravity\.rb_dumps | grep project_name

# Zeitstempel-Check
stat _rb-dump/project_DUMP_*.txt | grep Modify
```

### Was tun mit alten Dumps?

```
❌ Alte Dumps: GELÖSCHT (Cleanup-Automatik)
✅ Aktuellster: BEHALTEN (für LLM-Kontext)
✅ Zentrale Kopie: BEHALTEN (für Forensics über alle Projekte)
```

---

## Zusammenfassung

| Event | Trigger | Action | Result |
|-------|---------|--------|--------|
| **Feature Complete** | Commit mit `[MILESTONE]` | `/pack` | Dump erstellt |
| **Docs Updated** | `.md` Änderung | Auto Hook | Dump erstellt |
| **Session End** | Manual `/pack` | packer.py | Dump erstellt |
| **Error Fixed** | Error-DB Entry | Manual `/pack` | Dump + Forensic |
| **Pre-Deploy** | Before push → prod | Manual `/pack` | Baseline Snapshot |

**Regel:** Nach jedem dieser Events → **Genau EINER Dump bleibt**.

---

## Version & Status

- **Version:** 1.0
- **Status:** Implementation Ready
- **Automation Level:** 70% bereits implementiert (Git Hooks fehlen noch)
- **Next Step:** Git Hooks Skripte in `.git/hooks/` hinzufügen

---

**Ziel:** Jeder Meilenstein hat einen Snapshot. Jede Session hat einen Baseline-Dump. Alles dokumentiert, nichts verloren. 📦✅
