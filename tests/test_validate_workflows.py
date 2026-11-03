"""Tests for tools/validate_workflows.py."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import validate_workflows as vw

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"
ENV_EXAMPLE = ROOT / ".env.example"


def write_workflow(tmp_path: Path, data: dict | str, name: str = "wf.json") -> Path:
    path = tmp_path / name
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


def minimal(**node_params) -> dict:
    return {
        "name": "t",
        "nodes": [
            {
                "parameters": node_params,
                "id": "a",
                "name": "A",
                "type": "n8n-nodes-base.code",
                "typeVersion": 2,
                "position": [0, 0],
            }
        ],
        "connections": {},
    }


@pytest.mark.parametrize("path", sorted((ROOT / "workflows").glob("*.json")), ids=lambda p: p.name)
def test_repository_workflows_pass(path: Path) -> None:
    report = vw.validate_workflow(path, vw.parse_env_example(ENV_EXAMPLE))
    assert report.ok, report.errors


def test_valid_fixture_passes() -> None:
    report = vw.validate_workflow(FIXTURES / "valid_workflow.json", {"TELEGRAM_CHAT_ID"})
    assert report.ok, report.errors
    assert report.env_vars == {"TELEGRAM_CHAT_ID"}


def test_broken_fixture_reports_every_problem() -> None:
    report = vw.validate_workflow(FIXTURES / "broken_workflow.json", {"TELEGRAM_CHAT_ID"})
    text = "\n".join(report.errors)
    expected = [
        "duplicate node name 'Fetch News'",
        "duplicate node id 'http'",
        "node 'No Position' is missing typeVersion, position",
        "'Fetch News' -> 'Send To Nowhere': target node does not exist",
        "connection source 'Ghost Node' is not a node",
        "inline secret in 'api_token'",
        "hard-coded chat ID",
        "credential 'telegramApi' must be a reference",
        "'pinData' is not empty",
        "$env.UNDOCUMENTED_VARIABLE is used but not documented",
    ]
    for fragment in expected:
        assert fragment in text, f"missing error {fragment!r} in:\n{text}"
    assert not report.ok


def test_invalid_json(tmp_path: Path) -> None:
    report = vw.validate_workflow(write_workflow(tmp_path, '{"name": "x", "nodes": ['))
    assert report.errors and report.errors[0].startswith("cannot parse JSON")


def test_duplicate_json_keys_are_rejected(tmp_path: Path) -> None:
    # n8n exports cannot contain duplicate keys; a hand edit that adds one silently drops data.
    raw = '{"name": "x", "nodes": [], "connections": {"A": {}, "A": {}}}'
    report = vw.validate_workflow(write_workflow(tmp_path, raw))
    assert "duplicate JSON key 'A'" in report.errors[0]


def test_missing_nodes(tmp_path: Path) -> None:
    report = vw.validate_workflow(write_workflow(tmp_path, {"name": "x", "nodes": [], "connections": {}}))
    assert "'nodes' must be a non-empty list" in report.errors


@pytest.mark.parametrize(
    "secret",
    [
        # Built at runtime so no secret-shaped literal is committed.
        "1234567890:" + "A" * 35,
        "sk-" + "x1" * 15,
        "ghp_" + "a" * 36,
        "AKIA" + "ABCDEFGHIJKLMNOP",
        "Bearer " + "abc.def-123" * 3,
    ],
    ids=["telegram", "openai", "github", "aws", "bearer"],
)
def test_known_secret_formats_are_detected(tmp_path: Path, secret: str) -> None:
    path = write_workflow(tmp_path, minimal(jsCode=f"const x = '{secret}';"))
    assert any("found inline" in e for e in vw.validate_workflow(path).errors)


def test_sensitive_parameter_must_be_expression(tmp_path: Path) -> None:
    bad = vw.validate_workflow(write_workflow(tmp_path, minimal(password="hunter2"), "bad.json"))
    good = vw.validate_workflow(write_workflow(tmp_path, minimal(password="={{ $env.PW }}"), "good.json"), {"PW"})
    assert any("inline secret" in e for e in bad.errors)
    assert good.ok, good.errors


def test_email_addresses(tmp_path: Path) -> None:
    personal = vw.validate_workflow(write_workflow(tmp_path, minimal(to="someone@gmail.com"), "a.json"))
    example = vw.validate_workflow(write_workflow(tmp_path, minimal(to="alerts@example.com"), "b.json"))
    assert any("e-mail address" in e for e in personal.errors)
    assert example.ok, example.errors


def test_env_reference_forms(tmp_path: Path) -> None:
    path = write_workflow(tmp_path, minimal(a="={{ $env.FOO }}", b="={{ $env['BAR'] }}"))
    report = vw.validate_workflow(path, {"FOO"})
    assert report.env_vars == {"FOO", "BAR"}
    assert report.errors == ["$env.BAR is used but not documented in .env.example"]


def test_parse_env_example(tmp_path: Path) -> None:
    env = tmp_path / ".env.example"
    env.write_text("# comment\nFOO=1\nexport BAR=\n\nnot a var\n", encoding="utf-8")
    assert vw.parse_env_example(env) == {"FOO", "BAR"}


def test_cli_exit_codes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert vw.main([str(FIXTURES / "valid_workflow.json"), "--env-example", str(ENV_EXAMPLE)]) == 0
    assert vw.main([str(FIXTURES / "broken_workflow.json"), "--env-example", str(ENV_EXAMPLE)]) == 1
    assert vw.main([str(tmp_path)]) == 1  # empty directory: nothing to validate
    out = capsys.readouterr().out
    assert "FAIL" in out and "OK" in out
