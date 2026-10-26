"""
In-Memory Rate Limiter
----------------------
Sliding-window rate limiter per client IP.
Maintains state purely in memory without persistence.
"""

import time
from collections import defaultdict
from typing import Dict, List
from fastapi import HTTPException, Request, status
from app.config import settings


class InMemoryRateLimiter:
    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_PER_MIN):
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, client_ip: str) -> None:
        """
        Validates whether the client IP has exceeded the allowed requests per minute.
        Raises HTTP 429 Too Many Requests if limit is breached.
        """
        now = time.time()
        window_start = now - 60.0

        # Purge timestamps older than 60 seconds
        recent = [ts for ts in self.requests[client_ip] if ts > window_start]
        self.requests[client_ip] = recent

        if len(recent) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute allowed. Please wait before retrying.",
            )

        self.requests[client_ip].append(now)

    def reset(self) -> None:
        """Clears all stored rate limit history (primarily for unit testing)."""
        self.requests.clear()


limiter = InMemoryRateLimiter()


def get_client_ip(request: Request) -> str:
    """Extracts client IP address safely considering X-Forwarded-For if present."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"
