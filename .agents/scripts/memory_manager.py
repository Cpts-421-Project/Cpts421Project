#!/usr/bin/env python3
"""
Self-Correcting Memory Manager & Knowledge Graph Auditor.

Enforces the 4 pillars of the project's continuous memory architecture:
1. Ever-Expanding: Validates tiered deep-memory nodes (.agents/memory/*.md) & archive.
2. Self-Correcting: Detects and auto-heals (--fix) broken workspace file:// links.
3. Well-Connected: Verifies bidirectional links between MEMORY.md, rules, and deep nodes.
4. Efficient & Accurate: Enforces hot-memory line/cycle budgets and 100% file mapping.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
from dataclasses import asdict, dataclass, field
from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Set, Tuple

REQUIRED_SECTIONS: Tuple[str, ...] = (
    "## [SYSTEM STATE]",
    "## [KNOWLEDGE GRAPH & DEEP MEMORY NODES]",
    "## [PRODUCTION STRUCTURE]",
    "## [DOMAIN CONNECTIVITY MATRIX]",
    "## [RECENT CHANGES]",
    "## [ACTIVE BACKLOG]",
)

MAX_HOT_MEMORY_LINES: int = 260
MAX_RECENT_CYCLES: int = 3

MARKDOWN_LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")
LINE_ANCHOR_RE = re.compile(r"^L(\d+)(?:-L?(\d+))?$")
CYCLE_HEADER_RE = re.compile(r"^\s*-\s*\*\*Cycle\s+(\d+)\b", re.MULTILINE)


@dataclass(frozen=True)
class LinkIssue:
    source_file: str
    raw_url: str
    reason: str
    repaired_url: Optional[str] = None


@dataclass
class MemoryHealthReport:
    healthy: bool = True
    hot_memory_lines: int = 0
    max_hot_memory_lines: int = MAX_HOT_MEMORY_LINES
    recent_cycle_count: int = 0
    max_recent_cycles: int = MAX_RECENT_CYCLES
    verified_links_count: int = 0
    healed_links_count: int = 0
    mapped_production_files_count: int = 0
    connected_memory_nodes_count: int = 0
    connected_rules_count: int = 0
    missing_sections: List[str] = field(default_factory=list)
    efficiency_warnings: List[str] = field(default_factory=list)
    broken_links: List[LinkIssue] = field(default_factory=list)
    unmapped_files: List[str] = field(default_factory=list)
    orphaned_memory_nodes: List[str] = field(default_factory=list)
    disconnected_memory_nodes: List[str] = field(default_factory=list)
    unmapped_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class MemoryAuditor:
    """Audits and self-heals the tiered project memory graph."""

    def __init__(self, repo_root: Path) -> None:
        if "\x00" in str(repo_root):
            raise ValueError("Null byte detected in repository root path.")
        self.repo_root: Path = repo_root.resolve()
        self.memory_hub_path: Path = self.repo_root / "MEMORY.md"
        self.memory_dir: Path = self.repo_root / ".agents" / "memory"
        self.rules_dir: Path = self.repo_root / ".agents" / "rules"
        self.repo_name: str = self.repo_root.name

    def _encode_repo_file_url(self, rel_posix_path: str, anchor: str = "") -> str:
        """Builds a canonical file:// URL for a repository-relative POSIX path."""
        clean_rel = rel_posix_path.lstrip("/")
        full_posix = f"{self.repo_root.as_posix()}/{clean_rel}"
        encoded_path = urllib.parse.quote(full_posix, safe="/:._-")
        if anchor:
            return f"file://{encoded_path}#{anchor}"
        return f"file://{encoded_path}"

    def _extract_section(self, content: str, header: str) -> str:
        """Extracts markdown text belonging to a specific ## [...] section."""
        idx = content.find(header)
        if idx == -1:
            return ""
        start = idx + len(header)
        next_header = re.search(r"^## \[", content[start:], flags=re.MULTILINE)
        if next_header:
            return content[start : start + next_header.start()]
        return content[start:]

    def audit_sections_and_efficiency(
        self, content: str, report: MemoryHealthReport
    ) -> None:
        """Verifies required sections, line budget, and recent-cycle compaction window."""
        lines = content.splitlines()
        report.hot_memory_lines = len(lines)

        if report.hot_memory_lines > MAX_HOT_MEMORY_LINES:
            report.healthy = False
            report.efficiency_warnings.append(
                f"MEMORY.md has {report.hot_memory_lines} lines "
                f"(exceeds budget of {MAX_HOT_MEMORY_LINES}). Compact into .agents/memory/."
            )

        for section in REQUIRED_SECTIONS:
            if section not in content:
                report.healthy = False
                report.missing_sections.append(section)

        recent_section = self._extract_section(content, "## [RECENT CHANGES]")
        cycles = CYCLE_HEADER_RE.findall(recent_section)
        report.recent_cycle_count = len(cycles)
        if report.recent_cycle_count > MAX_RECENT_CYCLES:
            report.healthy = False
            report.efficiency_warnings.append(
                f"[RECENT CHANGES] contains {report.recent_cycle_count} cycles "
                f"(max {MAX_RECENT_CYCLES}). Archive older cycles to .agents/memory/archive.md."
            )
        elif report.recent_cycle_count == 0 and "## [RECENT CHANGES]" in content:
            report.healthy = False
            report.efficiency_warnings.append(
                "[RECENT CHANGES] contains 0 cycle entries."
            )

    def _resolve_and_validate_link(
        self, source_file: Path, raw_url: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates a single markdown link target.
        Returns (is_valid, error_reason, repaired_url_if_healable).
        """
        if "\x00" in raw_url:
            return False, "Null byte in URL", None

        if raw_url.startswith(("http://", "https://", "mailto:", "conversation://")):
            return True, None, None

        if raw_url.startswith("#"):
            return True, None, None

        anchor = ""
        url_without_anchor = raw_url
        if "#" in raw_url:
            url_without_anchor, anchor = raw_url.split("#", 1)

        if url_without_anchor.startswith("file://"):
            parsed = urllib.parse.urlparse(url_without_anchor)
            unquoted_path = urllib.parse.unquote(parsed.path)

            if "\x00" in unquoted_path or ".." in PurePosixPath(unquoted_path).parts:
                return False, "Path traversal or null byte in file:// URL", None

            marker = f"/{self.repo_name}/"
            if marker in unquoted_path:
                rel_part = unquoted_path.split(marker, 1)[1]
                target_path = (self.repo_root / rel_part).resolve()
                try:
                    target_path.relative_to(self.repo_root)
                except ValueError:
                    return False, "Resolved path escapes repository root", None

                if not target_path.exists():
                    return False, f"Target file does not exist: {rel_part}", None

                return self._validate_anchor(target_path, anchor)

            # Check if this is a broken workspace link missing the repo_name segment
            parent_name = self.repo_root.parent.name
            broken_marker = f"/{parent_name}/"
            if broken_marker in unquoted_path:
                candidate_rel = unquoted_path.split(broken_marker, 1)[1]
                candidate_target = (self.repo_root / candidate_rel).resolve()
                try:
                    candidate_target.relative_to(self.repo_root)
                except ValueError:
                    return False, "Candidate path escapes repository root", None

                if candidate_target.exists():
                    healed_url = self._encode_repo_file_url(candidate_rel, anchor)
                    return (
                        False,
                        f"Missing '/{self.repo_name}/' in workspace file:// path",
                        healed_url,
                    )

            return (
                False,
                f"External or non-existent file:// path outside repository: {unquoted_path}",
                None,
            )

        # Relative file link
        unquoted_rel = urllib.parse.unquote(url_without_anchor)
        if "\x00" in unquoted_rel or unquoted_rel.startswith("~"):
            return False, "Invalid characters in relative path", None

        resolved = (source_file.parent / unquoted_rel).resolve()
        try:
            resolved.relative_to(self.repo_root)
        except ValueError:
            return False, f"Relative link escapes repository root: {raw_url}", None

        if not resolved.exists():
            return False, f"Relative link target does not exist: {raw_url}", None

        return self._validate_anchor(resolved, anchor)

    def _validate_anchor(
        self, target_path: Path, anchor: str
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validates #L<start>-L<end> line range anchors against actual file length."""
        if not anchor or not target_path.is_file():
            return True, None, None

        match = LINE_ANCHOR_RE.match(anchor)
        if not match:
            return True, None, None

        start_line = int(match.group(1))
        end_line = int(match.group(2)) if match.group(2) else start_line
        if start_line < 1 or end_line < start_line:
            return False, f"Invalid line range #{anchor}", None

        try:
            total_lines = len(
                target_path.read_text(encoding="utf-8", errors="replace").splitlines()
            )
        except OSError as exc:
            return False, f"Unable to read target file for line check: {exc}", None

        if end_line > max(total_lines, 1):
            return (
                False,
                f"Line anchor #{anchor} exceeds file length ({total_lines} lines)",
                None,
            )
        return True, None, None

    def audit_and_heal_links(
        self, report: MemoryHealthReport, auto_fix: bool = False
    ) -> None:
        """Scans MEMORY.md, .agents/memory/*.md, and .agents/rules/*.md for link accuracy."""
        files_to_scan: List[Path] = []
        if self.memory_hub_path.exists():
            files_to_scan.append(self.memory_hub_path)
        if self.memory_dir.exists():
            files_to_scan.extend(sorted(self.memory_dir.glob("*.md")))
        if self.rules_dir.exists():
            files_to_scan.extend(sorted(self.rules_dir.glob("*.md")))

        for md_file in files_to_scan:
            original_text = md_file.read_text(encoding="utf-8")
            updated_text = original_text
            rel_source = md_file.relative_to(self.repo_root).as_posix()

            for match in MARKDOWN_LINK_RE.finditer(original_text):
                raw_url = match.group(2)
                is_valid, reason, repaired_url = self._resolve_and_validate_link(
                    md_file, raw_url
                )
                if is_valid:
                    report.verified_links_count += 1
                else:
                    if auto_fix and repaired_url:
                        updated_text = updated_text.replace(
                            f"]({raw_url})", f"]({repaired_url})"
                        )
                        report.healed_links_count += 1
                        report.verified_links_count += 1
                    else:
                        report.healthy = False
                        report.broken_links.append(
                            LinkIssue(
                                source_file=rel_source,
                                raw_url=raw_url,
                                reason=reason or "Invalid link",
                                repaired_url=repaired_url,
                            )
                        )

            if auto_fix and updated_text != original_text:
                md_file.write_text(updated_text, encoding="utf-8")

    def audit_knowledge_graph(
        self, hub_content: str, report: MemoryHealthReport
    ) -> None:
        """Verifies bidirectional links between MEMORY.md, .agents/memory/*.md, and .agents/rules/*.md."""
        if self.memory_dir.exists():
            for node_file in sorted(self.memory_dir.glob("*.md")):
                rel_node = node_file.relative_to(self.repo_root).as_posix()
                if rel_node not in hub_content and node_file.name not in hub_content:
                    report.healthy = False
                    report.orphaned_memory_nodes.append(rel_node)
                else:
                    report.connected_memory_nodes_count += 1

                node_text = node_file.read_text(encoding="utf-8")
                if "MEMORY.md" not in node_text:
                    report.healthy = False
                    report.disconnected_memory_nodes.append(rel_node)

        if self.rules_dir.exists():
            for rule_file in sorted(self.rules_dir.glob("*.md")):
                rel_rule = rule_file.relative_to(self.repo_root).as_posix()
                if rel_rule not in hub_content and rule_file.name not in hub_content:
                    report.healthy = False
                    report.unmapped_rules.append(rel_rule)
                else:
                    report.connected_rules_count += 1

    def _discover_production_files(self) -> List[str]:
        """Discovers active source, test, and CI workflow files that MUST be mapped in MEMORY.md."""
        scan_specs: List[Tuple[str, Tuple[str, ...]]] = [
            ("code/backend/src", (".py", ".sql")),
            ("code/backend/datacollection", (".py",)),
            ("code/backend/tests", (".py",)),
            ("code/frontend/src", (".js", ".jsx", ".css")),
            (".github/workflows", (".yml",)),
        ]
        discovered: List[str] = []
        for base_rel, suffixes in scan_specs:
            base_dir = self.repo_root / base_rel
            if not base_dir.exists():
                continue
            for path in sorted(base_dir.rglob("*")):
                if not path.is_file():
                    continue
                if "__pycache__" in path.parts or "assets" in path.parts:
                    continue
                if path.name == "__init__.py":
                    continue
                if path.suffix in suffixes:
                    discovered.append(path.relative_to(self.repo_root).as_posix())
        return discovered

    def audit_production_structure(
        self, hub_content: str, report: MemoryHealthReport
    ) -> None:
        """Ensures 100% of active source, test, and workflow files are mapped in MEMORY.md."""
        unquoted_hub = urllib.parse.unquote(hub_content)
        production_files = self._discover_production_files()

        for rel_path in production_files:
            if rel_path in unquoted_hub:
                report.mapped_production_files_count += 1
            else:
                report.healthy = False
                report.unmapped_files.append(rel_path)

    def run_audit(self, auto_fix: bool = False) -> MemoryHealthReport:
        """Executes the full memory health audit (and optional self-healing pass)."""
        report = MemoryHealthReport()

        if not self.memory_hub_path.exists():
            report.healthy = False
            report.missing_sections.append("MEMORY.md (file missing)")
            return report

        self.audit_and_heal_links(report, auto_fix=auto_fix)

        hub_content = self.memory_hub_path.read_text(encoding="utf-8")
        self.audit_sections_and_efficiency(hub_content, report)
        self.audit_knowledge_graph(hub_content, report)
        self.audit_production_structure(hub_content, report)

        return report


def format_report(report: MemoryHealthReport) -> str:
    """Formats a human-readable summary of the memory health audit."""
    status = "HEALTHY (100% Connected & Verified)" if report.healthy else "DRIFT DETECTED"
    lines = [
        f"=== MEMORY SYSTEM INTEGRITY REPORT: {status} ===",
        f"Hot Memory Size       : {report.hot_memory_lines}/{report.max_hot_memory_lines} lines",
        f"Recent Cycles Window  : {report.recent_cycle_count}/{report.max_recent_cycles} cycles",
        f"Verified Links        : {report.verified_links_count} (Auto-Healed: {report.healed_links_count})",
        f"Mapped Prod/Test Files: {report.mapped_production_files_count}",
        f"Connected Deep Nodes  : {report.connected_memory_nodes_count}",
        f"Connected System Rules: {report.connected_rules_count}",
    ]

    if report.missing_sections:
        lines.append("\n[!] Missing Required Sections:")
        for sec in report.missing_sections:
            lines.append(f"  - {sec}")

    if report.efficiency_warnings:
        lines.append("\n[!] Efficiency & Compaction Warnings:")
        for warn in report.efficiency_warnings:
            lines.append(f"  - {warn}")

    if report.broken_links:
        lines.append("\n[!] Broken or Unverified Links:")
        for issue in report.broken_links:
            fix_hint = f" -> Fixable: {issue.repaired_url}" if issue.repaired_url else ""
            lines.append(
                f"  - [{issue.source_file}] {issue.raw_url} ({issue.reason}){fix_hint}"
            )

    if report.unmapped_files:
        lines.append("\n[!] Unmapped Production/Test Files (Missing from MEMORY.md):")
        for path in report.unmapped_files:
            lines.append(f"  - {path}")

    if report.orphaned_memory_nodes:
        lines.append("\n[!] Orphaned Deep Memory Nodes (Not linked in MEMORY.md):")
        for node in report.orphaned_memory_nodes:
            lines.append(f"  - {node}")

    if report.disconnected_memory_nodes:
        lines.append("\n[!] Disconnected Memory Nodes (Missing backlink to MEMORY.md):")
        for node in report.disconnected_memory_nodes:
            lines.append(f"  - {node}")

    if report.unmapped_rules:
        lines.append("\n[!] Unmapped System Rules (Not referenced in MEMORY.md):")
        for rule in report.unmapped_rules:
            lines.append(f"  - {rule}")

    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit and self-heal the project's tiered memory system."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Path to the repository root.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Automatically heal broken workspace file:// links in memory files.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the audit report as structured JSON.",
    )
    args = parser.parse_args(argv)

    auditor = MemoryAuditor(repo_root=args.repo_root)
    report = auditor.run_audit(auto_fix=args.fix)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(format_report(report))

    return 0 if report.healthy else 1


if __name__ == "__main__":
    sys.exit(main())

