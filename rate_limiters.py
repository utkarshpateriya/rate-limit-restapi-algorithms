"""
Rate limiting algorithm implementations.
Each limiter can be used as middleware with the FastAPI application.
"""

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict
import heapq


class RateLimiter(ABC):
    """Base class for all rate limiting algorithms."""

    @abstractmethod
    def is_allowed(self, client_id: str) -> bool:
        """Check if a request from the client is allowed."""
        pass

    @abstractmethod
    def reset(self):
        """Reset the limiter state."""
        pass


class FixedWindowCounter(RateLimiter):
    """
    Fixed Window Counter algorithm.
    Divides time into fixed windows and counts requests in each window.
    Simple but has edge case issues at window boundaries.
    """

    def __init__(self, window_size: int = 60, max_requests: int = 10):
        """
        Args:
            window_size: Time window in seconds
            max_requests: Maximum requests allowed per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Dict[str, tuple[int, int]] = {}  # {client_id: (window_start, request_count)}

    def is_allowed(self, client_id: str) -> bool:
        current_time = int(time.time())
        current_window = (current_time // self.window_size) * self.window_size

        if client_id not in self.requests:
            self.requests[client_id] = (current_window, 1)
            return True

        window_start, count = self.requests[client_id]

        if window_start == current_window:
            if count < self.max_requests:
                self.requests[client_id] = (current_window, count + 1)
                return True
            return False
        else:
            self.requests[client_id] = (current_window, 1)
            return True

    def reset(self):
        self.requests.clear()


class SlidingWindowLog(RateLimiter):
    """
    Sliding Window Log algorithm.
    Keeps a log of request timestamps and counts requests within the window.
    Most accurate but memory intensive.
    """

    def __init__(self, window_size: int = 60, max_requests: int = 10):
        """
        Args:
            window_size: Time window in seconds
            max_requests: Maximum requests allowed per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.logs: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_size

        # Remove old entries outside the window
        if client_id in self.logs:
            self.logs[client_id] = [ts for ts in self.logs[client_id] if ts > window_start]

        # Check if request is allowed
        if len(self.logs[client_id]) < self.max_requests:
            self.logs[client_id].append(current_time)
            return True

        return False

    def reset(self):
        self.logs.clear()


class SlidingWindowCounter(RateLimiter):
    """
    Sliding Window Counter algorithm.
    Hybrid approach combining fixed window and sliding window concepts.
    More memory efficient than sliding window log with better accuracy than fixed window.
    """

    def __init__(self, window_size: int = 60, max_requests: int = 10):
        """
        Args:
            window_size: Time window in seconds
            max_requests: Maximum requests allowed per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self.requests: Dict[str, list] = defaultdict(list)

    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()
        window_start = current_time - self.window_size

        # Remove old requests outside the window
        self.requests[client_id] = [ts for ts in self.requests[client_id] if ts > window_start]

        # Check if request is allowed
        if len(self.requests[client_id]) < self.max_requests:
            self.requests[client_id].append(current_time)
            return True

        return False

    def reset(self):
        self.requests.clear()


class TokenBucket(RateLimiter):
    """
    Token Bucket algorithm.
    Tokens are added to a bucket at a fixed rate. Each request consumes a token.
    Allows burst traffic up to bucket capacity while maintaining average rate limit.
    """

    def __init__(self, capacity: int = 10, refill_rate: float = 1.0):
        """
        Args:
            capacity: Maximum tokens in the bucket
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.buckets: Dict[str, tuple[float, float]] = {}  # {client_id: (tokens, last_refill_time)}

    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()

        if client_id not in self.buckets:
            self.buckets[client_id] = (self.capacity, current_time)
            return True

        tokens, last_refill = self.buckets[client_id]

        # Add tokens based on time elapsed
        elapsed = current_time - last_refill
        tokens = min(self.capacity, tokens + elapsed * self.refill_rate)

        if tokens >= 1:
            tokens -= 1
            self.buckets[client_id] = (tokens, current_time)
            return True

        self.buckets[client_id] = (tokens, current_time)
        return False

    def reset(self):
        self.buckets.clear()


class LeakyBucket(RateLimiter):
    """
    Leaky Bucket algorithm.
    Requests are added to a queue (bucket) and processed at a fixed rate.
    Provides smooth traffic flow and prevents burst traffic.
    """

    def __init__(self, capacity: int = 10, leak_rate: float = 1.0):
        """
        Args:
            capacity: Maximum requests in the bucket
            leak_rate: Requests processed per second
        """
        self.capacity = capacity
        self.leak_rate = leak_rate
        self.buckets: Dict[str, tuple[float, float]] = {}  # {client_id: (requests_in_bucket, last_leak_time)}

    def is_allowed(self, client_id: str) -> bool:
        current_time = time.time()

        if client_id not in self.buckets:
            self.buckets[client_id] = (1, current_time)
            return True

        requests, last_leak = self.buckets[client_id]

        # Leak requests based on time elapsed
        elapsed = current_time - last_leak
        requests = max(0, requests - elapsed * self.leak_rate)

        if requests < self.capacity:
            requests += 1
            self.buckets[client_id] = (requests, current_time)
            return True

        self.buckets[client_id] = (requests, current_time)
        return False

    def reset(self):
        self.buckets.clear()
