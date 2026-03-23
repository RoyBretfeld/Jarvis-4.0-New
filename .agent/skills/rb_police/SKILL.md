---
name: RB Police
description: Security-Scanner und Compliance-Prüfer. Findet Secrets, verbotene Dateien und Protokoll-Verstöße. Integriert die Sicherheitsregeln des RB-Protokolls.
author: Antigravity Core
version: 3.0.0
triggers:
  - "Police"
  - "Audit this file"
  - "Check project security"
---

# RB Police: Security & Compliance

> Vereint: `pre_commit_police.py` + `05_SECURITY.md`

## 1. Prerequisites

- [ ] Python 3.12+ verfügbar
- [ ] `scripts/pre_commit_police.py` existiert im Skill-Ordner
- [ ] Workspace ist ein Git-Repository (für Diff-Mode)

## 2. Instructions

### Schnell-Scan (Standard)
1. **Ausführen:** `python .agent/skills/rb_police/scripts/pre_commit_police.py`
2. **Output interpretieren:**
   - `✅ Scan complete` → Alles sauber, Grün melden
   - `⚠️ Policy violations` → Dateien + Zeilen auflisten
   - `❌ BLOCKED` → **SOFORT** den User alarmieren

### Voll-Scan (CI-Modus)
```powershell
$env:RB_POLICE_FULL_SCAN = "true"
python .agent/skills/rb_police/scripts/pre_commit_police.py
```

## 3. Sicherheitsregeln (Integriert)

### Verbotene Patterns (Hard Block)
| Pattern | Risiko | Beispiel |
|---|---|---|
| `AIza[0-9A-Za-z-_]{35}` | Google API Key | `AIzaSyB...` |
| `Authorization:\s*Bearer` | Auth Token | `Authorization: Bearer eyJ...` |
| `access_token` / `refresh_token` | OAuth Token | Token-Leaks |
| `sk-[a-zA-Z0-9]{20,}` | OpenAI Key | `sk-proj-...` |
| `BEGIN RSA PRIVATE KEY` | Private Key | PEM-Dateien |
| `API_KEY=` / `SECRET_KEY=` | Env-Secrets | `.env`-Leaks |

### Verbotene Dateien (Dürfen nicht ins Repo)
- `.env`, `client_secrets.json`, `credentials.json`
- `token.json`, `*.pem`, `*.key`
- `*.db`, `*.sqlite`, `*.db-journal`

### Ausnahmen (False-Positive-Filter)
- Zeilen mit `os.environ` oder `json.load` (laden, nicht definieren)
- Das Police-Skript selbst (enthält die Patterns als Regeln)
- Kommentare und Platzhalter (`{{...}}`, `TODO`)

## 4. Security-Checkliste (für /flow-close)

- [ ] Keine Secrets im Code
- [ ] Keine Secrets in Logs oder Dumps
- [ ] Blocked Files in `.gitignore`
- [ ] SQL: Prepared Statements / ORM (kein String-Concat)
- [ ] XSS: Output Escaping aktiv
- [ ] CSRF: Token/Cookie Policy gesetzt
- [ ] Uploads: MIME-Type + Size-Limit validiert

## 5. Constraints

- **NIEMALS** das Police-Script umgehen oder deaktivieren
- **IMMER** vor Commits ausführen (Pre-Commit Gate)
- Bei **jedem** neuen Secret-Pattern: Script erweitern + Error-DB Eintrag
