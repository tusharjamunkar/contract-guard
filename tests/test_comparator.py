"""
Unit tests for ContractComparator.
"""

from pathlib import Path
from contract_guard.comparator import ContractComparator
from contract_guard.parser import OpenAPISpec, load_spec_from_file

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_breaking_diff():
    base = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v1_base.json"))
    head = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v2_breaking.json"))

    comparator = ContractComparator(base, head)
    result = comparator.compare()

    assert result.is_breaking is True
    assert len(result.breaking_changes) >= 4

    categories = [c.category.value for c in result.breaking_changes]
    assert "METHOD_REMOVED" in categories
    assert "PARAM_REQUIRED_CHANGED" in categories
    assert "REQUEST_PROPERTY_REQUIRED_ADDED" in categories
    assert "RESPONSE_PROPERTY_REMOVED" in categories


def test_additive_diff():
    base = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v1_base.json"))
    head = OpenAPISpec(load_spec_from_file(FIXTURES_DIR / "v2_additive.json"))

    comparator = ContractComparator(base, head)
    result = comparator.compare()

    assert result.is_breaking is False
    assert len(result.breaking_changes) == 0
    assert len(result.info_changes) >= 3

    categories = [c.category.value for c in result.info_changes]
    assert "ENDPOINT_ADDED" in categories
    assert "PARAM_OPTIONAL_ADDED" in categories
    assert "RESPONSE_PROPERTY_ADDED" in categories
