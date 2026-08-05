"""The Facebook adapter, against a fake Graph.

No token and no network. `respx` intercepts httpx, so every branch that matters — including the ones
that only happen at 3am — is exercised before a real credential exists.

The failure modes are the point of this file. Publishing succeeds in one way and fails in several,
and the several are what decide whether a broken post is recoverable or merely lost.
"""

import httpx
import pytest
import respx

from brandcortex.adapters.channel.facebook.adapter import CommentFailed, FacebookChannelAdapter
from brandcortex.adapters.channel.facebook.client import GraphAuthError, GraphClient, GraphError
from brandcortex.schemas.draft import GeneratedDraft, PublishRequest

GRAPH = "https://graph.facebook.com/v21.0"
PAGE = "1223598310834457"
CARD = b"\x89PNG\r\n\x1a\nfake"


@pytest.fixture
def adapter(monkeypatch):
    """An adapter with the database and the asset store stubbed out — only Graph is under test."""
    import contextlib
    import io

    from brandcortex.services import assets

    monkeypatch.setattr(assets, "open_stored", lambda key: io.BytesIO(CARD))

    @contextlib.contextmanager
    def no_session():
        yield None

    return FacebookChannelAdapter(
        page_id=PAGE,
        session_factory=no_session,
        client_factory=lambda _s: GraphClient("test-token", version="v21.0", app_secret="secret"),
    )


@pytest.fixture
def request_():
    return PublishRequest(
        brand="testbrand",
        asset_storage_key="cards/x.png",
        draft=GeneratedDraft(
            post_text="อันดับ 1 ของประเทศ 9 รายการ",
            first_comment_text="📊 สถิติทั้งหมด\nhttps://thaiswim.com/swimmers/x?utm_campaign=swimmer-abc",
        ),
    )


class TestPublish:
    @respx.mock
    def test_photo_then_comment_in_that_order(self, adapter, request_) -> None:
        photo = respx.post(f"{GRAPH}/{PAGE}/photos").mock(
            return_value=httpx.Response(200, json={"id": "photo_1", "post_id": "page_post_1"})
        )
        comment = respx.post(f"{GRAPH}/page_post_1/comments").mock(
            return_value=httpx.Response(200, json={"id": "comment_1"})
        )

        result = adapter.publish(request_)

        assert result.channel_post_id == "page_post_1"
        assert result.channel_comment_id == "comment_1"
        assert photo.called and comment.called

    @respx.mock
    def test_the_image_is_uploaded_not_linked(self, adapter, request_) -> None:
        """Handing Meta a URL would put the render timing in their hands. These bytes were approved."""
        route = respx.post(f"{GRAPH}/{PAGE}/photos").mock(
            return_value=httpx.Response(200, json={"post_id": "p1"})
        )
        respx.post(f"{GRAPH}/p1/comments").mock(return_value=httpx.Response(200, json={"id": "c1"}))

        adapter.publish(request_)

        body = route.calls.last.request.content
        assert CARD in body, "the captured bytes must be in the request"
        assert b"url" not in route.calls.last.request.url.query

    @respx.mock
    def test_the_page_scoped_id_is_preferred_over_the_photo_id(self, adapter, request_) -> None:
        """`id` is the photo object; `post_id` is what insights and permalinks are keyed by."""
        respx.post(f"{GRAPH}/{PAGE}/photos").mock(
            return_value=httpx.Response(200, json={"id": "photo_9", "post_id": "page_post_9"})
        )
        respx.post(f"{GRAPH}/page_post_9/comments").mock(
            return_value=httpx.Response(200, json={"id": "c"})
        )

        assert adapter.publish(request_).channel_post_id == "page_post_9"

    @respx.mock
    def test_a_failed_comment_still_reports_the_live_post_id(self, adapter, request_) -> None:
        """The photo is on the Page whatever happens next. A post whose id we did not record is one
        nobody can find to fix or delete."""
        respx.post(f"{GRAPH}/{PAGE}/photos").mock(
            return_value=httpx.Response(200, json={"post_id": "live_post"})
        )
        respx.post(f"{GRAPH}/live_post/comments").mock(
            return_value=httpx.Response(403, json={"error": {"code": 200, "type": "OAuthException"}})
        )

        with pytest.raises(CommentFailed) as exc:
            adapter.publish(request_)

        assert exc.value.channel_post_id == "live_post"

    @respx.mock
    def test_the_token_never_appears_in_a_url(self, adapter, request_) -> None:
        """URLs reach access logs, proxies and error trackers. Form bodies generally do not."""
        route = respx.post(f"{GRAPH}/{PAGE}/photos").mock(
            return_value=httpx.Response(200, json={"post_id": "p"})
        )
        respx.post(f"{GRAPH}/p/comments").mock(return_value=httpx.Response(200, json={"id": "c"}))

        adapter.publish(request_)

        assert "test-token" not in str(route.calls.last.request.url)
        assert b"appsecret_proof" in route.calls.last.request.content


class TestErrorsAreSortedCorrectly:
    """Retrying the wrong failure is how a loud problem becomes a slow one."""

    @respx.mock
    def test_a_rate_limit_is_retried(self) -> None:
        route = respx.get(f"{GRAPH}/thing").mock(
            side_effect=[
                httpx.Response(200, json={"error": {"code": 4, "type": "OAuthException"}}),
                httpx.Response(200, json={"ok": True}),
            ]
        )
        assert GraphClient("t", version="v21.0").get("thing") == {"ok": True}
        assert route.call_count == 2

    @respx.mock
    def test_an_invalid_token_is_not_retried(self) -> None:
        route = respx.get(f"{GRAPH}/thing").mock(
            return_value=httpx.Response(200, json={"error": {"code": 190, "type": "OAuthException"}})
        )
        with pytest.raises(GraphAuthError):
            GraphClient("t", version="v21.0").get("thing")
        assert route.call_count == 1, "a person must re-authorize; retrying only delays that"

    @respx.mock
    def test_graph_prose_is_not_echoed_back(self) -> None:
        """Meta's message can quote the request, which carries the token."""
        respx.get(f"{GRAPH}/thing").mock(
            return_value=httpx.Response(
                200,
                json={
                    "error": {
                        "code": 100,
                        "type": "GraphMethodException",
                        "message": "Bad request: access_token=SECRET-VALUE",
                    }
                },
            )
        )
        with pytest.raises(GraphError) as exc:
            GraphClient("t", version="v21.0").get("thing")
        assert "SECRET-VALUE" not in str(exc.value)
        assert "code=100" in str(exc.value)


class TestInsights:
    @respx.mock
    def test_metrics_are_normalized_and_the_raw_payload_kept(self, adapter) -> None:
        respx.get(f"{GRAPH}/p1/insights").mock(
            return_value=httpx.Response(
                200,
                json={
                    "data": [
                        {"name": "post_impressions", "values": [{"value": 4210}]},
                        {"name": "post_impressions_unique", "values": [{"value": 3180}]},
                        {"name": "post_clicks", "values": [{"value": 96}]},
                        {
                            "name": "post_reactions_by_type_total",
                            "values": [{"value": {"like": 120, "love": 18}}],
                        },
                    ]
                },
            )
        )
        respx.get(f"{GRAPH}/p1").mock(
            return_value=httpx.Response(
                200, json={"shares": {"count": 22}, "comments": {"summary": {"total_count": 7}}}
            )
        )

        snap = adapter.fetch_insights("p1")

        assert (snap.reach, snap.impressions, snap.link_clicks) == (3180, 4210, 96)
        assert snap.reactions == 138, "reaction types are summed, not counted"
        assert (snap.shares, snap.comments) == (22, 7)
        assert snap.raw["insights"]["data"], "kept whole — Meta renames metrics between versions"

    @respx.mock
    def test_a_missing_metric_stays_missing(self, adapter) -> None:
        """Zero is a claim that nothing happened. Absent is not the same thing, and the learning
        loop weights them differently."""
        respx.get(f"{GRAPH}/p2/insights").mock(return_value=httpx.Response(200, json={"data": []}))
        respx.get(f"{GRAPH}/p2").mock(return_value=httpx.Response(200, json={}))

        snap = adapter.fetch_insights("p2")

        assert snap.reach is None and snap.shares is None and snap.reactions is None

    @respx.mock
    def test_saves_is_never_invented(self, adapter) -> None:
        """Meta exposes no reliable Page-post saves metric. A plausible proxy would get weighted."""
        respx.get(f"{GRAPH}/p3/insights").mock(return_value=httpx.Response(200, json={"data": []}))
        respx.get(f"{GRAPH}/p3").mock(return_value=httpx.Response(200, json={}))

        assert adapter.fetch_insights("p3").saves is None
