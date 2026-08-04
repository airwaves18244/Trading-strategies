"""Cross-cutting exception hierarchy. PHASE 0 CONTRACT."""
from __future__ import annotations


class QbtError(Exception):
    """Base for all qbt errors."""


class ConfigError(QbtError):
    """Missing/invalid configuration (.env, yaml)."""


class ProviderError(QbtError):
    """Base for provider failures; carries provider name."""

    def __init__(self, message: str, provider: str = ""):
        super().__init__(message)
        self.provider = provider


class ProviderAuthError(ProviderError):
    """Bad/expired credentials. Includes ALGOPACK's 200-with-HTML-login case."""


class RateLimitError(ProviderError):
    """Provider rate limit hit; retry_after seconds if known."""

    def __init__(self, message: str, provider: str = "", retry_after: float | None = None):
        super().__init__(message, provider)
        self.retry_after = retry_after


class DataGapError(QbtError):
    """Requested range not available in store and provider cannot fill it."""


class SchemaError(QbtError):
    """CSV/parquet import does not match a documented event schema."""


class LookaheadError(QbtError):
    """Raised by the validation harness when a strategy reads the future."""
