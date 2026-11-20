"""Shared data models: the contract in code. See docs/CONTRACT.md section 3.

Owner: Architect. Adding or changing a field is a contract change.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Unit = Annotated[float, Field(ge=0.0, le=1.0)]


class _Model(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class Evidence(_Model):
    kind: Literal["pr", "issue", "commit", "file", "review", "self_declared", "cv"]
    ref: str  # URL or identifier
    note: str = ""


class IssueRef(_Model):
    repo: str  # "owner/name"
    number: int

    def __str__(self) -> str:
        return f"{self.repo}#{self.number}"


class LinkedPR(_Model):
    number: int
    state: Literal["open", "merged", "closed"]
    files_changed: list[str] = Field(default_factory=list)
    additions: int = 0
    deletions: int = 0
    created_at: datetime
    merged_at: datetime | None = None


class Issue(_Model):
    ref: IssueRef
    title: str
    body: str = ""
    state: Literal["open", "closed"]
    labels: list[str] = Field(default_factory=list)
    author: str | None = None
    assignees: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    comments_count: int = 0
    last_maintainer_activity_at: datetime | None = None
    linked_prs: list[LinkedPR] = Field(default_factory=list)
    mentions: list[IssueRef] = Field(default_factory=list)


class Skill(_Model):
    name: str  # namespaced: lang:, area:, concept:, tool:
    level: Unit
    confidence: Unit
    evidence: list[Evidence] = Field(default_factory=list)


class SkillProfile(_Model):
    person: str
    skills: list[Skill] = Field(default_factory=list)
    typical_change_lines: int | None = None
    want_to_learn: list[str] = Field(default_factory=list)
    hours_per_week: float | None = None
    seniority: str | None = None  # team mode only

    def skill_map(self) -> dict[str, Skill]:
        return {s.name: s for s in self.skills}


class DifficultyEstimate(_Model):
    issue: IssueRef
    effort: Unit  # 0 trivial, 1 very hard
    est_hours_low: float = Field(ge=0)
    est_hours_high: float = Field(ge=0)
    concepts: list[str] = Field(default_factory=list)
    likely_files: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    confidence: Unit
    source: Literal["history", "llm", "blended"]
    evidence: list[Evidence] = Field(default_factory=list)


class UnavailableReason(StrEnum):
    CLOSED = "closed"
    ASSIGNED = "assigned"
    OPEN_PR = "open_pr"
    STALE = "stale"
    BLOCKED = "blocked"
    NEEDS_DESIGN = "needs_design"
    NOT_ACTIONABLE = "not_actionable"


class AvailabilityResult(_Model):
    available: bool
    reasons: list[UnavailableReason] = Field(default_factory=list)


class FitBreakdown(_Model):
    skill_overlap: Unit
    stretch: Unit
    effort_fit: Unit
    responsiveness: Unit


class Match(_Model):
    issue: IssueRef
    score: Unit
    breakdown: FitBreakdown
    difficulty: DifficultyEstimate
    reasons: list[str] = Field(default_factory=list)
    first_steps: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: Unit


class EdgeKind(StrEnum):
    MENTIONS = "mentions"
    DUPLICATE = "duplicate"
    BLOCKS = "blocks"
    SAME_FILES = "same_files"
    SAME_CLUSTER = "same_cluster"


class IssueEdge(_Model):
    source: IssueRef
    target: IssueRef
    kind: EdgeKind
    weight: Unit = 1.0


class IssueNode(_Model):
    ref: IssueRef
    title: str
    cluster: str | None = None
    effort: Unit | None = None
    fit: Unit | None = None


class IssueGraph(_Model):
    repo: str
    nodes: list[IssueNode] = Field(default_factory=list)
    edges: list[IssueEdge] = Field(default_factory=list)
    clusters: dict[str, list[IssueRef]] = Field(default_factory=dict)
