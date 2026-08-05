"""Slot assignment for approved drafts (spec §7 step 5).

Three policies, all read from `brand_config.scheduling` and refined by the playbook's timing rules:

* **Source-type alternation** — for ThaiSwim, swimmer ↔ event, so the Page does not read as a single
  repeating format.
* **Minimum spacing** — no stacked posts; two posts an hour apart compete with each other for the same
  audience rather than reaching twice as many people.
* **Preferred windows** — learned per source type, in the brand's local timezone.

Timing is the lowest-risk lever in the system, which is why it is the one the spec allows to auto-tune
without an approval gate (§10.3). Voice and strategy changes do not get that.

Open decisions this touches: #4 (how much of Phase 2 scheduling to automate) and #5 (whether Phase 1
posts immediately or always schedules).
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

#: How far ahead to look before giving up on a policy. At one post a day, three weeks of candidates
#: is far more than any real queue, so exhausting it means the policy is unsatisfiable rather than
#: the calendar being busy.
HORIZON_DAYS = 21


@dataclass
class Slot:
    """A proposed publish time, and what shaped it.

    The reasons matter as much as the time. A scheduler that silently returns "Thursday" invites the
    reviewer to override it on instinct; one that says "Wednesday is taken, and the last post was
    also a swimmer" is arguing its case and can be disagreed with on the merits.
    """

    at: datetime
    reasons: list[str]
    relaxed: list[str]


@dataclass
class Booked:
    """An existing post occupying the calendar."""

    at: datetime
    source_type: str | None


class Scheduler:
    def __init__(self, brand_config: dict, playbook: dict | None = None) -> None:
        self._config = brand_config
        self._playbook = playbook or {}

    @property
    def _policy(self) -> dict:
        # The playbook may tune timing without an approval gate (§10.3) — the only lever it may move
        # unsupervised, because it is the cheapest to get wrong and the easiest to revert.
        policy = dict(self._config.get("scheduling") or {})
        learned = (self._playbook.get("timing.preferred_hours") or {}).get("hours")
        if learned:
            policy["preferred_hours"] = learned
        return policy

    def next_slot(
        self,
        *,
        booked: list[Booked],
        source_type: str,
        after: datetime | None = None,
    ) -> Slot:
        """The next publish time honouring preferred windows, spacing, daily cap and alternation.

        `booked` is every scheduled or published time for this brand and channel — the caller reads
        it, so the core stays free of queries and this stays testable without a database.

        Alternation is a preference, not a constraint. A queue of six swimmer cards must still get
        scheduled; when honouring it would push a post past the horizon, it is dropped and said so
        in `relaxed`. Spacing and the daily cap are never relaxed: those protect the audience from
        two posts competing for the same attention, which is a worse failure than a repeated format.
        """
        policy = self._policy
        tz = ZoneInfo(self._config.get("timezone", "UTC"))
        hours = sorted(policy.get("preferred_hours") or [9])
        spacing = timedelta(hours=float(policy.get("min_spacing_hours", 0)))
        per_day = int(policy.get("max_posts_per_day", 0) or 0)
        alternate = bool(policy.get("alternate_source_types"))

        start = (after or datetime.now(UTC)).astimezone(tz)
        reasons = [
            f"preferred hours {', '.join(f'{h:02d}:00' for h in hours)} {tz}",
        ]
        if spacing:
            reasons.append(f"at least {spacing.total_seconds() / 3600:g}h after the previous post")
        if per_day:
            reasons.append(f"at most {per_day} post{'s' if per_day > 1 else ''} a day")

        for require_alternation in ([True, False] if alternate else [False]):
            candidate = self._search(
                start, tz, hours, spacing, per_day, booked, source_type, require_alternation
            )
            if candidate is not None:
                relaxed = []
                if alternate and not require_alternation:
                    relaxed.append(
                        f"could not alternate away from {source_type} within {HORIZON_DAYS} days"
                    )
                elif alternate:
                    previous = [b for b in sorted(booked, key=lambda b: b.at) if b.at < candidate]
                    if previous and previous[-1].source_type:
                        # Name the post being alternated *away from*, not the one being placed.
                        reasons.append(f"alternates away from the previous {previous[-1].source_type}")
                return Slot(at=candidate.astimezone(UTC), reasons=reasons, relaxed=relaxed)

        raise ValueError(
            f"no slot within {HORIZON_DAYS} days satisfies spacing and the daily cap; "
            "the queue is fuller than the policy allows"
        )

    def _search(
        self, start, tz, hours, spacing, per_day, booked, source_type, require_alternation
    ) -> datetime | None:
        taken = sorted(booked, key=lambda b: b.at)
        for day in range(HORIZON_DAYS):
            date = (start + timedelta(days=day)).date()
            same_day = [b for b in taken if b.at.astimezone(tz).date() == date]
            if per_day and len(same_day) >= per_day:
                continue

            for hour in hours:
                candidate = datetime(date.year, date.month, date.day, hour, tzinfo=tz)
                if candidate <= start:
                    continue
                if spacing and any(abs(candidate - b.at) < spacing for b in taken):
                    continue
                if require_alternation:
                    previous = [b for b in taken if b.at < candidate]
                    if previous and previous[-1].source_type == source_type:
                        continue
                return candidate
        return None
