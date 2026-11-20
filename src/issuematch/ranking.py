"""Fit scoring and ranking. Pure: no I/O. See docs/RANKING_SPEC.md. Owner: Ranking agent.

Reason and first-step generation from evidence is milestone M5 and is not built yet.
"""

from __future__ import annotations

import math
from pathlib import PurePosixPath
from typing import Literal

from issuematch.config import Settings
from issuematch.models import DifficultyEstimate, FitBreakdown, Match, SkillProfile

FitLabel = Literal["Great fit", "Good fit", "Possible fit", "Weak match"]
ConfidenceLabel = Literal["High confidence", "Medium confidence", "Low confidence"]
EffortLabel = Literal["Small", "Medium", "Large", "Very large"]

_EXT_LANG = {
    ".py": "python",
    ".rs": "rust",
    ".go": "go",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".java": "java",
    ".rb": "ruby",
    ".luau": "luau",
    ".lua": "lua",
}


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def required_skills(difficulty: DifficultyEstimate) -> list[str]:
    """Skills an issue needs, derived from its difficulty estimate (RANKING_SPEC)."""
    skills: set[str] = {f"concept:{c.lower()}" for c in difficulty.concepts}
    for f in difficulty.likely_files:
        path = PurePosixPath(f)
        if len(path.parts) > 1:
            skills.add(f"area:{path.parts[0]}")
        lang = _EXT_LANG.get(path.suffix.lower())
        if lang:
            skills.add(f"lang:{lang}")
    return sorted(skills)


def skill_overlap(profile: SkillProfile, required: list[str], settings: Settings) -> float:
    if not required:
        return settings.NO_REQUIRED_SKILLS_OVERLAP
    have = profile.skill_map()
    return _clamp(sum(have[r].level if r in have else 0.0 for r in required) / len(required))


def stretch(profile: SkillProfile, required: list[str], effort: float, settings: Settings) -> float:
    """Gaussian around STRETCH_TARGET on gap = effort - comfort, plus a learning bonus."""
    have = profile.skill_map()
    comfort = sum(have[r].level for r in required if r in have) / len(required) if required else 0.5
    gap = effort - comfort
    score = math.exp(-(((gap - settings.STRETCH_TARGET) / settings.STRETCH_WIDTH) ** 2) / 2)
    learn = {w.lower() for w in profile.want_to_learn}
    if any(r.split(":", 1)[-1] in learn or r in learn for r in required):
        score += settings.LEARN_BONUS
    return _clamp(score)


def effort_fit(difficulty: DifficultyEstimate, hours_per_week: float | None, s: Settings) -> float:
    if hours_per_week is None or hours_per_week <= 0:
        return s.UNKNOWN_HOURS_EFFORT_FIT
    ratio = difficulty.est_hours_high / hours_per_week
    if ratio <= 1:
        return 1.0
    return _clamp(1 - (ratio - 1) / (s.EFFORT_FIT_ZERO_AT - 1))


def fit_score(breakdown: FitBreakdown, settings: Settings) -> float:
    weights = (
        settings.WEIGHT_SKILL,
        settings.WEIGHT_STRETCH,
        settings.WEIGHT_EFFORT,
        settings.WEIGHT_RESPONSIVENESS,
    )
    parts = (
        breakdown.skill_overlap,
        breakdown.stretch,
        breakdown.effort_fit,
        breakdown.responsiveness,
    )
    total = sum(weights)
    return _clamp(sum(w * p for w, p in zip(weights, parts, strict=True)) / total) if total else 0.0


def fit_label(score: float, s: Settings) -> FitLabel:
    if score >= s.FIT_LABEL_GREAT:
        return "Great fit"
    if score >= s.FIT_LABEL_GOOD:
        return "Good fit"
    if score >= s.FIT_LABEL_POSSIBLE:
        return "Possible fit"
    return "Weak match"


def confidence_label(confidence: float, s: Settings) -> ConfidenceLabel:
    if confidence >= s.CONFIDENCE_LABEL_HIGH:
        return "High confidence"
    if confidence >= s.CONFIDENCE_LABEL_MEDIUM:
        return "Medium confidence"
    return "Low confidence"


def effort_label(effort: float, s: Settings) -> EffortLabel:
    if effort < s.EFFORT_LABEL_SMALL:
        return "Small"
    if effort < s.EFFORT_LABEL_MEDIUM:
        return "Medium"
    if effort < s.EFFORT_LABEL_LARGE:
        return "Large"
    return "Very large"


def score_issue(
    profile: SkillProfile,
    difficulty: DifficultyEstimate,
    settings: Settings,
    responsiveness: float | None = None,
) -> Match:
    req = required_skills(difficulty)
    breakdown = FitBreakdown(
        skill_overlap=skill_overlap(profile, req, settings),
        stretch=stretch(profile, req, difficulty.effort, settings),
        effort_fit=effort_fit(difficulty, profile.hours_per_week, settings),
        responsiveness=(
            settings.DEFAULT_RESPONSIVENESS if responsiveness is None else _clamp(responsiveness)
        ),
    )
    have = profile.skill_map()
    matched = [have[r].confidence for r in req if r in have]
    skill_conf = sum(matched) / len(matched) if matched else settings.MIN_MATCH_CONFIDENCE
    comfort = sum(have[r].level for r in req if r in have) / len(req) if req else 0.5
    score = fit_score(breakdown, settings)
    confidence = min(difficulty.confidence, skill_conf)
    return Match(
        issue=difficulty.issue,
        score=score,
        breakdown=breakdown,
        difficulty=difficulty,
        evidence=list(difficulty.evidence),
        confidence=confidence,
        fit_label=fit_label(score, settings),
        confidence_label=confidence_label(confidence, settings),
        effort_label=effort_label(difficulty.effort, settings),
        stretch=breakdown.stretch >= settings.STRETCH_TAG_MIN and difficulty.effort > comfort,
    )


def rank(matches: list[Match], settings: Settings, top_n: int | None = None) -> list[Match]:
    """Confident picks first by score, then 'Less sure' picks; cut to top_n.

    This only orders recommendations. It never decides what a person may claim.
    """
    n = settings.TOP_N if top_n is None else top_n
    confident = [m for m in matches if m.confidence >= settings.MIN_CONFIDENCE]
    maybe = [m for m in matches if m.confidence < settings.MIN_CONFIDENCE]
    ordered = sorted(confident, key=lambda m: m.score, reverse=True) + sorted(
        maybe, key=lambda m: m.score, reverse=True
    )
    return ordered[:n]
