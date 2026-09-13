"""
Data models for ContractGuard changes, severities, and diff results.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, List, Optional


class Severity(str, Enum):
    BREAKING = "BREAKING"
    WARNING = "WARNING"
    INFO = "INFO"


class ChangeCategory(str, Enum):
    ENDPOINT_REMOVED = "ENDPOINT_REMOVED"
    ENDPOINT_ADDED = "ENDPOINT_ADDED"
    METHOD_REMOVED = "METHOD_REMOVED"
    METHOD_ADDED = "METHOD_ADDED"
    OPERATION_DEPRECATED = "OPERATION_DEPRECATED"

    PARAM_REMOVED = "PARAM_REMOVED"
    PARAM_REQUIRED_ADDED = "PARAM_REQUIRED_ADDED"
    PARAM_OPTIONAL_ADDED = "PARAM_OPTIONAL_ADDED"
    PARAM_TYPE_CHANGED = "PARAM_TYPE_CHANGED"
    PARAM_REQUIRED_CHANGED = "PARAM_REQUIRED_CHANGED"

    REQUEST_BODY_REQUIRED_CHANGED = "REQUEST_BODY_REQUIRED_CHANGED"
    REQUEST_BODY_REMOVED = "REQUEST_BODY_REMOVED"
    REQUEST_PROPERTY_REMOVED = "REQUEST_PROPERTY_REMOVED"
    REQUEST_PROPERTY_REQUIRED_ADDED = "REQUEST_PROPERTY_REQUIRED_ADDED"
    REQUEST_PROPERTY_TYPE_CHANGED = "REQUEST_PROPERTY_TYPE_CHANGED"
    REQUEST_PROPERTY_OPTIONAL_ADDED = "REQUEST_PROPERTY_OPTIONAL_ADDED"

    RESPONSE_STATUS_REMOVED = "RESPONSE_STATUS_REMOVED"
    RESPONSE_STATUS_ADDED = "RESPONSE_STATUS_ADDED"
    RESPONSE_PROPERTY_REMOVED = "RESPONSE_PROPERTY_REMOVED"
    RESPONSE_PROPERTY_TYPE_CHANGED = "RESPONSE_PROPERTY_TYPE_CHANGED"
    RESPONSE_PROPERTY_ADDED = "RESPONSE_PROPERTY_ADDED"


@dataclass
class Change:
    category: ChangeCategory
    severity: Severity
    path: str
    method: str
    location: str
    description: str
    old_value: Any = None
    new_value: Any = None


@dataclass
class DiffResult:
    changes: List[Change] = field(default_factory=list)
    base_title: Optional[str] = None
    base_version: Optional[str] = None
    head_title: Optional[str] = None
    head_version: Optional[str] = None

    @property
    def breaking_changes(self) -> List[Change]:
        return [c for c in self.changes if c.severity == Severity.BREAKING]

    @property
    def warnings(self) -> List[Change]:
        return [c for c in self.changes if c.severity == Severity.WARNING]

    @property
    def info_changes(self) -> List[Change]:
        return [c for c in self.changes if c.severity == Severity.INFO]

    @property
    def is_breaking(self) -> bool:
        return len(self.breaking_changes) > 0

    @property
    def total_changes(self) -> int:
        return len(self.changes)
