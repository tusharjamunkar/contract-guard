"""
Unit tests for OpenAPI spec parser and dereferencing.
"""

from contract_guard.parser import OpenAPISpec, load_spec_from_string


def test_parser_dereference_ref():
    spec_data = {
        "openapi": "3.0.0",
        "info": {"title": "Test API", "version": "1.0.0"},
        "paths": {
            "/item": {
                "get": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Item": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}}
                }
            }
        }
    }

    spec = OpenAPISpec(spec_data)
    assert spec.title == "Test API"
    assert spec.version == "1.0.0"
    schema = spec.paths["/item"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]
    assert schema["type"] == "object"
    assert "name" in schema["properties"]


def test_parser_circular_ref_guard():
    spec_data = {
        "openapi": "3.0.0",
        "paths": {},
        "components": {
            "schemas": {
                "Node": {
                    "type": "object",
                    "properties": {
                        "child": {"$ref": "#/components/schemas/Node"}
                    }
                }
            }
        }
    }
    spec = OpenAPISpec(spec_data)
    node_schema = spec.dereferenced["components"]["schemas"]["Node"]
    assert node_schema["properties"]["child"]["properties"]["child"]["_circular_ref"] == "#/components/schemas/Node"
