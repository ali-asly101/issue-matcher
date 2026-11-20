from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from issuematch.cli import EXIT_NOT_IMPLEMENTED, app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def test_map_demo_writes_mermaid(tmp_path: Path) -> None:
    result = runner.invoke(app, ["map", "--demo", "--format", "mermaid", "--out", str(tmp_path)])
    assert result.exit_code == 0, result.stdout
    files = list(tmp_path.glob("*.mmd"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8").startswith("graph LR")


def test_unbuilt_commands_exit_4() -> None:
    result = runner.invoke(app, ["match", "o/r", "--user", "me"])
    assert result.exit_code == EXIT_NOT_IMPLEMENTED
    assert "M5" in result.stdout
