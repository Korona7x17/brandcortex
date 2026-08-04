"""Numeric grounding tests (`core.generation.claims`).

The failure this guards against is a caption asserting a number the card doesn't show. Half these tests
are the positive path; the other half are deliberately wrong copy, because a check never run against
known-bad input is untested code in a path that publishes to a real audience.
"""

from brandcortex.core.generation.claims import check, supported_numbers

# Shaped like a real swimmer snapshot.
FACTS = {
    "name": "ริน สืบสงวน",
    "club": "สมาคมราชกรีฑาสโมสร",
    "ageGroups": ["55-59"],
    "goldCount": 9,
    "goldStrokes": 4,
    "multiGold": True,
    "rankedCount": 9,
    "topRank": 1,
    "rows": [
        {"stroke": "backstroke", "distance": 50, "course": "LCM", "rank": 1, "time": "42.06"},
        {"stroke": "freestyle", "distance": 100, "course": "LCM", "rank": 2, "time": "1:02.35"},
    ],
    "season": "2025-2026",
}


class TestSupportedNumbers:
    def test_harvests_nested_and_embedded(self) -> None:
        got = supported_numbers(FACTS)
        assert {"9", "4", "1", "50", "100", "42.06", "1:02.35"} <= got
        # Embedded in strings: an age group and a season each contribute both endpoints.
        assert {"55", "59", "2025", "2026"} <= got

    def test_booleans_do_not_leak_as_one(self) -> None:
        """`isinstance(True, int)` is True in Python, so an unguarded walk would silently support 1."""
        assert supported_numbers({"multiGold": True, "flag": False}) == set()


class TestGroundedCopy:
    def test_accurate_caption_passes(self) -> None:
        text = "ริน สืบสงวน · รุ่น 55-59 — อันดับ 1 ของประเทศ 9 รายการ ครบ 4 ท่า"
        assert check(text, FACTS).ok

    def test_thai_numerals_are_understood(self) -> None:
        assert check("อันดับ ๑ ของประเทศ ๙ รายการ", FACTS).ok

    def test_links_are_not_scanned(self) -> None:
        """A URL's path digits assert nothing; scanning them trains people to ignore this check."""
        assert check("📊 https://thaiswim.com/swimmers/x?v=88123", FACTS).ok

    def test_hashtags_are_not_scanned(self) -> None:
        assert check("สรุป #Top100 #ThaiSwim2026", FACTS).ok


class TestUngroundedCopy:
    def test_inflated_count_is_caught(self) -> None:
        """The headline failure: copy claiming more than the card shows."""
        result = check("อันดับ 1 ของประเทศ 12 รายการ", FACTS)
        assert not result.ok
        assert "12" in result.unsupported

    def test_wrong_time_is_caught(self) -> None:
        result = check("ทำเวลา 41.06 ในท่ากรรเชียง 50 ม.", FACTS)
        assert not result.ok
        assert "41.06" in result.unsupported

    def test_invented_stroke_count_is_caught(self) -> None:
        result = check("ครบ 5 ท่า", FACTS)
        assert not result.ok
        assert "5" in result.unsupported

    def test_reports_each_bad_number_once(self) -> None:
        result = check("12 รายการ และอีก 12 รายการ", FACTS)
        assert result.unsupported == ["12"]

    def test_allowlist_covers_language_not_claims(self) -> None:
        """Small numbers appear as ordinary words; a brand extends this via brand_config."""
        assert check("อีก 2 ปีข้างหน้า", FACTS).ok
        assert not check("อีก 7 ปีข้างหน้า", FACTS).ok


class TestEventFacts:
    """Event cards state a top-N, which must come from the snapshot rather than the template."""

    EVENT = {"stroke": "backstroke", "distance": 50, "n": 10, "rowCount": 10, "season": "2025-2026"}

    def test_top_n_is_grounded(self) -> None:
        assert check("10 อันดับแรกของประเทศในฤดูกาล 2025-2026", self.EVENT).ok

    def test_top_n_mismatch_is_caught(self) -> None:
        """A short bucket returned 8 rows; the caption must not still promise 10."""
        short = {**self.EVENT, "n": 8, "rowCount": 8}
        result = check("10 อันดับแรกของประเทศ", short)
        assert not result.ok
        assert "10" in result.unsupported
