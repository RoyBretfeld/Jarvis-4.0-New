"""
AWP-067 – Peer Review Agent
Automatisierte Code-Review nach den refactor_logic_v1.md Standards:
  - Komplexität (max. 20 Zeilen pro Funktion)
  - Docstrings (alle öffentlichen Symbole)
  - Typ-Annotationen (alle Parameter + Returns)
  - Keine globalen Variablen außerhalb von Konstanten
  - Keine doppelten Logikblöcke (copy-paste detection)

Python 3.12 | AST
"""

from __future__ import annotations

import ast
import hashlib
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger("jarvis.peer_review")

MAX_FUNC_LINES  = 20
MAX_COMPLEXITY  = 10   # McCabe-approximation: branching nodes


@dataclass
class ReviewIssue:
    severity: str        # "error" | "warning" | "info"
    rule: str
    message: str
    line: int = 0


@dataclass
class ReviewResult:
    file: str
    issues: list[ReviewIssue] = field(default_factory=list)
    passed: bool = True
    score: int = 100     # 100 = perfect; deducted per issue

    def add(self, issue: ReviewIssue) -> None:
        self.issues.append(issue)
        if issue.severity == "error":
            self.passed = False
            self.score -= 10
        elif issue.severity == "warning":
            self.score -= 3
        self.score = max(0, self.score)


class PeerReviewer:

    def review_file(self, path: Path) -> ReviewResult:
        result = ReviewResult(file=str(path))
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except (OSError, SyntaxError) as exc:
            result.add(ReviewIssue("error", "parse", str(exc)))
            return result

        lines = source.splitlines()
        self._check_functions(tree, lines, result)
        self._check_public_symbols(tree, result)
        self._check_globals(tree, result)
        self._check_duplicates(tree, source, result)
        return result

    # ── Rule: function length + complexity ────────────────────────────────

    def _check_functions(
        self,
        tree: ast.AST,
        lines: list[str],
        result: ReviewResult,
    ) -> None:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith("_"):
                continue   # private functions — relaxed rules

            # Length
            end = getattr(node, "end_lineno", node.lineno)
            func_lines = end - node.lineno + 1
            if func_lines > MAX_FUNC_LINES:
                result.add(ReviewIssue(
                    "warning", "func_length",
                    f"Function `{node.name}` is {func_lines} lines "
                    f"(max {MAX_FUNC_LINES})",
                    node.lineno,
                ))

            # McCabe-approximation
            complexity = 1 + sum(
                1 for n in ast.walk(node)
                if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                   ast.With, ast.Assert, ast.BoolOp))
            )
            if complexity > MAX_COMPLEXITY:
                result.add(ReviewIssue(
                    "warning", "complexity",
                    f"Function `{node.name}` complexity ≈{complexity} "
                    f"(max {MAX_COMPLEXITY})",
                    node.lineno,
                ))

    # ── Rule: docstrings + type annotations ───────────────────────────────

    def _check_public_symbols(
        self,
        tree: ast.AST,
        result: ReviewResult,
    ) -> None:
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("_"):
                    continue
                if not ast.get_docstring(node):
                    result.add(ReviewIssue(
                        "warning", "missing_docstring",
                        f"Public function `{node.name}` has no docstring",
                        node.lineno,
                    ))
                # Check return annotation
                if node.returns is None and node.name != "__init__":
                    result.add(ReviewIssue(
                        "info", "missing_return_type",
                        f"`{node.name}` missing return type annotation",
                        node.lineno,
                    ))
                # Check param annotations
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    if arg.annotation is None:
                        result.add(ReviewIssue(
                            "info", "missing_param_type",
                            f"`{node.name}` param `{arg.arg}` has no type annotation",
                            node.lineno,
                        ))

            elif isinstance(node, ast.ClassDef):
                if not node.name.startswith("_") and not ast.get_docstring(node):
                    result.add(ReviewIssue(
                        "info", "missing_class_docstring",
                        f"Class `{node.name}` has no docstring",
                        node.lineno,
                    ))

    # ── Rule: no bare globals (only UPPER_CASE constants allowed) ─────────

    def _check_globals(self, tree: ast.AST, result: ReviewResult) -> None:
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        name = target.id
                        if not name.isupper() and not name.startswith("_"):
                            result.add(ReviewIssue(
                                "warning", "global_variable",
                                f"Global variable `{name}` should be UPPER_CASE constant "
                                f"or moved inside a class/function",
                                node.lineno,
                            ))

    # ── Rule: copy-paste detection (body hash duplicates) ─────────────────

    def _check_duplicates(
        self,
        tree: ast.AST,
        source: str,
        result: ReviewResult,
    ) -> None:
        body_hashes: dict[str, str] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if len(node.body) < 3:
                continue   # too short to be meaningful
            try:
                body_src = ast.unparse(node)
                h = hashlib.md5(body_src.encode()).hexdigest()
            except Exception:
                continue
            if h in body_hashes:
                result.add(ReviewIssue(
                    "error", "duplicate_body",
                    f"`{node.name}` appears to be a duplicate of "
                    f"`{body_hashes[h]}`",
                    node.lineno,
                ))
            else:
                body_hashes[h] = node.name

    # ── Batch review ───────────────────────────────────────────────────────

    def review_directory(self, src_dir: Path) -> list[ReviewResult]:
        results = []
        for py in src_dir.rglob("*.py"):
            if "__pycache__" in str(py):
                continue
            results.append(self.review_file(py))
        return results

    def summary_report(self, results: list[ReviewResult]) -> str:
        errors   = sum(1 for r in results for i in r.issues if i.severity == "error")
        warnings = sum(1 for r in results for i in r.issues if i.severity == "warning")
        avg_score = sum(r.score for r in results) / max(len(results), 1)
        passed   = sum(1 for r in results if r.passed)
        lines = [
            "# Peer Review Summary",
            f"- Files reviewed: **{len(results)}**",
            f"- Passed: **{passed}/{len(results)}**",
            f"- Errors: **{errors}** | Warnings: **{warnings}**",
            f"- Average score: **{avg_score:.0f}/100**",
            "",
        ]
        for r in sorted(results, key=lambda x: x.score):
            if r.issues:
                lines.append(f"### {r.file} (score: {r.score})")
                for issue in r.issues:
                    prefix = "❌" if issue.severity == "error" else "⚠" if issue.severity == "warning" else "ℹ"
                    loc = f" (line {issue.line})" if issue.line else ""
                    lines.append(f"- {prefix} [{issue.rule}] {issue.message}{loc}")
                lines.append("")
        return "\n".join(lines)


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    reviewer = PeerReviewer()
    src = Path(__file__).parent.parent
    results = reviewer.review_directory(src)
    report = reviewer.summary_report(results)
    out = src.parent / "logs" / "peer_review_report.md"
    out.write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport saved to {out}")
