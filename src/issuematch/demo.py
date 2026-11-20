"""Built-in sample data so the CLI can be shown without a token. Not real issues."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from issuematch.models import Issue, IssueRef, LinkedPR

DEMO_REPO = "demo/tinyparser"


def demo_issues(now: datetime | None = None) -> list[Issue]:
    now = now or datetime.now(UTC)
    recent = now - timedelta(days=3)

    def ref(n: int) -> IssueRef:
        return IssueRef(repo=DEMO_REPO, number=n)

    def pr(n: int, files: list[str], state: str = "merged") -> LinkedPR:
        return LinkedPR(
            number=n,
            state=state,
            files_changed=files,
            additions=40,
            deletions=10,
            created_at=recent,
            merged_at=recent if state == "merged" else None,
        )

    return [
        Issue(
            ref=ref(10),
            title="Tokenizer crashes on unicode identifiers",
            body="Repro attached. Related to #12.",
            state="open",
            labels=["bug", "area/lexer"],
            created_at=recent,
            updated_at=recent,
            linked_prs=[pr(101, ["lexer/tokenize.py"], "closed")],
        ),
        Issue(
            ref=ref(11),
            title="Support raw string literals",
            body="Blocked by #10 since the tokenizer needs unicode first.",
            state="open",
            labels=["enhancement", "area/lexer"],
            created_at=recent,
            updated_at=recent,
        ),
        Issue(
            ref=ref(12),
            title="Better error messages for unexpected tokens",
            body="See #10 for one bad example.",
            state="open",
            labels=["good first issue", "area/errors"],
            created_at=recent,
            updated_at=recent,
            linked_prs=[pr(102, ["errors/report.py", "lexer/tokenize.py"], "closed")],
        ),
        Issue(
            ref=ref(13),
            title="Add async streaming parser API",
            body="Depends on #14.",
            state="open",
            labels=["enhancement", "area/parser"],
            created_at=recent,
            updated_at=recent,
        ),
        Issue(
            ref=ref(14),
            title="Refactor parser state machine",
            body="Needed before streaming work.",
            state="open",
            labels=["area/parser"],
            assignees=["maintainer1"],
            created_at=recent,
            updated_at=recent,
            linked_prs=[pr(103, ["parser/state.py"], "open")],
        ),
    ]
