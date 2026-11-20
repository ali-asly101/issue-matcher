from __future__ import annotations

from issuematch.config import Settings
from issuematch.models import DifficultyEstimate, FitBreakdown, IssueRef, Skill, SkillProfile
from issuematch.ranking import (
    confidence_label,
    effort_fit,
    effort_label,
    fit_label,
    fit_score,
    rank,
    required_skills,
    score_issue,
    stretch,
)


def est(n: int = 1, effort: float = 0.4, hours: float = 4, conf: float = 0.8) -> DifficultyEstimate:
    return DifficultyEstimate(
        issue=IssueRef(repo="o/r", number=n),
        effort=effort,
        est_hours_low=hours / 2,
        est_hours_high=hours,
        concepts=["async"],
        likely_files=["src/parser/core.py"],
        confidence=conf,
        source="history",
    )


def person(level: float = 0.5, **kw: object) -> SkillProfile:
    skills = [
        Skill(name=n, level=level, confidence=0.8)
        for n in ("lang:python", "area:src", "concept:async")
    ]
    return SkillProfile(person="me", skills=skills, **kw)  # type: ignore[arg-type]


def test_required_skills_from_estimate() -> None:
    assert required_skills(est()) == ["area:src", "concept:async", "lang:python"]


def test_fit_score_in_range_and_monotonic(settings: Settings) -> None:
    low = FitBreakdown(skill_overlap=0.2, stretch=0.5, effort_fit=0.5, responsiveness=0.5)
    high = low.model_copy(update={"skill_overlap": 0.9})
    assert 0 <= fit_score(low, settings) < fit_score(high, settings) <= 1


def test_stretch_peaks_at_target(settings: Settings) -> None:
    req = required_skills(est())
    p = person(level=0.5)
    at_target = stretch(p, req, 0.5 + settings.STRETCH_TARGET, settings)
    too_easy = stretch(p, req, 0.0, settings)
    too_hard = stretch(p, req, 1.0, settings)
    assert at_target > too_easy
    assert at_target > too_hard


def test_learning_bonus(settings: Settings) -> None:
    req = required_skills(est())
    base = stretch(person(level=0.2), req, 0.9, settings)
    learning = stretch(person(level=0.2, want_to_learn=["async"]), req, 0.9, settings)
    assert learning > base


def test_effort_fit(settings: Settings) -> None:
    assert effort_fit(est(hours=4), 5, settings) == 1.0
    assert effort_fit(est(hours=40), 5, settings) == 0.0
    assert effort_fit(est(hours=4), None, settings) == settings.UNKNOWN_HOURS_EFFORT_FIT


def test_rank_sorts_and_cuts_with_maybe_last(settings: Settings) -> None:
    p = person(level=0.6, hours_per_week=6)
    matches = [score_issue(p, est(n=i, effort=0.1 * i), settings) for i in range(1, 8)]
    unsure = score_issue(p, est(n=99, conf=0.1), settings)
    ranked = rank([*matches, unsure], settings, top_n=10)
    assert ranked[-1].issue.number == 99
    confident_scores = [m.score for m in ranked[:-1]]
    assert confident_scores == sorted(confident_scores, reverse=True)
    assert len(rank(matches, settings)) == settings.TOP_N


def test_fit_labels(settings: Settings) -> None:
    assert fit_label(settings.FIT_LABEL_GREAT, settings) == "Great fit"
    assert fit_label(settings.FIT_LABEL_GOOD, settings) == "Good fit"
    assert fit_label(settings.FIT_LABEL_POSSIBLE, settings) == "Possible fit"
    assert fit_label(0.0, settings) == "Weak match"


def test_confidence_and_effort_labels(settings: Settings) -> None:
    assert confidence_label(0.9, settings) == "High confidence"
    assert confidence_label(settings.CONFIDENCE_LABEL_MEDIUM, settings) == "Medium confidence"
    assert confidence_label(0.1, settings) == "Low confidence"
    assert effort_label(0.1, settings) == "Small"
    assert effort_label(0.4, settings) == "Medium"
    assert effort_label(0.6, settings) == "Large"
    assert effort_label(0.9, settings) == "Very large"


def test_match_carries_labels(settings: Settings) -> None:
    m = score_issue(person(level=0.6, hours_per_week=6), est(), settings)
    assert m.fit_label in {"Great fit", "Good fit", "Possible fit", "Weak match"}
    assert m.confidence_label.endswith("confidence")
    assert m.effort_label == "Medium"
