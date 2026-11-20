from __future__ import annotations

from datetime import datetime

from issuematch.config import Settings
from issuematch.demo import DEMO_REPO, demo_issues
from issuematch.graph import (
    build_issue_graph,
    cluster_for,
    find_blockers,
    find_mentions,
    to_mermaid,
)
from issuematch.models import EdgeKind, IssueGraph, LinkedPR
from tests.conftest import make_issue


def test_find_mentions_ignores_urls_and_words() -> None:
    assert find_mentions("see #12 and #7, not a/b#3 or abc#4") == {12, 7}


def test_find_blockers() -> None:
    assert find_blockers("This is Blocked by #5 and depends on #9.") == {5, 9}


def test_blocks_edge_direction(settings: Settings) -> None:
    a = make_issue(1, body="")
    b = make_issue(2, body="blocked by #1")
    g = build_issue_graph("o/r", [a, b], settings)
    blocks = [e for e in g.edges if e.kind is EdgeKind.BLOCKS]
    assert len(blocks) == 1
    assert (blocks[0].source.number, blocks[0].target.number) == (1, 2)
    assert not [e for e in g.edges if e.kind is EdgeKind.MENTIONS]


def test_same_files_edge_and_cluster(settings: Settings, now: datetime) -> None:
    pr = LinkedPR(number=9, state="merged", files_changed=["lexer/a.py"], created_at=now)
    a = make_issue(1, linked_prs=[pr])
    b = make_issue(2, linked_prs=[pr.model_copy(update={"number": 10})])
    g = build_issue_graph("o/r", [a, b], settings)
    assert any(e.kind is EdgeKind.SAME_FILES for e in g.edges)
    assert cluster_for(a) == "lexer"
    assert cluster_for(make_issue(3, labels=["area/docs"])) == "docs"
    assert cluster_for(make_issue(4)) == "misc"


def test_mentions_outside_repo_are_dropped(settings: Settings) -> None:
    g = build_issue_graph("o/r", [make_issue(1, body="see #999")], settings)
    assert g.edges == []


def test_demo_graph_mermaid_and_json_roundtrip(settings: Settings) -> None:
    issues = demo_issues()
    g = build_issue_graph(DEMO_REPO, issues, settings)
    text = to_mermaid(g)
    assert text.startswith("graph LR\n")
    assert text.count("subgraph") == len(g.clusters)
    assert "-->|blocks|" in text
    assert IssueGraph.model_validate_json(g.model_dump_json()) == g
