"""Diff Generator for Software Engineer Agent.

Generates unified diffs for code changes.
"""

from typing import Any
from dataclasses import dataclass

from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DiffHunk:
    """Single diff hunk."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: list[str]


@dataclass
class Diff:
    """Complete diff result."""

    file_path: str
    old_content: str
    new_content: str
    hunks: list[DiffHunk]
    stats: dict[str, int]
    is_new_file: bool


class DiffGenerator:
    """Generates unified diffs for code changes."""

    def __init__(self):
        """Initialize diff generator."""

    def generate(
        self,
        file_path: str,
        old_content: str,
        new_content: str,
    ) -> Diff:
        """Generate unified diff.

        Args:
            file_path: Path to file.
            old_content: Original content.
            new_content: New content.

        Returns:
            Diff result.
        """
        logger.info("Generating diff for %s", file_path)

        is_new_file = not old_content

        if is_new_file:
            hunks = self._generate_new_file_hunks(new_content)
        else:
            hunks = self._compute_diff(old_content, new_content)

        stats = self._compute_stats(old_content, new_content, hunks)

        return Diff(
            file_path=file_path,
            old_content=old_content,
            new_content=new_content,
            hunks=hunks,
            stats=stats,
            is_new_file=is_new_file,
        )

    def _generate_new_file_hunks(self, content: str) -> list[DiffHunk]:
        """Generate hunks for new file."""
        lines = content.split("\n")
        return [
            DiffHunk(
                old_start=0,
                old_count=0,
                new_start=1,
                new_count=len(lines),
                lines=[f"+{line}" for line in lines],
            )
        ]

    def _compute_diff(
        self,
        old_content: str,
        new_content: str,
    ) -> list[DiffHunk]:
        """Compute diff hunks using LCS algorithm."""
        old_lines = old_content.split("\n")
        new_lines = new_content.split("\n")

        # LCS matrix
        m, n = len(old_lines), len(new_lines)
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if old_lines[i - 1] == new_lines[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1] + 1
                else:
                    dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])

        # Backtrack to find diff
        hunks = []
        current_hunk_lines = []
        hunk_start_old = 1
        hunk_start_new = 1
        i, j = m, n

        changes = []
        while i > 0 or j > 0:
            if i > 0 and j > 0 and old_lines[i - 1] == new_lines[j - 1]:
                if current_hunk_lines:
                    hunks.append(self._create_hunk(
                        hunk_start_old, hunk_start_new,
                        current_hunk_lines
                    ))
                    current_hunk_lines = []
                i -= 1
                j -= 1
                hunk_start_old = i + 1
                hunk_start_new = j + 1
            elif j > 0 and (i == 0 or dp[i][j - 1] >= dp[i - 1][j]):
                current_hunk_lines.append(f"+{new_lines[j - 1]}")
                j -= 1
            else:
                current_hunk_lines.append(f"-{old_lines[i - 1]}")
                i -= 1

        if current_hunk_lines:
            hunks.append(self._create_hunk(
                hunk_start_old, hunk_start_new,
                current_hunk_lines
            ))

        return list(reversed(hunks))

    def _create_hunk(
        self,
        old_start: int,
        new_start: int,
        lines: list[str],
    ) -> DiffHunk:
        """Create diff hunk."""
        old_count = sum(1 for l in lines if l.startswith("-") or l.startswith(" "))
        new_count = sum(1 for l in lines if l.startswith("+") or l.startswith(" "))

        return DiffHunk(
            old_start=old_start,
            old_count=old_count,
            new_start=new_start,
            new_count=new_count,
            lines=lines,
        )

    def _compute_stats(
        self,
        old_content: str,
        new_content: str,
        hunks: list[DiffHunk],
    ) -> dict[str, int]:
        """Compute diff statistics."""
        additions = 0
        deletions = 0

        for hunk in hunks:
            for line in hunk.lines:
                if line.startswith("+"):
                    additions += 1
                elif line.startswith("-"):
                    deletions += 1

        return {
            "additions": additions,
            "deletions": deletions,
            "changes": additions + deletions,
        }

    def format_unified_diff(self, diff: Diff) -> str:
        """Format diff as unified diff string."""
        lines = []
        lines.append(f"--- a/{diff.file_path}")
        lines.append(f"+++ b/{diff.file_path}")

        for hunk in diff.hunks:
            lines.append(
                f"@@ -{hunk.old_start},{hunk.old_count} "
                f"+{hunk.new_start},{hunk.new_count} @@"
            )
            lines.extend(hunk.lines)

        return "\n".join(lines)

    def format_readable_diff(self, diff: Diff) -> str:
        """Format diff as readable string."""
        lines = []
        lines.append(f"=== Changes to {diff.file_path} ===")
        lines.append(f"Additions: {diff.stats['additions']}")
        lines.append(f"Deletions: {diff.stats['deletions']}")
        lines.append("")

        for hunk in diff.hunks:
            lines.append(f"@@ Lines {hunk.new_start}-{hunk.new_start + hunk.new_count} @@")
            for line in hunk.lines:
                if line.startswith("+"):
                    lines.append(f"\033[32m{line}\033[0m")
                elif line.startswith("-"):
                    lines.append(f"\033[31m{line}\033[0m")
                else:
                    lines.append(line)
            lines.append("")

        return "\n".join(lines)
