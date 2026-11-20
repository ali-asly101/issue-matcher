"""GitHub access. Every network call goes through GitHubClient. Owner: Ingest agent."""

from issuematch.github.client import GitHubClient, JSONObject
from issuematch.github.errors import (
    BadTokenError,
    GitHubError,
    GraphQLError,
    MissingTokenError,
    RateLimitExhaustedError,
    RetriesExhaustedError,
    UnexpectedResponseError,
)

__all__ = [
    "BadTokenError",
    "GitHubClient",
    "GitHubError",
    "GraphQLError",
    "JSONObject",
    "MissingTokenError",
    "RateLimitExhaustedError",
    "RetriesExhaustedError",
    "UnexpectedResponseError",
]
