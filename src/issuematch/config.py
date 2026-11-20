"""All tunables. See docs/CONTRACT.md section 4. Owner: Architect.

Every value has a comment with its meaning and unit. Override any value with an
environment variable prefixed ISSUEMATCH_ (for example ISSUEMATCH_TOP_N=10) or in .env.
Secrets (GITHUB_TOKEN, ANTHROPIC_API_KEY) are read separately and never have defaults.
"""

from __future__ import annotations

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ISSUEMATCH_", env_file=".env", extra="ignore", frozen=True
    )

    # --- App ---
    APP_NAME: str = "IssueMatch"  # display name; the only place the name lives
    DATA_DIR: Path = Path("data")  # where the SQLite cache lives (git-ignored)
    LOG_LEVEL: str = "INFO"  # Python logging level name

    # --- GitHub ---
    GITHUB_API_URL: str = "https://api.github.com/graphql"  # GraphQL endpoint
    GITHUB_PAGE_SIZE: int = 50  # items per GraphQL page (max 100)
    GITHUB_MAX_ISSUES: int = 2000  # cap per state (open/closed) per ingest (issues)
    GITHUB_CLOSED_HISTORY_DAYS: int = 730  # how far back closed issues are fetched (days)
    GITHUB_MIN_RATE_REMAINING: int = 100  # pause or stop below this many points left
    GITHUB_HTTP_TIMEOUT_SECONDS: float = 30.0  # per-request HTTP timeout (seconds)
    GITHUB_MAX_RETRIES: int = 5  # retries after 403/429/502/RATE_LIMITED before giving up (count)
    GITHUB_BACKOFF_BASE_SECONDS: float = 1.0  # first retry wait; doubles each retry (seconds)
    GITHUB_BACKOFF_MAX_SECONDS: float = 60.0  # cap on any computed back-off wait (seconds)
    GITHUB_BACKOFF_JITTER_FRACTION: float = 0.25  # random extra wait, up to this share of it (0-1)
    GITHUB_PR_FILES_CAP: int = 100  # max files read per pull request; cap is recorded (files)

    # --- Availability (docs/AVAILABILITY_SPEC.md) ---
    STALE_DAYS: int = 180  # no maintainer activity for this long -> stale (days)
    BLOCKED_LABELS: tuple[str, ...] = ("blocked", "on hold", "waiting for upstream")
    NEEDS_DESIGN_LABELS: tuple[str, ...] = ("needs design", "needs discussion", "rfc")
    NOT_ACTIONABLE_LABELS: tuple[str, ...] = ("question", "discussion", "wontfix", "invalid")

    # --- Ranking (docs/RANKING_SPEC.md) ---
    WEIGHT_SKILL: float = 0.40  # weight of skill overlap in the fit score (unitless)
    WEIGHT_STRETCH: float = 0.25  # weight of the stretch component (unitless)
    WEIGHT_EFFORT: float = 0.20  # weight of effort vs available time (unitless)
    WEIGHT_RESPONSIVENESS: float = 0.15  # weight of maintainer responsiveness (unitless)
    STRETCH_TARGET: float = 0.15  # ideal (effort - comfort) gap; >0 means a bit harder (0..1)
    STRETCH_WIDTH: float = 0.20  # how quickly stretch score falls off around the target (0..1)
    LEARN_BONUS: float = 0.15  # stretch bonus when a required skill is in want_to_learn (0..1)
    TOP_N: int = 5  # picks shown by default (issues)
    MIN_CONFIDENCE: float = 0.35  # picks below this go to the "maybe" list (0..1)
    UNKNOWN_HOURS_EFFORT_FIT: float = 0.7  # effort_fit used when hours_per_week is unknown
    EFFORT_FIT_ZERO_AT: float = 4.0  # effort_fit hits 0 at this multiple of weekly hours
    DEFAULT_RESPONSIVENESS: float = 0.5  # used until review latency is measured (0..1)
    NO_REQUIRED_SKILLS_OVERLAP: float = 0.5  # skill_overlap when an issue lists no skills
    MIN_MATCH_CONFIDENCE: float = 0.3  # confidence floor when no skills matched (0..1)

    # --- Labels people see instead of numbers (CLAUDE.md hard rule 11) ---
    FIT_LABEL_GREAT: float = 0.75  # score at or above -> "Great fit" (0..1)
    FIT_LABEL_GOOD: float = 0.55  # score at or above -> "Good fit" (0..1)
    FIT_LABEL_POSSIBLE: float = 0.35  # score at or above -> "Possible fit", below -> "Weak match"
    CONFIDENCE_LABEL_HIGH: float = 0.7  # confidence at or above -> "High confidence" (0..1)
    CONFIDENCE_LABEL_MEDIUM: float = 0.45  # at or above -> "Medium", below -> "Low confidence"
    EFFORT_LABEL_SMALL: float = 0.25  # effort below -> "Small" (0..1)
    EFFORT_LABEL_MEDIUM: float = 0.5  # effort below -> "Medium" (0..1)
    EFFORT_LABEL_LARGE: float = 0.75  # effort below -> "Large", at or above -> "Very large"
    STRETCH_TAG_MIN: float = 0.6  # stretch component at or above (and effort > comfort) -> tag

    # --- Skill profile and cold start (docs/SKILL_PROFILE_SPEC.md) ---
    EVIDENCE_CONFIDENCE: float = 0.8  # starting confidence for work evidence (0..1)
    CV_CONFIDENCE: float = 0.35  # max confidence of a skill backed only by a CV (0..1)
    DECLARED_CONFIDENCE: float = 0.3  # max confidence of a self-declared-only skill (0..1)
    DECLARED_MAX_LEVEL: float = 0.75  # level cap for declared skills until verified (0..1)
    VERIFIED_MIN_EVIDENCE: int = 3  # independent work items needed to mark a skill verified
    DECLARED_DECAY_DAYS: int = 180  # half-life of unbacked declared confidence (days)
    LEVEL_SATURATION: float = 5.0  # evidence count at which level reaches ~63% (items)
    COLD_START_MIN_SKILLS: int = 3  # fewer evidence-backed skills than this -> cold start flow
    COLD_START_PREFERRED_EFFORT: float = 0.4  # cold start: higher effort ranks lower, never hidden
    CV_MAX_BYTES: int = 5_000_000  # largest CV upload accepted (bytes)

    # --- Difficulty (docs/DIFFICULTY_SPEC.md) ---
    SIMILAR_K: int = 8  # closed neighbours used for the history estimate (issues)
    HISTORY_WEIGHT: float = 0.7  # share of history vs LLM in the blended estimate (0..1)
    EFFORT_LINES_SATURATION: int = 400  # changed lines that count as maximum effort (lines)

    # --- LLM ---
    LLM_MODEL: str = "claude-haiku-5-5"  # model for shortlist estimates; change freely
    LLM_SHORTLIST_SIZE: int = 25  # only this many issues per run reach the LLM (issues)
    LLM_MAX_TOKENS: int = 1024  # max output tokens per estimate call (tokens)
    LLM_BUDGET_USD_PER_RUN: float = 0.50  # stop calling the LLM past this spend (USD)

    # --- Embeddings ---
    EMBEDDING_BACKEND: str = "local"  # "local" (sentence-transformers) or "api"; see PLAN Q1
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"  # embedding model name for the backend
    DUPLICATE_SIMILARITY: float = 0.88  # cosine at or above this -> duplicate edge (0..1)

    # --- Map (docs/ISSUE_MAP_SPEC.md) ---
    MAP_MAX_NODES: int = 400  # nodes kept in an exported map (issues)
    SAME_FILES_MIN_OVERLAP: int = 1  # shared files needed for a same_files edge (files)


def github_token() -> str | None:
    """GitHub token from the environment. Never stored in Settings or logged."""
    return os.environ.get("GITHUB_TOKEN") or None


def anthropic_api_key() -> str | None:
    """Anthropic API key from the environment. Never stored in Settings or logged."""
    return os.environ.get("ANTHROPIC_API_KEY") or None
