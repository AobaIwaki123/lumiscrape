"""System-wide custom exceptions for lumiscrape."""


class LumiscrapeError(Exception):
    """Base exception for all lumiscrape errors."""


class ParseError(LumiscrapeError):
    """Raised when mechanical parsing fails or required fields are missing."""


class StorageError(LumiscrapeError):
    """Raised when object storage (MinIO) operations fail."""


class DatabaseError(LumiscrapeError):
    """Raised when database operations fail."""


class LLMFallbackError(LumiscrapeError):
    """Raised when autonomous LLM fallback fails."""
