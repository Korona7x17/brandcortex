"""Enumerations shared across models.

None of these name a brand or a channel. `brand` and `channel` are free-form keyed strings resolved
through the adapter registry, so adding IG or brand #2 never touches this file.
"""

from enum import StrEnum

from sqlalchemy import Enum as SAEnum


def status_column(enum_cls: type[StrEnum], *, length: int = 16) -> SAEnum:
    """Column type for a status enum: a VARCHAR that still comes back as an enum member.

    Declaring these as a plain `String` is the obvious thing, and it is wrong in a way that hides.
    The value writes fine but loads back as a bare `str`, so every `status is PostStatus.DRAFT` in
    the codebase silently evaluates False against a row read from the database, while continuing to
    work on the object still in the identity map. The orchestrator's state machine is built on those
    comparisons; the symptom is an approve button that 409s in production and passes every test that
    never reloads the row.

    `native_enum=False` keeps the storage a VARCHAR — no Postgres ENUM type, so adding a status is
    an ordinary migration rather than an `ALTER TYPE`. `values_callable` stores `draft` rather than
    `DRAFT`, which keeps the column readable in a query and lets an API filter pass the string
    straight through.
    """
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        values_callable=lambda enum: [member.value for member in enum],
    )


class PostStatus(StrEnum):
    """Lifecycle of a post inside BrandCortex.

    Note this is *our* authoritative record of "posted to channel". The brand's own engine history
    means "content generated / available" and is a different event entirely (spec §4.4).
    """

    DRAFT = "draft"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"


class PlaybookRuleStatus(StrEnum):
    PROPOSED = "proposed"  # reflection agent suggested it; awaiting the approval gate
    ACTIVE = "active"  # generation engine and scheduler read this
    RETIRED = "retired"  # superseded or rolled back; kept for revertibility


class ExperimentStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    CONCLUDED = "concluded"
    ABANDONED = "abandoned"
