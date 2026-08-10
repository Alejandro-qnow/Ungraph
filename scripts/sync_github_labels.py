#!/usr/bin/env python3
"""
Create or update GitHub issue labels (aligned with docs/DEVELOPMENT_WORKFLOW.md).

Requires GitHub CLI: https://cli.github.com/
  gh auth login
  cd repo && python scripts/sync_github_labels.py

Uses `gh label create ... --force` so existing labels get updated.
"""

from __future__ import annotations

import subprocess
import sys

# name, color (hex without #), description
LABELS: list[tuple[str, str, str]] = [
    ("feature", "0E8A16", "New capability / product work"),
    ("fix", "D73A4A", "Bug or regression"),
    ("chore", "FEF2C0", "Maintenance, deps, tooling"),
    ("docs", "0075CA", "Documentation"),
    ("research", "D4C5F9", "Spike / exploration"),
    ("test", "FBCA04", "Test harness / coverage"),
    ("triage", "EDEDED", "Needs classification"),
]


def main() -> int:
    for name, color, desc in LABELS:
        cmd = [
            "gh",
            "label",
            "create",
            name,
            "--color",
            color,
            "--description",
            desc,
            "--force",
        ]
        try:
            subprocess.run(cmd, check=True)
        except FileNotFoundError:
            print("Install GitHub CLI: https://cli.github.com/", file=sys.stderr)
            return 1
        except subprocess.CalledProcessError as e:
            print(f"Failed: {e}", file=sys.stderr)
            return e.returncode
    print(f"Synced {len(LABELS)} labels.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
