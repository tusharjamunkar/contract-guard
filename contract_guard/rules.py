"""
Classification rules defining what constitutes a BREAKING, WARNING, or ADDITIVE change.
"""

from typing import Any
from .models import Change, ChangeCategory, Severity


def create_change(
    category: ChangeCategory,
    path: str,
    method: str,
    location: str,
    description: str,
    old_value: Any = None,
    new_value: Any = None,
) -> Change:
    breaking_categories = {
        ChangeCategory.ENDPOINT_REMOVED,
        ChangeCategory.METHOD_REMOVED,
        ChangeCategory.PARAM_REMOVED,
        ChangeCategory.PARAM_REQUIRED_ADDED,
        ChangeCategory.PARAM_TYPE_CHANGED,
        ChangeCategory.PARAM_REQUIRED_CHANGED,
        ChangeCategory.REQUEST_BODY_REQUIRED_CHANGED,
        ChangeCategory.REQUEST_BODY_REMOVED,
        ChangeCategory.REQUEST_PROPERTY_REMOVED,
        ChangeCategory.REQUEST_PROPERTY_REQUIRED_ADDED,
        ChangeCategory.REQUEST_PROPERTY_TYPE_CHANGED,
        ChangeCategory.RESPONSE_STATUS_REMOVED,
        ChangeCategory.RESPONSE_PROPERTY_REMOVED,
        ChangeCategory.RESPONSE_PROPERTY_TYPE_CHANGED,
    }

    warning_categories = {
        ChangeCategory.OPERATION_DEPRECATED,
    }

    if category in breaking_categories:
        severity = Severity.BREAKING
    elif category in warning_categories:
        severity = Severity.WARNING
    else:
        severity = Severity.INFO

    return Change(
        category=category,
        severity=severity,
        path=path,
        method=method.upper(),
        location=location,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )
