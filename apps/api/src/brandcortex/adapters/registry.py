"""Runtime resolution of adapters by key.

This module exists so `core/` never imports a concrete adapter. The core asks for
`get_channel_adapter("facebook")`; it does not know what that string means. Registration happens here,
at the edge, where brand and channel names are allowed to appear.

Adding brand #2 or channel #2 = write the adapter, register it, add config. No core change.
"""

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


def bootstrap() -> None:
    """Register the adapters this deployment runs.

    Called once at app/worker startup. The only place in the codebase where brand and channel names are
    bound to implementations.

    TODO(phase-1): construct and register the ThaiSwim source adapter and the Facebook channel adapter,
    reading credentials from `channel_tokens`.
    """
    raise NotImplementedError("adapter bootstrap not implemented (Phase 1)")
