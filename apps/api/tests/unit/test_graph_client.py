"""Tests for Graph API auth mechanics."""

from brandcortex.adapters.channel.facebook.client import GraphClient, appsecret_proof


class TestAppsecretProof:
    def test_matches_meta_reference_algorithm(self) -> None:
        """HMAC-SHA256 keyed by the app secret over the access token, hex-encoded.

        The expected digest was produced independently of this module, so the test cannot pass by
        agreeing with a buggy implementation:

            echo -n "TOKEN" | openssl dgst -sha256 -hmac "SECRET"
        """
        assert appsecret_proof("TOKEN", "SECRET") == (
            "9bcde7f1d5e226d86e4692a62e5ec88f99306fb302d74b2dc3bff8a03770b63d"
        )

    def test_key_order_is_secret_then_token(self) -> None:
        """Swapping them produces a valid-looking hex string that Meta rejects — an easy silent bug."""
        assert appsecret_proof("a", "b") != appsecret_proof("b", "a")

    def test_is_deterministic(self) -> None:
        assert appsecret_proof("t", "s") == appsecret_proof("t", "s")


class TestAuthParams:
    def test_includes_proof_when_secret_configured(self) -> None:
        client = GraphClient("TOKEN", version="v21.0", app_secret="SECRET")
        params = client._auth_params()
        assert params["access_token"] == "TOKEN"
        assert params["appsecret_proof"] == appsecret_proof("TOKEN", "SECRET")

    def test_omits_proof_when_no_secret(self) -> None:
        """Before 'Require app secret' is switched on, calls must still work."""
        assert "appsecret_proof" not in GraphClient("TOKEN", version="v21.0")._auth_params()

    def test_repr_does_not_leak_the_token(self) -> None:
        assert "TOKEN" not in repr(GraphClient("TOKEN", version="v21.0", app_secret="SECRET"))
