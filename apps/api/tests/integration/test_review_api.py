"""The HTTP surface the review dashboard talks to.

Phase 1's UI is a queue, a diff and two buttons, so these tests are mostly about what a reviewer can
*see*: the engine's original next to the current text, the card's own numbers next to the caption
asserting them, and the exact image bytes that will publish.

The status codes matter as much as the payloads. A rejected edit is a 422 carrying its reasons — the
reviewer needs to read them — a rejected *state change* is a 409, and a channel failure is a 502 over
a post the orchestrator has already marked `failed`. Collapsing those into one error would make "your
wording is wrong", "you already published this" and "Meta is down" look identical in the UI.
"""

import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from brandcortex.adapters import registry
from brandcortex.adapters.source.thaiswim import mapping
from brandcortex.adapters.source.thaiswim import templates as thaiswim_templates
from brandcortex.api.routes import content_items, posts
from brandcortex.core import brand_config as brand_config_store
from brandcortex.core.generation import templates
from brandcortex.db.session import get_session
from brandcortex.services import assets
from tests.conftest import FakeChannelAdapter
from tests.integration.test_persistence_pipeline import SWIMMER_ROW

SEED = Path(__file__).resolve().parents[2] / "seeds" / "thaiswim.brand_config.json"
SITE = "https://thaiswim.com"

CARD_BYTES = b"\x89PNG\r\n\x1a\nnot-a-real-png-but-these-exact-bytes-are-what-publishes"


@pytest.fixture(autouse=True)
def registered(monkeypatch):
    templates.clear()
    registry.clear()
    thaiswim_templates.register(templates)
    registry.register_channel_adapter(FakeChannelAdapter.channel, FakeChannelAdapter())

    stored: dict[str, bytes] = {}

    def capture(asset, *, post_id: str) -> str:
        key = f"cards/{post_id}.png"
        stored[key] = CARD_BYTES
        return key

    monkeypatch.setattr(assets, "capture", capture)
    monkeypatch.setattr(assets, "open_stored", lambda key: io.BytesIO(stored[key]))
    yield
    templates.clear()
    registry.clear()


@pytest.fixture
def client(session):
    brand_config_store.save(session, json.loads(SEED.read_text()))
    session.commit()

    app = FastAPI()
    app.include_router(content_items.router)
    app.include_router(posts.router)
    app.dependency_overrides[get_session] = lambda: session
    return TestClient(app)


@pytest.fixture
def envelope():
    return json.loads(mapping.row_to_content_item(SWIMMER_ROW, site_url=SITE).model_dump_json())


@pytest.fixture
def drafted(client, envelope) -> dict:
    response = client.post("/content-items", json=envelope)
    assert response.status_code == 200, response.text
    return response.json()


def test_ingest_returns_a_draft_the_reviewer_can_act_on(drafted):
    assert drafted["status"] == "draft"
    assert drafted["post_text"]
    assert drafted["utm_campaign"] in drafted["first_comment_text"]
    assert drafted["facts"]["goldCount"] == 9
    assert drafted["edited"] is False


def test_ingest_is_idempotent_over_http(client, envelope, drafted):
    again = client.post("/content-items", json=envelope)
    assert again.json()["id"] == drafted["id"]


def test_the_queue_lists_drafts_and_filters_by_status(client, drafted):
    assert [row["id"] for row in client.get("/posts?status=draft").json()] == [drafted["id"]]
    assert client.get("/posts?status=published").json() == []


def test_the_card_served_is_the_captured_copy(client, drafted):
    """Not a proxy to the brand's render URL. The reviewer approves the bytes that ship."""
    response = client.get(f"/posts/{drafted['id']}/card")

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == CARD_BYTES


def test_an_edit_is_visible_as_an_edit(client, drafted):
    response = client.patch(
        f"/posts/{drafted['id']}", json={"post_text": drafted["post_text"] + " ครับ"}
    )
    body = response.json()

    assert response.status_code == 200
    assert body["edited"] is True
    assert body["generated"]["post_text"] == drafted["post_text"]


def test_a_rejected_edit_returns_reasons_the_reviewer_can_read(client, drafted):
    response = client.patch(
        f"/posts/{drafted['id']}", json={"post_text": drafted["post_text"] + " 23 เหรียญทอง"}
    )

    assert response.status_code == 422
    assert any("23" in reason for reason in response.json()["detail"]["reasons"])


def test_publishing_before_approval_is_a_conflict_not_a_validation_error(client, drafted):
    assert client.post(f"/posts/{drafted['id']}/publish").status_code == 409


def test_approve_then_publish_records_the_channel_ids(client, drafted):
    approved = client.post(f"/posts/{drafted['id']}/approve")
    assert approved.status_code == 200, approved.text
    assert approved.json()["status"] == "approved"

    published = client.post(f"/posts/{drafted['id']}/publish").json()
    assert published["status"] == "published"
    assert published["channel_post_id"] == "page_1_post_1"
    assert published["channel_comment_id"] == "comment-1"


def test_a_channel_failure_is_a_502_over_a_post_left_recoverable(client, drafted):
    registry.register_channel_adapter(
        FakeChannelAdapter.channel, FakeChannelAdapter(error=RuntimeError("graph: token expired"))
    )
    client.post(f"/posts/{drafted['id']}/approve")

    assert client.post(f"/posts/{drafted['id']}/publish").status_code == 502

    after = client.get(f"/posts/{drafted['id']}").json()
    assert after["status"] == "failed"
    assert "token expired" in after["error"]
    assert after["post_text"], "everything needed to retry is still on the row"


def test_a_missing_post_is_a_404_whatever_the_id_looks_like(client):
    assert client.get("/posts/not-a-uuid").status_code == 404
    assert client.get(f"/posts/{datetime(2026, 1, 1, tzinfo=UTC).isoformat()}").status_code == 404
