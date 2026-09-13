"""
CLI integration tests for contractguard.
"""

from pathlib import Path
import subprocess
import sys

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_cli_diff_breaking_exits_1():
    base = FIXTURES_DIR / "v1_base.json"
    head = FIXTURES_DIR / "v2_breaking.json"
    res = subprocess.run(
        [sys.executable, "-m", "contract_guard.cli", "diff", "--base", str(base), "--head", str(head)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 1
    assert "BREAKING CHANGES DETECTED" in res.stdout


def test_cli_diff_additive_exits_0():
    base = FIXTURES_DIR / "v1_base.json"
    head = FIXTURES_DIR / "v2_additive.json"
    res = subprocess.run(
        [sys.executable, "-m", "contract_guard.cli", "diff", "--base", str(base), "--head", str(head)],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert res.returncode == 0
    assert "NO BREAKING CHANGES" in res.stdout

