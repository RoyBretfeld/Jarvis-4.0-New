#!/usr/bin/env python3
"""
RB-Framework Police (Antigravity Edition)
Prüft auf Secrets und grobe Verstöße gegen das Protokoll.
"""
import os
import re
import sys
from pathlib import Path

# Blocked Files (Dürfen nicht committed werden)
BLOCK_FILES = [
    r"\.env$", 
    r"client_secrets\.json$", 
    r"credentials\.json$", 
    r"token\.json$", 
    r"drive_index\.db$",
    r"drive_index\.db-journal$"
]

# Secret Patterns (Harte Regeln)
SECRET_PATTERNS = [
    r"AIza[0-9A-Za-z-_]{35}", # Google API Key
    r"Authorization:\s*Bearer",
    r"access_token",
    r"refresh_token",
    r"sk-[a-zA-Z0-9]{20,}" # OpenAI Key pattern added for extra safety
]

def fail(msg):
    print(f"[POLICE] ❌ FAIL: {msg}")
    sys.exit(1)

def scan_file(path):
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        for i, line in enumerate(content.split("\n"), 1):
            for pattern in SECRET_PATTERNS:
                if re.search(pattern, line):
                    # Ausnahme: Code, der Secrets lädt/definiert, nicht das Secret selbst
                    if "os.environ" in line or "json.load" in line: continue
                    # Ausnahme: Diesen Script selbst ignorieren falls es Pattern enthält
                    if "SECRET_PATTERNS" in line: continue
                    
                    fail(f"Secret-Verdacht in {path.name}:{i} -> {pattern}")
    except Exception:
        pass

def main():
    print("🚓 RB Police: Scanning Antigravity Project...")
    root = Path.cwd()
    
    # 1. Check Blocked Files
    for pattern in BLOCK_FILES:
        for f in root.glob("*"):
            if re.search(pattern, f.name):
                # Wir warnen nur lokal, da diese Dateien lokal nötig sind, aber nicht ins Git dürfen
                print(f"[POLICE] ℹ️  Lokale Config gefunden (Check .gitignore): {f.name}")

    # 2. Scan Source Code in src/, system/, Jarvis_Development/
    EXCLUDE_DIRS = {".git", ".venv", "__pycache__", "node_modules"}
    for folder in ["src", "system", "Jarvis_Development"]:
        src = root / folder
        if src.exists():
            for py_file in src.rglob("*.py"):
                if any(ex in py_file.parts for ex in EXCLUDE_DIRS):
                    continue
                scan_file(py_file)
    
    # 3. Check Protocol Existence
    if not (root / "docs/_rb/02_SYSTEM_FACTS.md").exists():
        print("[POLICE] ❌ CRITICAL: RB Protokoll (02_SYSTEM_FACTS.md) fehlt in docs/_rb/!")
        sys.exit(1)

    print("[POLICE] ✅ Scan complete. System conforms to RB Protocol.")

if __name__ == "__main__":
    main()
