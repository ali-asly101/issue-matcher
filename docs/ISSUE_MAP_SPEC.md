# ISSUE MAP SPEC

Owner: Map agent. Code: `src/issuematch/graph.py` (pure), `src/issuematch/mapview/` (HTML export).

## Goal

A map of the repo's issues that shows structure at a glance: which subsystems have the most work, what blocks what, which issues are duplicates, and where **you** are strongest.

## Nodes and edges

| Edge kind | Rule | Weight |
| --- | --- | --- |
| `mentions` | issue body/comments reference `#N` | 1.0 |
| `blocks` | text patterns: "blocked by #N", "depends on #N", "after #N" | 1.0 |
| `duplicate` | embedding cosine >= `DUPLICATE_SIMILARITY` | the similarity |
| `same_files` | linked PRs or `likely_files` share at least `SAME_FILES_MIN_OVERLAP` files | Jaccard overlap |
| `same_cluster` | implicit, rendered as grouping, not drawn as edges | - |

Open issues only by default; closed ones with `--include-closed`. Cap at `MAP_MAX_NODES`, keeping the highest-degree and best-fit nodes.

## Clusters

v1: cluster by the most common top-level path among linked PRs/likely files, fall back to the first `area/*` or `component:*` label, else `misc`. Later: community detection on the graph + an LLM-written cluster name.

## Overlays

- Colour by `effort` (difficulty) or by `fit` for a given user.
- Size by degree (how connected).
- Onboarding path: topological order over `blocks` edges inside a user's best cluster.

## Exports

- JSON (`IssueGraph`), Mermaid (`graph LR`, one subgraph per cluster), and later a self-contained HTML file using Cytoscape.js (no server needed).

## Acceptance tests

- [x] Mention edges parsed from bodies (`tests/test_graph.py`).
- [x] "blocked by #N" produces a `blocks` edge pointing the right way.
- [x] Mermaid export is valid syntax for the demo graph (subgraph per cluster).
- [ ] 1,000-node graph builds in under 5 seconds.
