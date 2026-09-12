#!/usr/bin/env python3
"""Convert a validated, local OpenAPI 3 document to Postman v2.1."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
from typing import Any


HTTP_METHODS = ("get", "put", "post", "patch", "delete", "head", "options", "trace")


def load_document(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        value = json.loads(text)
    except json.JSONDecodeError:
        if not shutil.which("yq"):
            raise SystemExit("输入不是 JSON；解析 YAML 需要安装 yq。")
        try:
            converted = subprocess.run(
                ["yq", "-o=json", ".", str(path)],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            value = json.loads(converted)
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            raise SystemExit(f"OpenAPI YAML 解析失败: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit("OpenAPI 根节点必须是对象。")
    return value


def dereference(document: dict[str, Any], value: Any) -> Any:
    if not isinstance(value, dict) or set(value) != {"$ref"}:
        return value
    ref = value["$ref"]
    if not isinstance(ref, str) or not ref.startswith("#/"):
        return value
    current: Any = document
    for part in ref[2:].split("/"):
        if not isinstance(current, dict) or part not in current:
            return value
        current = current[part]
    return current


def example_for(document: dict[str, Any], schema: Any) -> Any:
    schema = dereference(document, schema)
    if not isinstance(schema, dict):
        return None
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if schema.get("enum"):
        return schema["enum"][0]
    if schema.get("nullable"):
        return None
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {name: example_for(document, child) for name, child in schema.get("properties", {}).items()}
    if schema_type == "array":
        return [example_for(document, schema.get("items", {}))]
    if schema_type in {"integer", "number"}:
        return 0
    if schema_type == "boolean":
        return True
    return ""


def media_example(document: dict[str, Any], content: Any) -> Any:
    if not isinstance(content, dict):
        return None
    media = content.get("application/json") or next(iter(content.values()), None)
    if not isinstance(media, dict):
        return None
    if "example" in media:
        return media["example"]
    examples = media.get("examples")
    if isinstance(examples, dict) and examples:
        first = next(iter(examples.values()))
        if isinstance(first, dict) and "value" in first:
            return first["value"]
    return example_for(document, media.get("schema", {}))


def parameter_example(document: dict[str, Any], parameter: dict[str, Any]) -> str:
    if "example" in parameter:
        value = parameter["example"]
    elif isinstance(parameter.get("examples"), dict) and parameter["examples"]:
        first = next(iter(parameter["examples"].values()))
        value = first.get("value", "") if isinstance(first, dict) else first
    else:
        value = example_for(document, parameter.get("schema", {}))
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def resolve_parameters(document: dict[str, Any], path_item: dict[str, Any], operation: dict[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for source in (path_item.get("parameters", []), operation.get("parameters", [])):
        if not isinstance(source, list):
            continue
        for raw in source:
            parameter = dereference(document, raw)
            if not isinstance(parameter, dict) or not parameter.get("name") or not parameter.get("in"):
                continue
            result = [item for item in result if item.get("name") != parameter["name"] or item.get("in") != parameter["in"]]
            result.append(parameter)
    return result


def server_url(document: dict[str, Any]) -> str:
    servers = document.get("servers")
    if isinstance(servers, list) and servers and isinstance(servers[0], dict) and servers[0].get("url"):
        return str(servers[0]["url"])
    return "{{baseUrl}}"


def security_definitions(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    components = document.get("components")
    return components.get("securitySchemes", {}) if isinstance(components, dict) else {}


def auth_for(document: dict[str, Any], operation: dict[str, Any]) -> dict[str, Any] | None:
    if operation.get("security") == []:
        return {"type": "noauth"}
    security = operation.get("security", document.get("security"))
    if not isinstance(security, list) or not security or not isinstance(security[0], dict):
        return None
    schemes = security_definitions(document)
    scheme_name = next(iter(security[0]), None)
    scheme = schemes.get(scheme_name, {}) if scheme_name else {}
    if scheme.get("type") == "http" and str(scheme.get("scheme", "")).lower() == "bearer":
        return {"type": "bearer", "bearer": [{"key": "token", "value": "{{accessToken}}", "type": "string"}]}
    if scheme.get("type") == "http" and str(scheme.get("scheme", "")).lower() == "basic":
        return {"type": "basic", "basic": [{"key": "username", "value": "{{username}}", "type": "string"}, {"key": "password", "value": "{{password}}", "type": "string"}]}
    if scheme.get("type") == "apiKey" and scheme.get("in") in {"header", "query"}:
        location = "header" if scheme["in"] == "header" else "query"
        return {"type": "apikey", "apikey": [{"key": "key", "value": scheme.get("name", "apiKey"), "type": "string"}, {"key": "value", "value": "{{apiKey}}", "type": "string"}, {"key": "in", "value": location, "type": "string"}]}
    return None


def postman_url(document: dict[str, Any], route: str, parameters: list[dict[str, Any]]) -> tuple[str, list[dict[str, str]], list[dict[str, str]]]:
    path_variables: list[dict[str, str]] = []
    query: list[dict[str, str]] = []
    by_name = {(item.get("in"), item.get("name")): item for item in parameters}

    rendered = route
    for name in route.split("{")[1:]:
        variable = name.split("}", 1)[0]
        parameter = by_name.get(("path", variable))
        value = parameter_example(document, parameter) if parameter else ""
        path_variables.append({"key": variable, "value": value})
        rendered = rendered.replace("{" + variable + "}", ":" + variable, 1)
    for parameter in parameters:
        if parameter.get("in") == "query":
            query.append({"key": str(parameter["name"]), "value": parameter_example(document, parameter), "description": str(parameter.get("description", ""))})
    base = server_url(document).rstrip("/")
    return base + (rendered if rendered.startswith("/") else "/" + rendered), path_variables, query


def test_lines(operation: dict[str, Any]) -> list[str]:
    responses = operation.get("responses", {})
    codes = [str(code) for code in responses if str(code).isdigit()]
    if not codes:
        return []
    quoted = ", ".join(json.dumps(code) for code in codes)
    return [
        f"const expected = [{quoted}];",
        "pm.test('状态码符合 OpenAPI 契约', function () {",
        "  pm.expect(expected).to.include(String(pm.response.code));",
        "});",
    ]


def build_collection(document: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    variables: dict[str, str] = {"baseUrl": "http://localhost:8080"}
    servers = document.get("servers")
    if isinstance(servers, list) and servers and isinstance(servers[0], dict):
        for name, value in servers[0].get("variables", {}).items():
            if isinstance(value, dict):
                variables[name] = str(value.get("default", ""))
    for scheme in security_definitions(document).values():
        if not isinstance(scheme, dict):
            continue
        if scheme.get("type") == "http" and str(scheme.get("scheme", "")).lower() == "bearer":
            variables["accessToken"] = ""
        elif scheme.get("type") == "http" and str(scheme.get("scheme", "")).lower() == "basic":
            variables.update({"username": "", "password": ""})
        elif scheme.get("type") == "apiKey":
            variables["apiKey"] = ""

    folders: dict[str, list[dict[str, Any]]] = {}
    for route in sorted(document.get("paths", {})):
        path_item = document["paths"][route]
        if not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            parameters = resolve_parameters(document, path_item, operation)
            raw_url, path_variables, query = postman_url(document, route, parameters)
            headers = []
            for parameter in parameters:
                if parameter.get("in") == "header":
                    headers.append({"key": str(parameter["name"]), "value": parameter_example(document, parameter), "description": str(parameter.get("description", ""))})
            request: dict[str, Any] = {"method": method.upper(), "header": headers, "url": {"raw": raw_url, "host": [server_url(document)], "path": route.strip("/").split("/") if route.strip("/") else [], "variable": path_variables, "query": query}}
            request_body = dereference(document, operation.get("requestBody", {}))
            if isinstance(request_body, dict) and request_body.get("content"):
                body = media_example(document, request_body["content"])
                request["body"] = {"mode": "raw", "raw": json.dumps(body, ensure_ascii=False, indent=2), "options": {"raw": {"language": "json"}}}
                headers.append({"key": "Content-Type", "value": "application/json"})
            auth = auth_for(document, operation)
            if auth:
                request["auth"] = auth
            item: dict[str, Any] = {"name": operation.get("summary") or operation.get("operationId") or f"{method.upper()} {route}", "request": request}
            tests = test_lines(operation)
            if tests:
                item["event"] = [{"listen": "test", "script": {"type": "text/javascript", "exec": tests}}]
            tags = operation.get("tags")
            folder = str(tags[0]) if isinstance(tags, list) and tags else "接口"
            folders.setdefault(folder, []).append(item)

    collection = {"info": {"_postman_id": "", "name": document.get("info", {}).get("title", "API Collection"), "description": document.get("info", {}).get("description", ""), "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"}, "variable": [{"key": key, "value": value} for key, value in sorted(variables.items())], "item": [{"name": name, "item": folders[name]} for name in sorted(folders)]}
    environment = {"name": "接口联调环境（示例）", "values": [{"key": key, "value": value, "type": "default", "enabled": True} for key, value in sorted(variables.items())], "_postman_variable_scope": "environment", "_postman_exported_using": "api-integration-docs"}
    return collection, environment


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=pathlib.Path)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    parser.add_argument("--environment-output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    document = load_document(args.input)
    collection, environment = build_collection(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.environment_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(collection, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.environment_output.write_text(json.dumps(environment, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    count = sum(len(folder["item"]) for folder in collection["item"])
    print(f"Postman Collection v2.1 已生成: {count} 个接口")
    print(f"- {args.output}")
    print(f"- {args.environment_output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
