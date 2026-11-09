class ConvoxAiError(Exception):
    """Base class for errors this service raises on purpose."""

class RetryableError(ConvoxAiError):
    def __init__(self, message: str, *, retry_after_s: float | None = None) -> None:
        super().__init__(message)
        self.message = message
        # Some providers say how long to wait (HTTP Retry-After). None means "use backoff".
        self.retry_after_s = retry_after_s


class PermanentError(ConvoxAiError):
    """Bad input or an impossible request. Retrying won't help."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message