"""Runtime resolution of adapters by key.

This module exists so `core/` never imports a concrete adapter. The core asks for
`get_channel_adapter("facebook")`; it does not know what that string means. Registration happens here,
at the edge, where brand and channel names are allowed to appear.

Adding brand #2 or channel #2 = write the adapter, register it, add config. No core change.
"""

from sqlalchemy.orm import Session

from brandcortex.adapters.base import ChannelAdapter, SourceAdapter

_SOURCE_ADAPTERS: dict[str, SourceAdapter] = {}
_CHANNEL_ADAPTERS: dict[str, ChannelAdapter] = {}


class AdapterNotRegistered(LookupError):
    pass


def register_source_adapter(brand: str, adapter: SourceAdapter) -> None:
    _SOURCE_ADAPTERS[brand] = adapter


def register_channel_adapter(channel: str, adapter: ChannelAdapter) -> None:
    _CHANNEL_ADAPTERS[channel] = adapter


def get_source_adapter(brand: str) -> SourceAdapter:
    try:
        return _SOURCE_ADAPTERS[brand]
    except KeyError as exc:
        raise AdapterNotRegistered(f"no source adapter registered for brand {brand!r}") from exc


def get_channel_adapter(channel: str) -> ChannelAdapter:
    try:
        return _CHANNEL_ADAPTERS[channel]
    except KeyError as exc:
        raise AdapterNotRegistered(f"no channel adapter registered for channel {channel!r}") from exc


def registered_brands() -> list[str]:
    return sorted(_SOURCE_ADAPTERS)


def registered_channels() -> list[str]:
    return sorted(_CHANNEL_ADAPTERS)


def clear() -> None:
    """Drop all registrations. For tests, so one test's adapters cannot leak into another's."""
    _SOURCE_ADAPTERS.clear()
    _CHANNEL_ADAPTERS.clear()


def bootstrap(session: Session | None = None) -> None:
    """Register the adapters this deployment runs.

    Called once at app/worker startup. The only place in the codebase where brand and channel names
    are bound to implementations — hence the local imports: pulling concrete adapters in at module
    scope would put them on the import path of anything that merely wanted to *resolve* one.

    Registering a brand also registers its post structures. They are brand copy, they live beside
    the adapter, and a source adapter without them produces items the engine cannot render — so
    binding the two together removes a way to half-configure a brand.

    `default_locale` is read from `brand_config` rather than defaulted here. A brand whose row is
    missing fails loudly at startup, which is the right time to find out: the quiet alternative is
    English captions over a Thai card, reaching the audience looking deliberate.
    """
    from brandcortex.adapters.channel.facebook.adapter import FacebookChannelAdapter
    from brandcortex.adapters.source.thaiswim import templates as thaiswim_templates
    from brandcortex.adapters.source.thaiswim.adapter import ThaiSwimSourceAdapter
    from brandcortex.config import get_settings
    from brandcortex.core import brand_config as brand_config_store
    from brandcortex.core.generation import templates
    from brandcortex.db.session import session_scope

    settings = get_settings()

    with session_scope(session) as db:
        config = brand_config_store.load(db, ThaiSwimSourceAdapter.brand)

    thaiswim = ThaiSwimSourceAdapter(
        settings.brand_site_url, default_locale=config.get("default_locale", "th")
    )
    register_source_adapter(thaiswim.brand, thaiswim)
    thaiswim_templates.register(templates)

    facebook = FacebookChannelAdapter()
    register_channel_adapter(facebook.channel, facebook)
