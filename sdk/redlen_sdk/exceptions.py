"""
SDK Exceptions
Custom exceptions for better error handling
"""


class RedlenSDKError(Exception):
    """Base exception for all SDK errors"""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)


class AuthenticationError(RedlenSDKError):
    """Raised when authentication fails"""
    pass


class RateLimitError(RedlenSDKError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: int = None, **kwargs):
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class NotFoundError(RedlenSDKError):
    """Raised when resource is not found"""
    pass


class ValidationError(RedlenSDKError):
    """Raised when request validation fails"""
    pass


class ServerError(RedlenSDKError):
    """Raised when server returns 5xx error"""
    pass


class NetworkError(RedlenSDKError):
    """Raised when network request fails"""
    pass
