#!/usr/bin/env python3
"""Static checks for exported n8n workflow JSON files.

Checks, per workflow file:
  * the file parses as JSON (duplicate object keys are rejected too)
  * top-level shape: "name", a "nodes" list and a "connections" object
  * every node has a name, type, typeVersion and position; names and ids are unique
  * every connection source and target refers to an existing node
  * no inline secrets: credential-like parameters must be n8n expressions or
    credential references, and known token formats are rejected anywhere
  * no hard-coded Telegram chat IDs, no personal e-mail addresses, no pinned data
  * every $env.VAR the workflow reads is documented in .env.example

Usage:
  python tools/validate_workflows.py [PATH ...] [--env-example .env.example]

PATH may be a workflow file or a directory (all *.json inside are checked).
Exit code is 0 when every file passes, 1 otherwise. Standard library only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

# Parameter keys whose literal values would be secrets.
SENSITIVE_KEY = re.compile(
    r"^(api[_-]?key|api[_-]?token|apikey|access[_-]?token|auth[_-]?token|bot[_-]?token|"
    r"token|secret|client[_-]?secret|password|passwd|private[_-]?key)$",
    re.IGNORECASE,
)
# Generic name/value pairs (query, header, body parameters) that carry a secret.
SENSITIVE_PAIR_NAME = re.compile(
    r"(api[_-]?key|api[_-]?token|access[_-]?token|token|secret|password|authorization)",
    re.IGNORECASE,
)
# Known secret formats, checked in every string of the workflow.
SECRET_PATTERNS = {
    "Telegram bot token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "OpenAI-style API key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "AWS access key id": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "Google API key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "Slack token": re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"),
    "Bearer token": re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]{20,}=*"),
}
CHAT_ID_KEY = re.compile(r"^chat[_-]?id$", re.IGNORECASE)
NUMERIC_ID = re.compile(r"^-?\d{5,}$")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+\.)+[A-Za-z]{2,}")
ALLOWED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
ENV_REF = re.compile(r"\$env(?:\.([A-Za-z_][A-Za-z0-9_]*)|\[\s*['\"]([A-Za-z_][A-Za-z0-9_]*)['\"]\s*\])")
REQUIRED_NODE_KEYS = ("name", "type", "typeVersion", "position")


@dataclass
class Report:
    path: Path
    errors: list[str] = field(default_factory=list)
    env_vars: set[str] = field(default_factory=set)

    @property
    def ok(self) -> bool:
        return not self.errors


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    seen: dict[str, Any] = {}
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate JSON key {key!r}")
        seen[key] = value
    return seen


def _walk(value: Any, path: str = "") -> Iterator[tuple[str, str, Any]]:
    """Yield (json_path, key, value) for every key/value below ``value``."""
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}" if path else key
            yield child_path, key, child
            yield from _walk(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_path = f"{path}[{index}]"
            yield child_path, "", child
            yield from _walk(child, child_path)


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


def _is_expression(value: str) -> bool:
    return value.startswith("=")


def _check_secrets(node_name: str, params: Any, errors: list[str]) -> None:
    for json_path, key, value in _walk(params):
        where = f"node {node_name!r} parameter {json_path}"
        if isinstance(value, str) and value and not _is_expression(value):
            if SENSITIVE_KEY.match(key):
                errors.append(f"{where}: inline secret; use an n8n credential or an expression")
            if CHAT_ID_KEY.match(key) and NUMERIC_ID.match(value.strip()):
                errors.append(f"{where}: hard-coded chat ID; use an expression such as {{{{ $env.TELEGRAM_CHAT_ID }}}}")
        # name/value pairs, e.g. queryParameters.parameters[].{name,value}
        if isinstance(value, dict) and isinstance(value.get("name"), str) and "value" in value:
            pair_value = value.get("value")
            if (
                SENSITIVE_PAIR_NAME.search(value["name"])
                and isinstance(pair_value, str)
                and pair_value
                and not _is_expression(pair_value)
            ):
                errors.append(
                    f"node {node_name!r} parameter {json_path}: inline secret in {value['name']!r}; "
                    "use an n8n credential instead"
                )


def _check_credentials(node_name: str, creds: Any, errors: list[str]) -> None:
    if not isinstance(creds, dict):
        errors.append(f"node {node_name!r}: 'credentials' must be an object")
        return
    for cred_type, ref in creds.items():
        if not isinstance(ref, dict) or set(ref) - {"id", "name"}:
            errors.append(
                f"node {node_name!r}: credential {cred_type!r} must be a reference "
                "with only 'id' and 'name' (no inline credential data)"
            )


def validate_workflow(path: Path, documented_env: set[str] | None = None) -> Report:
    report = Report(path)
    errors = report.errors
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeDecodeError, ValueError) as exc:  # JSONDecodeError is a ValueError
        errors.append(f"cannot parse JSON: {exc}")
        return report

    if not isinstance(data, dict):
        errors.append("top level must be a JSON object")
        return report
    if not isinstance(data.get("name"), str) or not data["name"].strip():
        errors.append("workflow 'name' is missing or empty")
    nodes = data.get("nodes")
    connections = data.get("connections", {})
    if not isinstance(nodes, list) or not nodes:
        errors.append("'nodes' must be a non-empty list")
        return report
    if not isinstance(connections, dict):
        errors.append("'connections' must be an object")
        connections = {}

    names: set[str] = set()
    ids: set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            errors.append(f"nodes[{index}] is not an object")
            continue
        missing = [key for key in REQUIRED_NODE_KEYS if key not in node]
        name = node.get("name", f"nodes[{index}]")
        if missing:
            errors.append(f"node {name!r} is missing {', '.join(missing)}")
        if isinstance(node.get("name"), str):
            if node["name"] in names:
                errors.append(f"duplicate node name {node['name']!r}")
            names.add(node["name"])
        node_id = node.get("id")
        if node_id is not None:
            if node_id in ids:
                errors.append(f"duplicate node id {node_id!r}")
            ids.add(node_id)
        position = node.get("position")
        if "position" in node and not (
            isinstance(position, list) and len(position) == 2 and all(isinstance(p, (int, float)) for p in position)
        ):
            errors.append(f"node {name!r}: 'position' must be [x, y]")
        _check_secrets(name, node.get("parameters", {}), errors)
        if "credentials" in node:
            _check_credentials(name, node["credentials"], errors)

    for source, outputs in connections.items():
        if source not in names:
            errors.append(f"connection source {source!r} is not a node")
        if not isinstance(outputs, dict):
            errors.append(f"connections of {source!r} must be an object")
            continue
        for conn_type, branches in outputs.items():
            if not isinstance(branches, list):
                errors.append(f"connections {source!r}.{conn_type} must be a list")
                continue
            for branch in branches:
                for target in branch or []:
                    if not isinstance(target, dict) or "node" not in target:
                        errors.append(f"connection from {source!r} has a malformed target")
                        continue
                    if target["node"] not in names:
                        errors.append(f"connection {source!r} -> {target['node']!r}: target node does not exist")
                    if not isinstance(target.get("index", 0), int) or target.get("index", 0) < 0:
                        errors.append(f"connection {source!r} -> {target['node']!r}: invalid input index")

    if data.get("pinData"):
        errors.append("'pinData' is not empty; pinned execution data can leak real payloads")

    for text in _strings(data):
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                errors.append(f"possible {label} found inline")
        for match in EMAIL.finditer(text):
            if not match.group(0).lower().endswith(ALLOWED_EMAIL_DOMAINS):
                errors.append("e-mail address found inline; use a placeholder or an env variable")
        for match in ENV_REF.finditer(text):
            report.env_vars.add(match.group(1) or match.group(2))

    if documented_env is not None:
        for var in sorted(report.env_vars - documented_env):
            errors.append(f"$env.{var} is used but not documented in .env.example")
    return report


def parse_env_example(path: Path) -> set[str]:
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            names.add(line.split("=", 1)[0].removeprefix("export ").strip())
    return names


def collect(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        files.extend(sorted(path.glob("*.json")) if path.is_dir() else [path])
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("workflows")])
    parser.add_argument("--env-example", type=Path, default=Path(".env.example"),
                        help="file that documents env variables (default: .env.example)")
    args = parser.parse_args(argv)

    documented = parse_env_example(args.env_example) if args.env_example.is_file() else None
    if documented is None:
        print(f"warning: {args.env_example} not found, skipping env documentation check", file=sys.stderr)
    files = collect(args.paths)
    if not files:
        print("no workflow files found", file=sys.stderr)
        return 1

    failed = 0
    for path in files:
        report = validate_workflow(path, documented)
        if report.ok:
            env = f" (env: {', '.join(sorted(report.env_vars))})" if report.env_vars else ""
            print(f"OK   {path}{env}")
        else:
            failed += 1
            print(f"FAIL {path}")
            for error in report.errors:
                print(f"     - {error}")
    print(f"\n{len(files) - failed}/{len(files)} workflow files passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
