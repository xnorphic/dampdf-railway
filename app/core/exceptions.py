# File: app/core/exceptions.py

from fastapi import HTTPException

class DamPDFException(Exception):
    def __init__(self, message: str, code: str = "INTERNAL_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)

class FileProcessingError(DamPDFException):
    def __init__(self, message: str):
        super().__init__(message, "FILE_PROCESSING_ERROR")

class FileTooLargeError(DamPDFException):
    def __init__(self, size_mb: float, max_size_mb: int):
        message = f"File size {size_mb:.1f}MB exceeds maximum {max_size_mb}MB"
        super().__init__(message, "FILE_TOO_LARGE")

class UnsupportedFileTypeError(DamPDFException):
    def __init__(self, file_type: str):
        message = f"File type '{file_type}' is not supported"
        super().__init__(message, "UNSUPPORTED_FILE_TYPE")

class SessionExpiredError(DamPDFException):
    def __init__(self):
        message = "Session has expired or not found"
        super().__init__(message, "SESSION_EXPIRED")

class RateLimitExceededError(DamPDFException):
    def __init__(self):
        message = "Rate limit exceeded. Please try again later or upgrade your plan."
        super().__init__(message, "RATE_LIMIT_EXCEEDED")
