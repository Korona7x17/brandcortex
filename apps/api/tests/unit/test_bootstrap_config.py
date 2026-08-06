"""Boot-time seeding: a reviewed file change reaches the database; a live edit survives it.

The bug this exists to prevent, in full: on 2026-08-06 a voice rule was written, tested, committed and
deployed, and every post the product made still ignored it — because `brand_config` is a database row
and nothing had run the seed loader against production. Green tests, correct file, correct code,
wrong output. Hours went into looking for a fault in the code.

The bug it must not introduce is the mirror image: a deploy silently reverting voice tuning somebody
did in `/settings/voice`, which would be worse, because that person has no reason to look.
"""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from brandcortex.core import brand_config as store
from brandcortex.db import bootstrap_config
from brandcortex.db.base import Base
from brandcortex.db.models import BrandConfig

DOCUMENT = {
    "brand": "testbrand",
    "display_name": "Test Brand",
    "voice": {"max_emoji": 1, "honorific": {"prefix": "คุณ", "locales": ["th"]}},
    "hashtags": {"core": ["#test"]},
}


@pytest.fixture
def session() -> Session:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


@pytest.fixture
def seed_file(tmp_path: Path) -> Path:
    path = tmp_path / "testbrand.brand_config.json"
    path.write_text(json.dumps(DOCUMENT, ensure_ascii=False), encoding="utf-8")
    return path


def test_creates_a_missing_row(session: Session, seed_file: Path) -> None:
    assert bootstrap_config.apply_seed(session, seed_file).startswith("created")
    assert store.load(session, "testbrand")["voice"]["max_emoji"] == 1


def test_second_boot_with_an_unchanged_file_does_nothing(session: Session, seed_file: Path) -> None:
    bootstrap_config.apply_seed(session, seed_file)
    assert bootstrap_config.apply_seed(session, seed_file) == "unchanged testbrand"


def test_a_changed_file_reaches_an_untouched_row(session: Session, seed_file: Path) -> None:
    """The whole point: ship the voice change with the deploy that carries it."""
    bootstrap_config.apply_seed(session, seed_file)

    changed = {**DOCUMENT, "voice": {**DOCUMENT["voice"], "max_emoji": 2}}
    seed_file.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")

    assert bootstrap_config.apply_seed(session, seed_file).startswith("updated")
    assert store.load(session, "testbrand")["voice"]["max_emoji"] == 2


def test_an_edited_row_is_never_overwritten(session: Session, seed_file: Path) -> None:
    """A deploy must not revert what someone tuned in the app.

    The file and the row have both moved on and they disagree. That is a conflict between two
    authorities, and picking a winner silently is how an operator's work disappears without anyone
    noticing it happened.
    """
    bootstrap_config.apply_seed(session, seed_file)

    edited = store.load(session, "testbrand")
    edited["voice"] = {**edited["voice"], "max_emoji": 4}
    store.save(session, edited)  # what /settings/voice does

    changed = {**DOCUMENT, "voice": {**DOCUMENT["voice"], "max_emoji": 2}}
    seed_file.write_text(json.dumps(changed, ensure_ascii=False), encoding="utf-8")

    assert bootstrap_config.apply_seed(session, seed_file) == "skipped-edited testbrand"
    assert store.load(session, "testbrand")["voice"]["max_emoji"] == 4


def test_the_manual_seed_command_still_forces_the_file_to_win(
    session: Session, seed_file: Path
) -> None:
    """The escape hatch out of `skipped-edited`.

    `db.seed` is unchanged: it calls `store.save` directly and always wins. That is right, because a
    person typed it — the refusal above is only about what a *deploy* may do unattended.
    """
    bootstrap_config.apply_seed(session, seed_file)
    edited = store.load(session, "testbrand")
    edited["voice"] = {**edited["voice"], "max_emoji": 4}
    store.save(session, edited)

    store.save(session, json.loads(seed_file.read_text(encoding="utf-8")))  # what db.seed does

    assert store.load(session, "testbrand")["voice"]["max_emoji"] == 1


def test_reindenting_the_file_is_not_a_change(session: Session, seed_file: Path) -> None:
    """Fingerprints compare meaning, not formatting — otherwise every reformat rewrites the row."""
    bootstrap_config.apply_seed(session, seed_file)
    seed_file.write_text(json.dumps(DOCUMENT, indent=4, ensure_ascii=False), encoding="utf-8")
    assert bootstrap_config.apply_seed(session, seed_file) == "unchanged testbrand"


def test_a_malformed_file_does_not_stop_the_boot(session: Session, tmp_path: Path) -> None:
    (tmp_path / "broken.brand_config.json").write_text("{not json", encoding="utf-8")
    (tmp_path / "testbrand.brand_config.json").write_text(
        json.dumps(DOCUMENT, ensure_ascii=False), encoding="utf-8"
    )

    results = bootstrap_config.apply_all(session, tmp_path)

    assert any(r.startswith("failed") for r in results)
    assert any(r.startswith("created") for r in results)
    assert session.get(BrandConfig, "testbrand") is not None
