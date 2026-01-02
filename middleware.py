"""
Middleware for applying rate limiting to FastAPI endpoints.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Optional
from rate_limiters import RateLimiter


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply rate limiting to all requests or specific endpoints.
    """

    def __init__(self, app, rate_limiter: RateLimiter, get_client_id: Optional[Callable] = None):
        """
        Args:
            app: FastAPI application
            rate_limiter: RateLimiter instance to use
            get_client_id: Optional function to extract client ID from request.
                          Defaults to IP address.
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.get_client_id = get_client_id or self._default_get_client_id

    @staticmethod
    def _default_get_client_id(request: Request) -> str:
        """Extract client IP address from request."""
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        client_id = self.get_client_id(request)

        if not self.rate_limiter.is_allowed(client_id):
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded. Too many requests.",
                    "client_id": client_id
                }
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Client"] = client_id
        return response


class EndpointRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to apply different rate limiters to different endpoints.
    """

    def __init__(self, app, endpoint_limiters: dict, get_client_id: Optional[Callable] = None):
        """
        Args:
            app: FastAPI application
            endpoint_limiters: Dict mapping endpoint paths to RateLimiter instances
            get_client_id: Optional function to extract client ID from request
        """
        super().__init__(app)
        self.endpoint_limiters = endpoint_limiters
        self.get_client_id = get_client_id or self._default_get_client_id

    @staticmethod
    def _default_get_client_id(request: Request) -> str:
        """Extract client IP address from request."""
        if request.client:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next):
        # Get the limiter for this endpoint (if any)
        limiter = self.endpoint_limiters.get(request.url.path)

        if limiter:
            client_id = self.get_client_id(request)
            if not limiter.is_allowed(client_id):
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "detail": "Rate limit exceeded. Too many requests.",
                        "client_id": client_id,
                        "endpoint": request.url.path
                    }
                )

        response = await call_next(request)
        return response
