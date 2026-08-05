"""Runtime configuration, loaded from the environment.

`.env.example` at the repo root is the manifest of every variable read here. Nothing in this module
knows a brand or channel name: per-brand behaviour (voice, hashtags, tag targets, north-star weighting)
lives in the `brand_config` table, and per-channel credentials live encrypted in `channel_tokens`.
Settings here are infrastructure only.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    env: Literal["local", "staging", "production"] = Field("local", alias="BRANDCORTEX_ENV")
    log_level: str = Field("INFO", alias="BRANDCORTEX_LOG_LEVEL")

    # BrandCortex's own database — the only one we write.
    database_url: str = Field(..., alias="DATABASE_URL")

    # The brand DB seam. Read-only by contract: we select from `card_renders` and never write back.
    # Bind a genuinely read-only role here so the contract is enforced by the database, not by habit.
    brand_db_url: str | None = Field(None, alias="BRAND_DB_URL")

    # Base URL of the brand's site. Card render URLs and canonical links are derived from it, so
    # pointing this at a staging host is what makes local drafting safe.
    brand_site_url: str = Field("https://thaiswim.com", alias="BRAND_SITE_URL")

    # BrandCortex's own store for captured card PNGs. Not shared with the brand, which never writes
    # here: each card is fetched once at draft time and those exact bytes are what publish.
    asset_bucket: str = Field(..., alias="ASSET_BUCKET")
    asset_endpoint_url: str | None = Field(None, alias="ASSET_ENDPOINT_URL")
    asset_access_key_id: str | None = Field(None, alias="ASSET_ACCESS_KEY_ID")
    asset_secret_access_key: str | None = Field(None, alias="ASSET_SECRET_ACCESS_KEY")
    asset_region: str = Field("ap-southeast-1", alias="ASSET_REGION")

    # Fernet key for `channel_tokens`. Rotating it requires re-encrypting stored tokens.
    token_encryption_key: str = Field(..., alias="TOKEN_ENCRYPTION_KEY")

    # Generation engine.
    anthropic_api_key: str | None = Field(None, alias="ANTHROPIC_API_KEY")
    generation_model: str = Field("claude-sonnet-5", alias="GENERATION_MODEL")

    # Facebook adapter. Pin the Graph version: Meta renames insight metrics between versions.
    facebook_app_id: str | None = Field(None, alias="FACEBOOK_APP_ID")
    facebook_app_secret: str | None = Field(None, alias="FACEBOOK_APP_SECRET")
    facebook_graph_version: str = Field("v21.0", alias="FACEBOOK_GRAPH_VERSION")
    facebook_page_id: str | None = Field(None, alias="FACEBOOK_PAGE_ID")

    # Origins allowed to call this API from a browser — the review dashboard, which runs as its own
    # origin. Comma-separated. Defaults to local development; production sets the real host. Never a
    # wildcard: these endpoints approve and publish, so any page a reviewer has open would be able to
    # drive them.
    cors_allow_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"], alias="CORS_ALLOW_ORIGINS"
    )

    # Site analytics is the source of truth for traffic; FB's click count is not.
    analytics_provider: str = Field("plausible", alias="ANALYTICS_PROVIDER")
    analytics_api_key: str | None = Field(None, alias="ANALYTICS_API_KEY")
    analytics_site_id: str | None = Field(None, alias="ANALYTICS_SITE_ID")


    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        """Accept `a,b` as well as a JSON array.

        pydantic-settings parses a list-typed variable as JSON, which makes the natural env spelling
        — a comma-separated list — a startup crash rather than a setting.
        """
        if isinstance(value, str) and not value.strip().startswith("["):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings singleton. FastAPI routes depend on this, not on module globals."""
    return Settings()  # type: ignore[call-arg]
