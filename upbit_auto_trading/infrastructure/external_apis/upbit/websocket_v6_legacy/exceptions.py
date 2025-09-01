"""Custom exceptions for the WebSocket v6 client."""

class WebSocketError(Exception):
    """Base exception for all WebSocket-related errors."""
    pass

class ConnectionError(WebSocketError):
    """Raised when a connection fails."""
    pass

class SubscriptionError(WebSocketError):
    """Raised when a subscription request fails."""
    pass

class AuthenticationError(WebSocketError):
    """Raised when authentication for private channels fails."""
    pass
