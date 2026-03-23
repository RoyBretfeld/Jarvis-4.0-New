#!/usr/bin/env python3
"""
RB-Framework Packer (v2.0)
Generates context dumps for agents/debugging
- Cross-platform (pathlib)
- Smart directory detection
- Configurable via environment
"""
import os
import re
import time
import shutil
from pathlib import Path
from typing import Set

# Default includes - automatically detect common project structures
DEFAULT_INCLUDE_DIRS = ["docs/_rb", "src", "tests", "scripts"]
COMMON_PROJECT_DIRS = [
    "backend", "frontend", "server", "client",
    "app", "lib", "pkg", "packages",
    "api", "web", "core",
    "agents", "static", "gui", "services", "tools",
    "docs",  # Immer inkludieren wenn vorhanden
]

# Spezielle Verzeichnisse die trotz Dot-Prefix eingeschlossen werden
SPECIAL_DOT_DIRS = [".agent"]

# Root-Level Dateien die immer eingeschlossen werden (wenn vorhanden)
ROOT_FILES = [
    "docs/_rb/02_SYSTEM_FACTS.md", "README.md", "ARCHITECTURE.md", "start_webui.bat", "Start.bat",
    "server.py", "config.py", "app.py", 
    "CHANGELOG.md", "RUNBOOK.md",
    "IMPROVEMENTS.md", "MISSION_COMPLETE.md", "RB_HARDENING_REPORT.md",
]

EXCLUDE_DIRS = {".git", "docs/_archive", "node_modules", ".venv", "__pycache__", 
                "dist", "build", ".next", ".nuxt", "vendor", 
                ".pytest_cache", "coverage", ".idea", ".vscode"}

MAX_BYTES = 2_000_000

BLOCK_FILES = [r"\.env$", r"\.pem$", r"\.key$", r"\.db$", r"\.sqlite$", r"\.pyc$"]

def is_blocked(path: Path) -> bool:
    """Check if file should be excluded from dump."""
    path_str = str(path).replace("\\", "/")
    return any(re.search(pattern, path_str, re.IGNORECASE) for pattern in BLOCK_FILES)

def detect_project_dirs(repo_root: Path) -> Set[Path]:
    """Auto-detect project directories based on common patterns."""
    detected = set()
    
    # Always include these if they exist
    for dir_name in DEFAULT_INCLUDE_DIRS:
        dir_path = repo_root / dir_name
        if dir_path.is_dir():
            detected.add(dir_path)
    
    # Scan for common project structures
    for item in repo_root.iterdir():
        if not item.is_dir():
            continue
        if item.name in EXCLUDE_DIRS:
            continue
        # Dot-Dirs: nur explizit erlaubte einschliessen
        if item.name.startswith("."):
            if item.name in SPECIAL_DOT_DIRS:
                detected.add(item)
            continue
        if item.name in COMMON_PROJECT_DIRS:
            detected.add(item)
    
    return detected

def should_exclude_dir(dir_path: Path) -> bool:
    """Check if directory should be excluded."""
    return any(excluded in dir_path.parts for excluded in EXCLUDE_DIRS)

def walk_and_collect(base_dir: Path, max_size: int) -> list:
    """Walk directory and collect file paths."""
    collected = []
    
    for item in base_dir.rglob("*"):
        if item.is_dir():
            continue
        
        # Skip excluded directories
        if should_exclude_dir(item):
            continue
        
        # Skip blocked files
        if is_blocked(item):
            continue
        
        # Skip large files
        try:
            if item.stat().st_size > max_size:
                continue
        except OSError:
            continue
        
        collected.append(item)
    
    return sorted(collected)

def get_antigravity_root() -> Path:
    """Find the Antigravity root directory for central dump storage."""
    # Hardcoded central path
    central = Path(r"E:\_____1111____Projekte-Programmierung\Antigravity")
    if central.is_dir():
        return central
    # Fallback: walk up from CWD looking for Antigravity marker
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "PROJEKT_UEBERSICHT.md").exists():
            return parent
        if parent.name == "Antigravity":
            return parent
    # Last resort: use CWD
    return Path.cwd()

def main():
    print("📦 LLM Project Packer v3.0")
    print("=" * 50)
    
    repo_root = Path.cwd()
    timestamp = time.strftime("%Y-%m-%d_%H-%M")
    project_name = repo_root.name
    
    # Local dump directory in project root
    dump_dir = repo_root / ".rb_dumps"
    dump_dir.mkdir(exist_ok=True)
    
    # Alte lokale Dumps bereinigen
    for old_dump in dump_dir.glob("*.txt"):
        try:
            old_dump.unlink()
        except OSError:
            pass
            
    # Dump mit Zeitstempel
    output_file = dump_dir / f"{project_name}_DUMP_{timestamp}.txt"
    
    # Get custom include dirs from environment
    custom_includes = os.environ.get("RB_PACK_INCLUDE", "")
    if custom_includes:
        include_dirs = {repo_root / d.strip() for d in custom_includes.split(",") if d.strip()}
        print(f"📂 Using custom includes: {', '.join(d.name for d in include_dirs)}")
    else:
        # Auto-detect
        include_dirs = detect_project_dirs(repo_root)
        print(f"🔍 Auto-detected directories: {', '.join(d.name for d in include_dirs)}")
    
    if not include_dirs:
        print("⚠️  No directories found to pack! Aborting.")
        return
    
    # Root-Level Dateien immer einschliessen (konfiguriert via ROOT_FILES)
    root_files = [repo_root / f for f in ROOT_FILES if (repo_root / f).exists() and not is_blocked(repo_root / f)]

    # Collect all files
    all_files = list(root_files)
    for dir_path in sorted(include_dirs):
        if not dir_path.exists():
            print(f"⚠️  Skipping non-existent: {dir_path.name}")
            continue
        all_files.extend(walk_and_collect(dir_path, MAX_BYTES))
    
    # Deduplicate while preserving order (so ROOT_FILES stay at the top)
    all_files = list(dict.fromkeys(all_files))
    
    print(f"📄 Found {len(all_files)} file(s) to pack")
    
    # Write dump
    with output_file.open("w", encoding="utf-8") as w:
        w.write(f"# Project Context Dump – Letzter Stand: {timestamp}\n")
        w.write(f"# Generated by LLM Project Packer v3.0\n")
        w.write(f"# Repository: {repo_root.name}\n")
        w.write(f"# Root: {repo_root}\n")
        w.write(f"# Total files: {len(all_files)}\n")
        w.write("\n" + "=" * 80 + "\n\n")
        
        for file_path in all_files:
            rel_path = file_path.relative_to(repo_root)
            w.write(f"\n\n{'=' * 80}\n")
            w.write(f"FILE: {rel_path}\n")
            w.write(f"{'=' * 80}\n\n")
            
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                w.write(content)
            except Exception as e:
                w.write(f"<ERROR: Could not read file: {e}>")
    
    # Kopie an zentralen Ort senden
    central_dumps_dir = get_antigravity_root() / ".rb_dumps"
    central_dumps_dir.mkdir(exist_ok=True)
    
    # Alte zentrale Dumps für dieses Projekt bereinigen
    for old_central in central_dumps_dir.glob(f"{project_name}_DUMP_*.txt"):
        try:
            old_central.unlink()
        except OSError:
            pass
            
    central_file = central_dumps_dir / output_file.name
    shutil.copy2(output_file, central_file)

    file_size_kb = output_file.stat().st_size / 1024
    print(f"✅ Context dump created: {output_file.name} (Local: {dump_dir})")
    print(f"✅ Copy sent to: {central_dumps_dir}")
    print(f"📊 Size: {file_size_kb:.1f} KB")
    print(f"\n💡 Tip: Use 'RB_PACK_INCLUDE=dir1,dir2' to customize includes")

if __name__ == "__main__":
    main()

