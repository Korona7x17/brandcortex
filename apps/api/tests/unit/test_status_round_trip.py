"""A status written to the database has to come back as the same thing.

This looks like a test of SQLAlchemy rather than of BrandCortex, and it is not. Every transition in
the orchestrator is an identity comparison — `post.status is PostStatus.DRAFT` — and a status column
declared as a plain `String` writes correctly, reads back as a bare `str`, and makes all of them
silently False.

What makes that worth a dedicated test is where it hides. An object still in the session's identity
map keeps the enum member that was assigned to it, so the pipeline tests pass end to end. The break
only appears once a *different* session loads the row — which is to say, once a reviewer clicks
approve in a request that did not create the draft. It was found by a test that happened to reload,
and this is the test that will find it next time.
"""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from brandcortex.db.models import (
    Experiment,
    ExperimentStatus,
    PlaybookRule,
    PlaybookRuleStatus,
    Post,
    PostStatus,
)

CASES = [
    (Post, PostStatus, PostStatus.APPROVED),
    (PlaybookRule, PlaybookRuleStatus, PlaybookRuleStatus.ACTIVE),
    (Experiment, ExperimentStatus, ExperimentStatus.RUNNING),
]


def _row(model, status):
    common = {"id": uuid.uuid4(), "brand": "testbrand", "status": status}
    if model is Post:
        return Post(**common, content_id="c1", channel="testchannel")
    if model is PlaybookRule:
        return PlaybookRule(**common, rule_key="timing.hour", version=1, rule="post at 20:00")
    return Experiment(**common, lever="intro_line")


def _draft(**overrides):
    return Post(
        id=uuid.uuid4(),
        brand="testbrand",
        content_id="c1",
        channel="testchannel",
        status=PostStatus.DRAFT,
        **overrides,
    )


@pytest.mark.parametrize(
    ("model", "enum_cls", "status"), CASES, ids=lambda v: getattr(v, "__name__", str(v))
)
def test_status_reloads_as_an_enum_member_not_a_string(session, model, enum_cls, status) -> None:
    row = _row(model, status)
    session.add(row)
    session.commit()

    # A genuinely separate session. Reusing `session` would hand back the identity-mapped object and
    # prove nothing — which is exactly how this bug survived the first time.
    with sessionmaker(bind=session.get_bind(), future=True)() as fresh:
        loaded = fresh.get(model, row.id)
        assert loaded.status is status, "identity comparison is what the state machines rest on"
        assert isinstance(loaded.status, enum_cls)


def test_the_stored_value_is_the_lowercase_one(session) -> None:
    """`draft`, not `DRAFT`. An API filter passes the string straight through, and a human reading
    the table should see what the UI shows."""
    post = _draft()
    session.add(post)
    session.commit()

    stored = (
        session.get_bind()
        .connect()
        .exec_driver_sql(
            "SELECT status FROM posts WHERE id = ?", (str(post.id).replace("-", ""),)
        )
        .scalar()
    )
    assert stored == "draft"


def test_filtering_by_the_plain_string_still_works(session) -> None:
    """The review UI sends `?status=draft`. The column type has to accept that, not only the enum."""
    session.add(_draft())
    session.commit()

    assert session.scalars(select(Post).where(Post.status == "draft")).all()
    assert not session.scalars(select(Post).where(Post.status == "published")).all()
