"""
Core contract difference engine.
"""

from typing import Any, Dict, List, Optional
from .models import Change, ChangeCategory, DiffResult
from .parser import OpenAPISpec
from .rules import create_change

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace"}


class ContractComparator:
    def __init__(self, base_spec: OpenAPISpec, head_spec: OpenAPISpec):
        self.base = base_spec
        self.head = head_spec

    def compare(self) -> DiffResult:
        changes: List[Change] = []
        base_paths = self.base.paths
        head_paths = self.head.paths
        all_paths = set(base_paths.keys()) | set(head_paths.keys())

        for path in sorted(all_paths):
            if path not in head_paths:
                for method, op in base_paths[path].items():
                    if method.lower() in HTTP_METHODS:
                        changes.append(
                            create_change(
                                category=ChangeCategory.ENDPOINT_REMOVED,
                                path=path,
                                method=method,
                                location=f"paths.{path}",
                                description=f"Endpoint removed: {method.upper()} {path}",
                                old_value=op.get("operationId"),
                            )
                        )
                continue

            if path not in base_paths:
                for method, op in head_paths[path].items():
                    if method.lower() in HTTP_METHODS:
                        changes.append(
                            create_change(
                                category=ChangeCategory.ENDPOINT_ADDED,
                                path=path,
                                method=method,
                                location=f"paths.{path}",
                                description=f"New endpoint added: {method.upper()} {path}",
                                new_value=op.get("operationId"),
                            )
                        )
                continue

            self._compare_path_operations(path, base_paths[path], head_paths[path], changes)

        return DiffResult(
            changes=changes,
            base_title=self.base.title,
            base_version=self.base.version,
            head_title=self.head.title,
            head_version=self.head.version,
        )

    def _compare_path_operations(
        self,
        path: str,
        base_path_item: Dict[str, Any],
        head_path_item: Dict[str, Any],
        changes: List[Change],
    ) -> None:
        base_methods = {k.lower(): v for k, v in base_path_item.items() if k.lower() in HTTP_METHODS}
        head_methods = {k.lower(): v for k, v in head_path_item.items() if k.lower() in HTTP_METHODS}

        for method, base_op in base_methods.items():
            if method not in head_methods:
                changes.append(
                    create_change(
                        category=ChangeCategory.METHOD_REMOVED,
                        path=path,
                        method=method,
                        location=f"paths.{path}.{method}",
                        description=f"HTTP method removed: {method.upper()} {path}",
                        old_value=base_op.get("operationId"),
                    )
                )
            else:
                head_op = head_methods[method]
                if not base_op.get("deprecated") and head_op.get("deprecated"):
                    changes.append(
                        create_change(
                            category=ChangeCategory.OPERATION_DEPRECATED,
                            path=path,
                            method=method,
                            location=f"paths.{path}.{method}.deprecated",
                            description=f"Operation marked deprecated: {method.upper()} {path}",
                        )
                    )
                self._compare_parameters(path, method, base_op.get("parameters", []), head_op.get("parameters", []), changes)
                self._compare_request_body(path, method, base_op.get("requestBody"), head_op.get("requestBody"), changes)
                self._compare_responses(path, method, base_op.get("responses", {}), head_op.get("responses", {}), changes)

        for method, head_op in head_methods.items():
            if method not in base_methods:
                changes.append(
                    create_change(
                        category=ChangeCategory.METHOD_ADDED,
                        path=path,
                        method=method,
                        location=f"paths.{path}.{method}",
                        description=f"New HTTP method supported: {method.upper()} {path}",
                        new_value=head_op.get("operationId"),
                    )
                )

    def _compare_parameters(
        self,
        path: str,
        method: str,
        base_params: List[Dict[str, Any]],
        head_params: List[Dict[str, Any]],
        changes: List[Change],
    ) -> None:
        base_map = {(p.get("name"), p.get("in")): p for p in base_params if "name" in p}
        head_map = {(p.get("name"), p.get("in")): p for p in head_params if "name" in p}

        for (name, param_in), b_param in base_map.items():
            if (name, param_in) not in head_map:
                changes.append(
                    create_change(
                        category=ChangeCategory.PARAM_REMOVED,
                        path=path,
                        method=method,
                        location=f"parameters.{param_in}.{name}",
                        description=f"Parameter removed: '{name}' in {param_in}",
                        old_value=b_param,
                    )
                )
            else:
                h_param = head_map[(name, param_in)]
                b_req = b_param.get("required", False)
                h_req = h_param.get("required", False)
                if not b_req and h_req:
                    changes.append(
                        create_change(
                            category=ChangeCategory.PARAM_REQUIRED_CHANGED,
                            path=path,
                            method=method,
                            location=f"parameters.{param_in}.{name}.required",
                            description=f"Parameter '{name}' changed from optional to required",
                            old_value=False,
                            new_value=True,
                        )
                    )

                b_type = self._extract_type(b_param.get("schema", {}))
                h_type = self._extract_type(h_param.get("schema", {}))
                if b_type and h_type and b_type != h_type:
                    changes.append(
                        create_change(
                            category=ChangeCategory.PARAM_TYPE_CHANGED,
                            path=path,
                            method=method,
                            location=f"parameters.{param_in}.{name}.type",
                            description=f"Parameter '{name}' type changed from '{b_type}' to '{h_type}'",
                            old_value=b_type,
                            new_value=h_type,
                        )
                    )

        for (name, param_in), h_param in head_map.items():
            if (name, param_in) not in base_map:
                is_req = h_param.get("required", False)
                cat = ChangeCategory.PARAM_REQUIRED_ADDED if is_req else ChangeCategory.PARAM_OPTIONAL_ADDED
                desc = (
                    f"New REQUIRED parameter added: '{name}' in {param_in}"
                    if is_req
                    else f"New optional parameter added: '{name}' in {param_in}"
                )
                changes.append(
                    create_change(
                        category=cat,
                        path=path,
                        method=method,
                        location=f"parameters.{param_in}.{name}",
                        description=desc,
                        new_value=h_param,
                    )
                )

    def _compare_request_body(
        self,
        path: str,
        method: str,
        base_body: Optional[Dict[str, Any]],
        head_body: Optional[Dict[str, Any]],
        changes: List[Change],
    ) -> None:
        if base_body is None and head_body is None:
            return

        if base_body is not None and head_body is None:
            changes.append(
                create_change(
                    category=ChangeCategory.REQUEST_BODY_REMOVED,
                    path=path,
                    method=method,
                    location="requestBody",
                    description="Request body removed",
                )
            )
            return

        if base_body is None and head_body is not None:
            if head_body.get("required", False):
                changes.append(
                    create_change(
                        category=ChangeCategory.REQUEST_BODY_REQUIRED_CHANGED,
                        path=path,
                        method=method,
                        location="requestBody.required",
                        description="New REQUIRED request body added",
                    )
                )
            return

        if not base_body.get("required", False) and head_body.get("required", False):
            changes.append(
                create_change(
                    category=ChangeCategory.REQUEST_BODY_REQUIRED_CHANGED,
                    path=path,
                    method=method,
                    location="requestBody.required",
                    description="Request body changed from optional to required",
                )
            )

        b_schema = base_body.get("content", {}).get("application/json", {}).get("schema", {})
        h_schema = head_body.get("content", {}).get("application/json", {}).get("schema", {})
        self._compare_schema_properties(path, method, "requestBody", b_schema, h_schema, is_request=True, changes=changes)

    def _compare_responses(
        self,
        path: str,
        method: str,
        base_responses: Dict[str, Any],
        head_responses: Dict[str, Any],
        changes: List[Change],
    ) -> None:
        for status_code, b_resp in base_responses.items():
            if status_code not in head_responses:
                if status_code.startswith("2") or status_code == "default":
                    changes.append(
                        create_change(
                            category=ChangeCategory.RESPONSE_STATUS_REMOVED,
                            path=path,
                            method=method,
                            location=f"responses.{status_code}",
                            description=f"Response status code removed: HTTP {status_code}",
                            old_value=status_code,
                        )
                    )
            else:
                h_resp = head_responses[status_code]
                b_schema = b_resp.get("content", {}).get("application/json", {}).get("schema", {})
                h_schema = h_resp.get("content", {}).get("application/json", {}).get("schema", {})
                self._compare_schema_properties(
                    path, method, f"responses.{status_code}", b_schema, h_schema, is_request=False, changes=changes
                )

        for status_code in head_responses:
            if status_code not in base_responses:
                changes.append(
                    create_change(
                        category=ChangeCategory.RESPONSE_STATUS_ADDED,
                        path=path,
                        method=method,
                        location=f"responses.{status_code}",
                        description=f"New response status code documented: HTTP {status_code}",
                        new_value=status_code,
                    )
                )

    def _compare_schema_properties(
        self,
        path: str,
        method: str,
        context: str,
        base_schema: Dict[str, Any],
        head_schema: Dict[str, Any],
        is_request: bool,
        changes: List[Change],
    ) -> None:
        b_props = base_schema.get("properties", {})
        h_props = head_schema.get("properties", {})
        b_req = set(base_schema.get("required", []))
        h_req = set(head_schema.get("required", []))

        for prop_name, b_prop in b_props.items():
            if prop_name not in h_props:
                cat = ChangeCategory.REQUEST_PROPERTY_REMOVED if is_request else ChangeCategory.RESPONSE_PROPERTY_REMOVED
                desc = (
                    f"Request payload property removed: '{prop_name}'"
                    if is_request
                    else f"Response payload property removed: '{prop_name}' (clients expecting this will break)"
                )
                changes.append(
                    create_change(
                        category=cat,
                        path=path,
                        method=method,
                        location=f"{context}.properties.{prop_name}",
                        description=desc,
                        old_value=b_prop,
                    )
                )
            else:
                h_prop = h_props[prop_name]
                b_t = self._extract_type(b_prop)
                h_t = self._extract_type(h_prop)
                if b_t and h_t and b_t != h_t:
                    cat = ChangeCategory.REQUEST_PROPERTY_TYPE_CHANGED if is_request else ChangeCategory.RESPONSE_PROPERTY_TYPE_CHANGED
                    changes.append(
                        create_change(
                            category=cat,
                            path=path,
                            method=method,
                            location=f"{context}.properties.{prop_name}.type",
                            description=f"Property '{prop_name}' type changed from '{b_t}' to '{h_t}'",
                            old_value=b_t,
                            new_value=h_t,
                        )
                    )

                if b_t == "object" and h_t == "object":
                    self._compare_schema_properties(
                        path, method, f"{context}.properties.{prop_name}", b_prop, h_prop, is_request, changes
                    )

        for prop_name, h_prop in h_props.items():
            if prop_name not in b_props:
                if is_request:
                    if prop_name in h_req:
                        changes.append(
                            create_change(
                                category=ChangeCategory.REQUEST_PROPERTY_REQUIRED_ADDED,
                                path=path,
                                method=method,
                                location=f"{context}.properties.{prop_name}",
                                description=f"New REQUIRED request property added: '{prop_name}'",
                                new_value=h_prop,
                            )
                        )
                    else:
                        changes.append(
                            create_change(
                                category=ChangeCategory.REQUEST_PROPERTY_OPTIONAL_ADDED,
                                path=path,
                                method=method,
                                location=f"{context}.properties.{prop_name}",
                                description=f"New optional request property added: '{prop_name}'",
                                new_value=h_prop,
                            )
                        )
                else:
                    changes.append(
                        create_change(
                            category=ChangeCategory.RESPONSE_PROPERTY_ADDED,
                            path=path,
                            method=method,
                            location=f"{context}.properties.{prop_name}",
                            description=f"New field in response payload: '{prop_name}'",
                            new_value=h_prop,
                        )
                    )

        if is_request:
            newly_required = (h_req - b_req) & set(b_props.keys())
            for prop_name in sorted(newly_required):
                changes.append(
                    create_change(
                        category=ChangeCategory.REQUEST_PROPERTY_REQUIRED_ADDED,
                        path=path,
                        method=method,
                        location=f"{context}.required.{prop_name}",
                        description=f"Existing request property '{prop_name}' was made REQUIRED",
                        old_value=False,
                        new_value=True,
                    )
                )

    def _extract_type(self, schema_node: Dict[str, Any]) -> Optional[str]:
        if "type" in schema_node:
            t = schema_node["type"]
            return t if isinstance(t, str) else str(t)
        if "properties" in schema_node:
            return "object"
        if "items" in schema_node:
            return "array"
        return None
