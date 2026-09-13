"""
OpenAPI specification loader and JSON schema dereferencer.
"""

import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def load_spec_from_string(content: str) -> Dict[str, Any]:
    content = content.strip()
    if content.startswith("{") or content.startswith("["):
        return json.loads(content)
    if HAS_YAML:
        return yaml.safe_load(content)
    return json.loads(content)


def load_spec_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"OpenAPI spec file not found: {file_path}")
    raw_content = path.read_text(encoding="utf-8")
    return load_spec_from_string(raw_content)


class OpenAPISpec:
    def __init__(self, raw_spec: Dict[str, Any]):
        self.raw = copy.deepcopy(raw_spec)
        self.dereferenced = self._dereference_root(copy.deepcopy(raw_spec))

    @property
    def title(self) -> str:
        return self.raw.get("info", {}).get("title", "API Contract")

    @property
    def version(self) -> str:
        return self.raw.get("info", {}).get("version", "1.0.0")

    @property
    def paths(self) -> Dict[str, Any]:
        return self.dereferenced.get("paths", {})

    def _resolve_ref(self, ref: str, root: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not ref.startswith("#/"):
            return None
        parts = ref[2:].split("/")
        curr = root
        for part in parts:
            if isinstance(curr, dict) and part in curr:
                curr = curr[part]
            else:
                return None
        return curr if isinstance(curr, dict) else None

    def _dereference_root(self, root: Dict[str, Any]) -> Dict[str, Any]:
        def _walk(node: Any, visited_refs: set) -> Any:
            if isinstance(node, dict):
                if "$ref" in node and isinstance(node["$ref"], str):
                    ref_str = node["$ref"]
                    if ref_str in visited_refs:
                        return {"type": "object", "_circular_ref": ref_str}
                    resolved = self._resolve_ref(ref_str, root)
                    if resolved is not None:
                        new_visited = visited_refs | {ref_str}
                        merged = copy.deepcopy(resolved)
                        for k, v in node.items():
                            if k != "$ref":
                                merged[k] = v
                        return _walk(merged, new_visited)
                return {k: _walk(v, visited_refs) for k, v in node.items()}
            elif isinstance(node, list):
                return [_walk(item, visited_refs) for item in node]
            return node

        return _walk(root, set())
