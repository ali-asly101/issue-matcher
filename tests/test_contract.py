"""Checks that the code still matches docs/CONTRACT.md (config keys and enums)."""

from __future__ import annotations

import re
from pathlib import Path

from issuematch.config import Settings
from issuematch.models import EdgeKind, UnavailableReason

CONTRACT = (Path(__file__).parent.parent / "docs" / "CONTRACT.md").read_text(encoding="utf-8")


def _section(title: str) -> str:
    start = CONTRACT.index(title)
    end = CONTRACT.find("\n## ", start + 1)
    return CONTRACT[start : end if end != -1 else None]


def test_every_contract_config_key_exists() -> None:
    table = _section("## 4. Config keys")
    rows = [line for line in table.splitlines() if line.startswith("| ") and "`" in line]
    keys = {k for row in rows for k in re.findall(r"`([A-Z][A-Z0-9_]+)`", row.split("|")[2])}
    missing = keys - set(Settings.model_fields)
    assert not missing, f"Contract keys missing from Settings: {sorted(missing)}"


def test_enums_match_contract() -> None:
    models = _section("## 3. Data models")
    for reason in UnavailableReason:
        assert f"`{reason.value}`" in models
    for kind in EdgeKind:
        assert f"`{kind.value}`" in models


def test_no_secrets_in_settings() -> None:
    for name in Settings.model_fields:
        assert not name.endswith(("_TOKEN", "_KEY", "_SECRET", "PASSWORD")), name
