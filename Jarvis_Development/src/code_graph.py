"""
AWP-064 – Code Context Graph
Erstellt eine JSON-Map der Python-Modul-Abhängigkeiten für die UI.
Output: data/module_graph.json  (Nodes + Edges für D3.js / vis.js)
Python 3.12 | AST-based (keine externen Tools nötig)
"""

from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.code_graph")

SRC_DIR    = Path(__file__).parent
OUTPUT     = Path(__file__).parent.parent / "data" / "module_graph.json"
MODULE_PREFIX = "jarvis"


@dataclass
class GraphNode:
    id: str          # module name
    label: str
    file: str
    lines: int
    group: str       # "core" | "agents" | "ui" | "config"
    size: int = 10   # visual weight (scales with lines)


@dataclass
class GraphEdge:
    source: str
    target: str
    weight: int = 1  # number of symbols imported


@dataclass
class ModuleGraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)


def _module_id(path: Path, root: Path) -> str:
    rel = path.relative_to(root)
    return str(rel).replace("\\", "/").replace("/", ".").removesuffix(".py")


def _group(path: Path) -> str:
    parts = path.parts
    if "agents" in parts:
        return "agents"
    if "ui" in parts:
        return "ui"
    if path.name in ("config.py", "schemas.py"):
        return "config"
    return "core"


def _parse_imports(source: str) -> list[str]:
    """Extract all imported module names from Python source."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module.split(".")[0])
    return imports


def build_graph(src_root: Path = SRC_DIR) -> ModuleGraph:
    graph = ModuleGraph()
    py_files = [
        f for f in src_root.rglob("*.py")
        if "__pycache__" not in str(f) and "ui" not in str(f)
    ]

    # Collect all local module names
    local_modules: dict[str, Path] = {}
    for f in py_files:
        mod_id = _module_id(f, src_root.parent)
        local_modules[f.stem] = f
        local_modules[mod_id] = f

    # Build nodes
    for f in py_files:
        mod_id = _module_id(f, src_root.parent)
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
            n_lines = len(source.splitlines())
        except OSError:
            n_lines = 0
        graph.nodes.append(GraphNode(
            id=mod_id,
            label=f.stem,
            file=str(f.relative_to(src_root.parent)),
            lines=n_lines,
            group=_group(f),
            size=max(8, min(50, n_lines // 20)),
        ))

    # Build edges
    edge_map: dict[tuple[str, str], int] = {}
    for f in py_files:
        src_id = _module_id(f, src_root.parent)
        try:
            source = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        imports = _parse_imports(source)
        for imp in imports:
            # Only edges to local modules
            if imp in local_modules:
                target_path = local_modules[imp]
                target_id = _module_id(target_path, src_root.parent)
                if src_id != target_id:
                    key = (src_id, target_id)
                    edge_map[key] = edge_map.get(key, 0) + 1

    graph.edges = [
        GraphEdge(source=s, target=t, weight=w)
        for (s, t), w in edge_map.items()
    ]

    log.info("Graph: %d nodes, %d edges", len(graph.nodes), len(graph.edges))
    return graph


def export_graph(graph: ModuleGraph, out: Path = OUTPUT) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "nodes": [asdict(n) for n in graph.nodes],
        "edges": [asdict(e) for e in graph.edges],
        "generated_at": __import__("datetime").datetime.utcnow().isoformat(),
        "stats": {
            "total_nodes": len(graph.nodes),
            "total_edges": len(graph.edges),
            "most_connected": sorted(
                [(n.id, sum(1 for e in graph.edges if e.source == n.id or e.target == n.id))
                 for n in graph.nodes],
                key=lambda x: -x[1]
            )[:5],
        },
    }
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    log.info("Graph exported to %s", out)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    g = build_graph()
    export_graph(g)
    print(f"Graph: {len(g.nodes)} nodes, {len(g.edges)} edges → {OUTPUT}")
