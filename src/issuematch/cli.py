"""Command-line interface. Wiring only. See docs/CLI_SPEC.md and docs/CONTRACT.md section 5.

Commands that need modules not built yet exit with code 4 and name the milestone.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Annotated

import typer

from issuematch import __version__
from issuematch.availability import is_available
from issuematch.config import Settings
from issuematch.demo import DEMO_REPO, demo_issues
from issuematch.graph import build_issue_graph, to_json, to_mermaid

app = typer.Typer(no_args_is_help=True, add_completion=False)

EXIT_NOT_IMPLEMENTED = 4


class MapFormat(StrEnum):
    JSON = "json"
    MERMAID = "mermaid"
    HTML = "html"


def _not_yet(what: str, milestone: str) -> None:
    typer.echo(f"{what} is not built yet (milestone {milestone} in docs/todo/MILESTONES.md).")
    raise typer.Exit(EXIT_NOT_IMPLEMENTED)


@app.command()
def version() -> None:
    """Print the app name and version."""
    typer.echo(f"{Settings().APP_NAME} {__version__}")


@app.command()
def ingest(repo: Annotated[str, typer.Argument(help="owner/name")]) -> None:
    """Fetch and cache issues and PRs for a repo."""
    _not_yet("Ingest", "M2")


@app.command()
def profile(login: str) -> None:
    """Build a skill profile for a GitHub user."""
    _not_yet("Skill profiles", "M3")


@app.command()
def match(
    repo: Annotated[str, typer.Argument(help="owner/name")],
    user: Annotated[str, typer.Option("--user", help="GitHub login")],
) -> None:
    """Recommend the open issues that best fit a user."""
    _not_yet("Matching", "M5")


@app.command("map")
def map_cmd(
    repo: Annotated[str, typer.Argument(help="owner/name")] = DEMO_REPO,
    fmt: Annotated[MapFormat, typer.Option("--format")] = MapFormat.MERMAID,
    demo: Annotated[bool, typer.Option("--demo", help="Use built-in sample data")] = False,
    out_dir: Annotated[Path, typer.Option("--out")] = Path("build"),
) -> None:
    """Build the issue map and write it to build/."""
    if not demo:
        _not_yet("Maps from real repos (needs ingest)", "M2 + M7")
    if fmt is MapFormat.HTML:
        _not_yet("The HTML map view", "M7")

    settings = Settings()
    now = datetime.now(UTC)
    issues = demo_issues(now)
    open_issues = [i for i in issues if i.state == "open"]
    graph = build_issue_graph(DEMO_REPO, open_issues, settings)
    available = sum(is_available(i, settings, now).available for i in open_issues)

    out_dir.mkdir(parents=True, exist_ok=True)
    text = to_mermaid(graph) if fmt is MapFormat.MERMAID else to_json(graph)
    ext = "mmd" if fmt is MapFormat.MERMAID else "json"
    path = out_dir / f"map-{DEMO_REPO.replace('/', '-')}.{ext}"
    path.write_text(text, encoding="utf-8")
    typer.echo(text)
    typer.echo(
        f"{len(graph.nodes)} issues, {len(graph.edges)} edges, {len(graph.clusters)} clusters; "
        f"{available} available. Wrote {path}"
    )


if __name__ == "__main__":
    app()
