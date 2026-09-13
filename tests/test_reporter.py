"""
Unit tests for Terminal, Markdown, and SARIF reporters.
"""

from pathlib import Path
import json
from contract_guard.comparator import ContractComparator
from contract_guard.parser import OpenAPISpec, load_spec_from_file
from contract_guard.reporter import MarkdownReporter, SarifReporter, TerminalReporter

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_terminal_reporter():
    base = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v1_base.json"))
    head = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v2_breaking.json"))
    result = ContractComparator(base, head).compare()

    output = TerminalReporter().render(result)
    assert "BREAKING CHANGES DETECTED" in output
    assert "User Commerce API" in output


def test_markdown_reporter():
    base = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v1_base.json"))
    head = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v2_breaking.json"))
    result = ContractComparator(base, head).compare()

    md = MarkdownReporter().render(result)
    assert "ContractGuard API Contract Review" in md
    assert "BREAKING CHANGES DETECTED" in md
    assert "| Method | Endpoint | Location | Description |" in md


def test_sarif_reporter():
    base = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v1_base.json"))
    head = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v2_breaking.json"))
    result = ContractComparator(base, head).compare()

    sarif_str = SarifReporter().render(result)
    sarif_data = json.loads(sarif_str)
    assert sarif_data["version"] == "2.1.0"
    assert sarif_data["runs"][0]["tool"]["driver"]["name"] == "ContractGuard"
    assert len(sarif_data["runs"][0]["results"]) >= 4
