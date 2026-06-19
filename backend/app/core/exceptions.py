class AppError(Exception):
    """Base application error with a user-facing message."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UnsupportedPlatformError(AppError):
    pass


class DownloadError(AppError):
    pass


class LLMServiceError(AppError):
    pass


class SubtitleExtractionError(AppError):
    pass
