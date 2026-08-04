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

from datetime import datetime


class Scheduler:
    def __init__(self, brand_config: dict, playbook: dict) -> None:
        self._config = brand_config
        self._playbook = playbook

    def next_slot(
        self, *, brand: str, channel: str, source_type: str, after: datetime | None = None
    ) -> datetime:
        """Pick the next publish time honouring alternation, spacing, and preferred windows.

        TODO(phase-2): implement against already-scheduled posts for this brand+channel.
        """
        raise NotImplementedError
