"""Build and publish the public SwerveSite stats snapshot.

This script is intended to run from a local checkout of SwerveSite after a stream
has been validated. It deliberately publishes only data/stats.json.

Requirements:
- The repository must already be cloned locally.
- Git authentication must already be configured for `git push`.
- SWERVE_DB_PASSWORD must be present in the environment for build_stats.py.
- The current Git branch must match SWERVE_SITE_BRANCH (default: swerve-2.0).

No GitHub token or database credential is stored in this repository.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATS_FILE = ROOT / "data" / "stats.json"
BUILD_SCRIPT = ROOT / "tools" / "build_stats.py"
EXPECTED_BRANCH = os.environ.get("SWERVE_SITE_BRANCH", "swerve-2.0")


def run(*args: str, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=capture,
    )


def current_branch() -> str:
    result = run("git", "branch", "--show-current", capture=True)
    return result.stdout.strip()


def validate_snapshot() -> dict:
    if not STATS_FILE.exists():
        raise RuntimeError(f"Stats snapshot was not created: {STATS_FILE}")

    payload = json.loads(STATS_FILE.read_text(encoding="utf-8"))

    required = ("generated_at", "latest_stream", "streak_leaders", "all_time")
    missing = [key for key in required if key not in payload]
    if missing:
        raise RuntimeError(
            "Generated stats snapshot is missing required keys: "
            + ", ".join(missing)
        )

    if not payload.get("generated_at"):
        raise RuntimeError("Generated stats snapshot has no generated_at timestamp")

    latest = payload.get("latest_stream") or {}
    if latest.get("stream_id") is None:
        raise RuntimeError("Generated stats snapshot has no latest stream_id")

    return payload


def stats_changed() -> bool:
    result = run(
        "git",
        "status",
        "--porcelain",
        "--",
        "data/stats.json",
        capture=True,
    )
    return bool(result.stdout.strip())


def main() -> int:
    branch = current_branch()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Refusing to publish from branch '{branch}'. "
            f"Expected '{EXPECTED_BRANCH}'."
        )

    print("Building validated public stats snapshot...")
    run(sys.executable, str(BUILD_SCRIPT))

    payload = validate_snapshot()
    stream_id = payload["latest_stream"]["stream_id"]

    if not stats_changed():
        print("Stats snapshot is already current. Nothing to publish.")
        return 0

    # Explicitly stage only the public stats snapshot. Never use `git add .` here.
    run("git", "add", "--", "data/stats.json")

    commit_message = f"Publish validated stream stats #{stream_id}"
    run("git", "commit", "-m", commit_message, "--", "data/stats.json")
    run("git", "push", "origin", EXPECTED_BRANCH)

    print(f"Published validated stats for stream #{stream_id} to {EXPECTED_BRANCH}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print(f"Publish command failed with exit code {exc.returncode}.", file=sys.stderr)
        raise SystemExit(exc.returncode)
    except Exception as exc:
        print(f"Stats publish failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
