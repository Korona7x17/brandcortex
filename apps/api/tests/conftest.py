"""Shared fixtures.

Tests never reach the Graph API or a brand's real database. Channel adapters are exercised against
fakes that satisfy the protocol; the seam is the whole point of the architecture, so it is also what
makes the system testable.
"""

import pytest


@pytest.fixture
def brand_config() -> dict:
    """Minimal brand config. Deliberately not ThaiSwim's real one — core tests must pass for any
    brand, and a test that only passes for ThaiSwim would hide a leaked assumption."""
    return {
        "brand": "testbrand",
        "timezone": "Asia/Bangkok",
        "default_locale": "th",
        "voice": {"max_emoji": 1, "banned_phrases": [], "forbidden_echoes": []},
        "intro_bank": {"th": ["intro-a", "intro-b", "intro-c"]},
        "hashtags": {"core": ["#Test"]},
        "unit_labels": {"metre": "ม."},
        "north_star": {"utm_sessions": 1.0, "shares": 0.5, "reactions": 0.0},
        "scheduling": {"min_spacing_hours": 6, "alternate_source_types": True},
    }
