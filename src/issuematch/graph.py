"""Issue map building and export. Pure: no I/O. See docs/ISSUE_MAP_SPEC.md. Owner: Map agent.

v1 builds mentions, blocks and same_files edges and path/label clusters. Duplicate edges
(embeddings) and the HTML view come in milestone M7.
"""

from __future__ import annotations

import re
from collections import Counter
from itertools import combinations
from pathlib import PurePosixPath

from issuematch.config import Settings
from issuematch.models import EdgeKind, Issue, IssueEdge, IssueGraph, IssueNode, IssueRef

_MENTION = re.compile(r"(?<![\w/])#(\d+)\b")
_BLOCKED_BY = re.compile(r"\b(?:blocked by|depends on|after)\s+#(\d+)\b", re.IGNORECASE)
_CLUSTER_LABEL_PREFIXES = ("area/", "area:", "component/", "component:")


def find_mentions(text: str) -> set[int]:
    return {int(n) for n in _MENTION.findall(text)}


def find_blockers(text: str) -> set[int]:
    """Issue numbers this text says it is blocked by."""
    return {int(n) for n in _BLOCKED_BY.findall(text)}


def _files(issue: Issue) -> set[str]:
    return {f for pr in issue.linked_prs for f in pr.files_changed}


def cluster_for(issue: Issue) -> str:
    """Most common top-level directory in linked PRs, else an area label, else 'misc'."""
    tops = Counter(
        PurePosixPath(f).parts[0] for f in _files(issue) if len(PurePosixPath(f).parts) > 1
    )
    if tops:
        return tops.most_common(1)[0][0]
    for label in issue.labels:
        low = label.lower()
        for prefix in _CLUSTER_LABEL_PREFIXES:
            if low.startswith(prefix):
                return low[len(prefix) :]
    return "misc"


def build_issue_graph(repo: str, issues: list[Issue], settings: Settings) -> IssueGraph:
    by_number = {i.ref.number: i for i in issues if i.ref.repo == repo}
    nodes = [
        IssueNode(ref=i.ref, title=i.title, cluster=cluster_for(i)) for i in by_number.values()
    ]
    edges: list[IssueEdge] = []
    seen: set[tuple[int, int, EdgeKind]] = set()

    def add(src: int, dst: int, kind: EdgeKind, weight: float = 1.0) -> None:
        key = (src, dst, kind)
        if src != dst and dst in by_number and key not in seen:
            seen.add(key)
            edges.append(
                IssueEdge(
                    source=by_number[src].ref, target=by_number[dst].ref, kind=kind, weight=weight
                )
            )

    for num, issue in by_number.items():
        blockers = find_blockers(issue.body)
        for b in blockers:
            add(b, num, EdgeKind.BLOCKS)  # blocker -> blocked issue
        explicit = find_mentions(issue.body) | {m.number for m in issue.mentions if m.repo == repo}
        for m in explicit - blockers:
            add(num, m, EdgeKind.MENTIONS)

    files = {num: _files(i) for num, i in by_number.items()}
    for a, b in combinations(sorted(by_number), 2):
        shared = files[a] & files[b]
        if len(shared) >= settings.SAME_FILES_MIN_OVERLAP and shared:
            add(a, b, EdgeKind.SAME_FILES, len(shared) / len(files[a] | files[b]))

    # Keep the most connected nodes when over the cap (ISSUE_MAP_SPEC; fit-aware later).
    if len(nodes) > settings.MAP_MAX_NODES:
        degree = Counter([e.source for e in edges] + [e.target for e in edges])
        nodes = sorted(nodes, key=lambda n: degree[n.ref], reverse=True)[: settings.MAP_MAX_NODES]
        kept = {n.ref for n in nodes}
        edges = [e for e in edges if e.source in kept and e.target in kept]

    clusters: dict[str, list[IssueRef]] = {}
    for node in nodes:
        clusters.setdefault(node.cluster or "misc", []).append(node.ref)

    return IssueGraph(repo=repo, nodes=nodes, edges=edges, clusters=clusters)


def _mermaid_id(ref: IssueRef) -> str:
    return f"i{ref.number}"


def _mermaid_label(text: str, limit: int = 40) -> str:
    clean = text.replace('"', "'").replace("\n", " ")
    return clean if len(clean) <= limit else clean[: limit - 1] + "…"


_ARROWS = {
    EdgeKind.BLOCKS: "-->|blocks|",
    EdgeKind.MENTIONS: "-.->|mentions|",
    EdgeKind.DUPLICATE: "<-->|duplicate|",
    EdgeKind.SAME_FILES: "---|same files|",
    EdgeKind.SAME_CLUSTER: "---",
}


def to_mermaid(graph: IssueGraph) -> str:
    titles = {n.ref: n.title for n in graph.nodes}
    lines = ["graph LR"]
    for idx, (name, refs) in enumerate(sorted(graph.clusters.items())):
        lines.append(f'  subgraph c{idx}["{_mermaid_label(name)}"]')
        for ref in refs:
            if ref in titles:
                label = _mermaid_label(f"#{ref.number} {titles[ref]}")
                lines.append(f'    {_mermaid_id(ref)}["{label}"]')
        lines.append("  end")
    for e in graph.edges:
        lines.append(f"  {_mermaid_id(e.source)} {_ARROWS[e.kind]} {_mermaid_id(e.target)}")
    return "\n".join(lines) + "\n"


def to_json(graph: IssueGraph) -> str:
    return graph.model_dump_json(indent=2)
