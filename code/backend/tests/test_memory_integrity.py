"""
Unit and Integration Tests for the Self-Correcting Memory System (.agents/scripts/memory_manager.py).

Follows test-rule.md:
- Arrange, Act, Assert (AAA) pattern.
- Normal, Edge, and Extraordinary test coverage.
- Isolated temporary workspaces (tmp_path) for mutation/failure tests plus live repository verification.
"""

import importlib.util
import sys
import urllib.parse
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = REPO_ROOT / ".agents" / "scripts" / "memory_manager.py"

spec = importlib.util.spec_from_file_location("memory_manager", SCRIPT_PATH)
memory_manager = importlib.util.module_from_spec(spec)
sys.modules["memory_manager"] = memory_manager
spec.loader.exec_module(memory_manager)

MemoryAuditor = memory_manager.MemoryAuditor
MAX_HOT_MEMORY_LINES = memory_manager.MAX_HOT_MEMORY_LINES
MAX_RECENT_CYCLES = memory_manager.MAX_RECENT_CYCLES
REQUIRED_SECTIONS = memory_manager.REQUIRED_SECTIONS


def _create_minimal_healthy_workspace(root: Path) -> Path:
    """Helper to scaffold an isolated synthetic repository with a connected memory graph."""
    repo = root / "Cpts421Project"
    (repo / ".agents" / "memory").mkdir(parents=True)
    (repo / ".agents" / "rules").mkdir(parents=True)
    (repo / "code" / "backend" / "src").mkdir(parents=True)

    main_py = repo / "code" / "backend" / "src" / "main.py"
    main_py.write_text("def app():\n    return True\n", encoding="utf-8")

    rule_md = repo / ".agents" / "rules" / "memory-backlog.md"
    rule_md.write_text("# Memory Rule\n", encoding="utf-8")

    encoded_root = urllib.parse.quote(repo.as_posix(), safe="/:._-")
    node_md = repo / ".agents" / "memory" / "architecture_and_infra.md"
    node_md.write_text(
        f"# Architecture\nConnected to [MEMORY.md](file://{encoded_root}/MEMORY.md)\n",
        encoding="utf-8",
    )

    memory_md = repo / "MEMORY.md"
    memory_md.write_text(
        "\n".join(
            [
                "# PROJECT MEMORY",
                "## [SYSTEM STATE]",
                f"- Rule: [memory-backlog.md](file://{encoded_root}/.agents/rules/memory-backlog.md)",
                "## [KNOWLEDGE GRAPH & DEEP MEMORY NODES]",
                f"- Node: [architecture_and_infra.md](file://{encoded_root}/.agents/memory/architecture_and_infra.md)",
                "## [PRODUCTION STRUCTURE]",
                f"- Backend: [main.py](file://{encoded_root}/code/backend/src/main.py#L1-L2)",
                "## [DOMAIN CONNECTIVITY MATRIX]",
                "- Core API -> code/backend/src/main.py",
                "## [RECENT CHANGES]",
                "- **Cycle 1 (Initial Setup):** Created main.py.",
                "## [ACTIVE BACKLOG]",
                "- None.",
            ]
        ),
        encoding="utf-8",
    )
    return repo


class TestMemorySystemNormalCases:
    """Normal Cases (Happy Path): Verify live repository and standard valid workspaces."""

    def test_liveRepositoryMemoryGraph_audit_isCompletelyHealthy(self):
        # Arrange
        if not (REPO_ROOT / "MEMORY.md").exists():
            pytest.skip("Repository root MEMORY.md not mounted in isolated container")
        auditor = MemoryAuditor(repo_root=REPO_ROOT)

        # Act
        report = auditor.run_audit(auto_fix=False)

        # Assert
        assert report.healthy is True, memory_manager.format_report(report)
        assert report.missing_sections == []
        assert report.broken_links == []
        assert report.unmapped_files == []
        assert report.orphaned_memory_nodes == []
        assert report.disconnected_memory_nodes == []
        assert report.unmapped_rules == []
        assert report.hot_memory_lines <= MAX_HOT_MEMORY_LINES
        assert 1 <= report.recent_cycle_count <= MAX_RECENT_CYCLES

    def test_runAudit_withValidSyntheticWorkspace_returnsHealthyReport(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)

        # Act
        report = auditor.run_audit(auto_fix=False)

        # Assert
        assert report.healthy is True
        assert report.verified_links_count == 4
        assert report.mapped_production_files_count == 1
        assert report.connected_memory_nodes_count == 1
        assert report.connected_rules_count == 1


class TestMemorySystemEdgeCases:
    """Edge Cases (Boundary Conditions): Limits on cycles, lines, anchors, and spaces."""

    def test_auditSectionsAndEfficiency_atExactCycleLimitBoundary_shiftsFromTrueToFalse(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)
        base_text = (workspace / "MEMORY.md").read_text(encoding="utf-8")

        three_cycles = base_text.replace(
            "- **Cycle 1 (Initial Setup):** Created main.py.",
            "\n".join(
                [f"- **Cycle {i} (Step):** Done." for i in range(1, MAX_RECENT_CYCLES + 1)]
            ),
        )
        four_cycles = base_text.replace(
            "- **Cycle 1 (Initial Setup):** Created main.py.",
            "\n".join(
                [f"- **Cycle {i} (Step):** Done." for i in range(1, MAX_RECENT_CYCLES + 2)]
            ),
        )

        # Act
        (workspace / "MEMORY.md").write_text(three_cycles, encoding="utf-8")
        report_at_limit = auditor.run_audit()

        (workspace / "MEMORY.md").write_text(four_cycles, encoding="utf-8")
        report_over_limit = auditor.run_audit()

        # Assert
        assert report_at_limit.healthy is True
        assert report_at_limit.recent_cycle_count == MAX_RECENT_CYCLES
        assert report_over_limit.healthy is False
        assert report_over_limit.recent_cycle_count == MAX_RECENT_CYCLES + 1
        assert any("Archive older cycles" in w for w in report_over_limit.efficiency_warnings)

    def test_auditSectionsAndEfficiency_atExactLineBudgetBoundary_shiftsFromTrueToFalse(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)
        base_lines = (workspace / "MEMORY.md").read_text(encoding="utf-8").splitlines()
        padding_needed = MAX_HOT_MEMORY_LINES - len(base_lines)

        exact_budget_text = "\n".join(base_lines + [f"- Item {i}" for i in range(padding_needed)])
        over_budget_text = exact_budget_text + "\n- Extra overflow line"

        # Act
        (workspace / "MEMORY.md").write_text(exact_budget_text, encoding="utf-8")
        report_exact = auditor.run_audit()

        (workspace / "MEMORY.md").write_text(over_budget_text, encoding="utf-8")
        report_over = auditor.run_audit()

        # Assert
        assert report_exact.hot_memory_lines == MAX_HOT_MEMORY_LINES
        assert report_exact.healthy is True
        assert report_over.hot_memory_lines == MAX_HOT_MEMORY_LINES + 1
        assert report_over.healthy is False

    def test_validateAnchor_atExactFileLineBoundaryAndOffByOne_detectsOverflow(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)
        encoded_root = urllib.parse.quote(workspace.as_posix(), safe="/:._-")
        memory_file = workspace / "MEMORY.md"

        # main.py has 2 lines; #L1-L3 is off-by-one beyond EOF
        content_overflow = memory_file.read_text(encoding="utf-8").replace(
            "#L1-L2", "#L1-L3"
        )
        memory_file.write_text(content_overflow, encoding="utf-8")

        # Act
        report = auditor.run_audit()

        # Assert
        assert report.healthy is False
        assert len(report.broken_links) == 1
        assert "exceeds file length (2 lines)" in report.broken_links[0].reason
        assert encoded_root in report.broken_links[0].raw_url


class TestMemorySystemExtraordinaryCases:
    """Extraordinary Cases (Sad Path & Self-Healing): Broken paths, traversal, null bytes, orphans."""

    def test_auditAndHealLinks_withMissingRepoSegmentInFileUrl_autoHealsInPlace(
        self, tmp_path: Path
    ):
        # Arrange
        parent_dir = tmp_path / "space dir"
        workspace = _create_minimal_healthy_workspace(parent_dir)
        auditor = MemoryAuditor(repo_root=workspace)

        encoded_parent = urllib.parse.quote(parent_dir.as_posix(), safe="/:._-")
        broken_url = f"file://{encoded_parent}/code/backend/src/main.py"
        memory_file = workspace / "MEMORY.md"
        memory_file.write_text(
            memory_file.read_text(encoding="utf-8") + f"\n- Broken: [main.py]({broken_url})\n",
            encoding="utf-8",
        )

        # Act
        report_before_fix = auditor.run_audit(auto_fix=False)
        report_after_fix = auditor.run_audit(auto_fix=True)
        report_verified = auditor.run_audit(auto_fix=False)

        # Assert
        assert report_before_fix.healthy is False
        assert len(report_before_fix.broken_links) == 1
        assert report_before_fix.broken_links[0].repaired_url is not None

        assert report_after_fix.healthy is True
        assert report_after_fix.healed_links_count == 1
        assert report_verified.healthy is True
        assert broken_url not in memory_file.read_text(encoding="utf-8")

    def test_memoryAuditor_withNullByteInPathOrLink_rejectsSafely(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)

        # Act & Assert: Null byte in constructor
        with pytest.raises(ValueError, match="Null byte"):
            MemoryAuditor(repo_root=Path("/tmp/bad\x00path"))

        # Act & Assert: Null byte in link
        valid, reason, _ = auditor._resolve_and_validate_link(
            workspace / "MEMORY.md", "file:///tmp/bad%00file.py"
        )
        assert valid is False
        assert "null byte" in reason.lower()

    def test_resolveAndValidateLink_withPathTraversalOutsideRepo_rejectsLink(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        auditor = MemoryAuditor(repo_root=workspace)

        # Act
        valid_rel, reason_rel, _ = auditor._resolve_and_validate_link(
            workspace / "MEMORY.md", "../../etc/passwd"
        )
        valid_file, reason_file, _ = auditor._resolve_and_validate_link(
            workspace / "MEMORY.md",
            f"file://{workspace.as_posix()}/../../etc/passwd",
        )

        # Assert
        assert valid_rel is False
        assert "escapes repository root" in reason_rel
        assert valid_file is False
        assert "traversal" in reason_file.lower()

    def test_runAudit_withUnmappedSourceFileAndOrphanedNode_flagsBothInReport(
        self, tmp_path: Path
    ):
        # Arrange
        workspace = _create_minimal_healthy_workspace(tmp_path)
        unmapped_service = workspace / "code" / "backend" / "src" / "orphan_service.py"
        unmapped_service.write_text("x = 1\n", encoding="utf-8")

        orphan_node = workspace / ".agents" / "memory" / "orphan_node.md"
        orphan_node.write_text("# Disconnected node without hub link\n", encoding="utf-8")

        auditor = MemoryAuditor(repo_root=workspace)

        # Act
        report = auditor.run_audit(auto_fix=False)

        # Assert
        assert report.healthy is False
        assert "code/backend/src/orphan_service.py" in report.unmapped_files
        assert ".agents/memory/orphan_node.md" in report.orphaned_memory_nodes
        assert ".agents/memory/orphan_node.md" in report.disconnected_memory_nodes

