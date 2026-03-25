"""
Xeepy Rate Limiter

Handles rate limiting to avoid API/platform restrictions.
"""

import asyncio
import random
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional

from loguru import logger


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    requests_per_minute: int = 30
    requests_per_hour: int = 300
    min_delay: float = 0.5
    max_delay: float = 1.5


@dataclass
class RateLimitState:
    """Tracks rate limit state."""
    requests: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_request_time: float = 0.0
    cooldown_until: float = 0.0
    total_requests: int = 0
    rate_limited_count: int = 0


class RateLimiter:
    """
    Rate limiter with sliding window and adaptive delays.

    Accepts either a RateLimitConfig or keyword arguments for backwards
    compatibility.
    """

    def __init__(
        self,
        config: Optional["RateLimitConfig"] = None,
        max_per_minute: int = 30,
        max_per_hour: int = 300,
        jitter_range: tuple[float, float] = (0.5, 1.5),
    ):
        if config is not None:
            self.max_per_minute = config.requests_per_minute
            self.max_per_hour = config.requests_per_hour
            self.jitter_range = (config.min_delay, config.max_delay)
        else:
            self.max_per_minute = max_per_minute
            self.max_per_hour = max_per_hour
            self.jitter_range = jitter_range
        self.state = RateLimitState()
        self._lock = asyncio.Lock()
        # Per-action history: {action_name: [timestamps]}
        self._history: dict[str, list[float]] = {}

    async def wait(self, action: str = "default") -> float:
        """Wait appropriate delay for the given action and record it."""
        delay = random.uniform(self.jitter_range[0], self.jitter_range[1])
        await asyncio.sleep(delay)
        now = time.time()
        self._history.setdefault(action, []).append(now)
        self.state.requests.append(now)
        self.state.last_request_time = now
        self.state.total_requests += 1
        return delay

    def remaining(self, action: str = "default") -> int:
        """Return estimated remaining requests in the current minute."""
        now = time.time()
        minute_ago = now - 60
        recent = sum(1 for t in self.state.requests if t > minute_ago)
        return max(0, self.max_per_minute - recent)

    def is_limited(self, action: str = "default") -> bool:
        """Return True if the rate limit has been reached."""
        return self.remaining(action) == 0

    def reset(self) -> None:
        """Reset all state and history."""
        self.state = RateLimitState()
        self._history = {}
    
    async def acquire(self, weight: int = 1) -> float:
        """
        Acquire permission to make a request.
        
        Args:
            weight: Request weight (for expensive operations)
            
        Returns:
            Actual delay waited in seconds
        """
        async with self._lock:
            now = time.time()
            delay = 0.0
            
            # Check if in cooldown
            if now < self.state.cooldown_until:
                delay = self.state.cooldown_until - now
                await asyncio.sleep(delay)
                now = time.time()
            
            # Clean old requests
            self._clean_old_requests(now)
            
            # Check per-minute limit
            minute_ago = now - 60
            requests_last_minute = sum(1 for t in self.state.requests if t > minute_ago)
            
            if requests_last_minute >= self.max_per_minute:
                # Wait until oldest request in window expires
                oldest_in_minute = min(t for t in self.state.requests if t > minute_ago)
                wait_time = 60 - (now - oldest_in_minute) + random.uniform(*self.jitter_range)
                logger.debug(f"Rate limit: waiting {wait_time:.2f}s (per-minute limit)")
                await asyncio.sleep(wait_time)
                delay += wait_time
                now = time.time()
            
            # Check per-hour limit
            hour_ago = now - 3600
            requests_last_hour = sum(1 for t in self.state.requests if t > hour_ago)
            
            if requests_last_hour >= self.max_per_hour:
                oldest_in_hour = min(t for t in self.state.requests if t > hour_ago)
                wait_time = 3600 - (now - oldest_in_hour) + random.uniform(*self.jitter_range)
                logger.warning(f"Rate limit: waiting {wait_time:.2f}s (per-hour limit)")
                await asyncio.sleep(wait_time)
                delay += wait_time
                now = time.time()
            
            # Record request
            for _ in range(weight):
                self.state.requests.append(now)
            self.state.last_request_time = now
            self.state.total_requests += weight
            
            return delay
    
    def _clean_old_requests(self, now: float) -> None:
        """Remove requests older than 1 hour from tracking."""
        hour_ago = now - 3600
        while self.state.requests and self.state.requests[0] < hour_ago:
            self.state.requests.popleft()
    
    async def wait_random(self, min_seconds: float, max_seconds: float) -> float:
        """
        Wait a random amount of time with jitter.
        
        Returns:
            Actual delay waited
        """
        delay = random.uniform(min_seconds, max_seconds)
        jitter = random.uniform(*self.jitter_range)
        total_delay = delay * jitter
        await asyncio.sleep(total_delay)
        return total_delay
    
    def trigger_cooldown(self, seconds: float) -> None:
        """Trigger a cooldown period (e.g., after rate limit error)."""
        self.state.cooldown_until = time.time() + seconds
        self.state.rate_limited_count += 1
        logger.warning(f"Rate limiter: cooldown triggered for {seconds}s")
    
    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        return {
            "requests_last_minute": sum(1 for t in self.state.requests if t > minute_ago),
            "requests_last_hour": sum(1 for t in self.state.requests if t > hour_ago),
            "total_requests": self.state.total_requests,
            "rate_limited_count": self.state.rate_limited_count,
            "in_cooldown": now < self.state.cooldown_until,
            "cooldown_remaining": max(0, self.state.cooldown_until - now),
        }
    
    def reset(self) -> None:
        """Reset rate limiter state."""
        self.state = RateLimitState()


class ActionRateLimiter:
    """
    Specialized rate limiter for different action types.
    
    Different actions have different rate limits on X/Twitter.
    """
    
    def __init__(self):
        self.limiters = {
            "like": RateLimiter(max_per_minute=10, max_per_hour=30),
            "unlike": RateLimiter(max_per_minute=10, max_per_hour=30),
            "retweet": RateLimiter(max_per_minute=5, max_per_hour=20),
            "unretweet": RateLimiter(max_per_minute=5, max_per_hour=20),
            "comment": RateLimiter(max_per_minute=2, max_per_hour=5),
            "follow": RateLimiter(max_per_minute=3, max_per_hour=15),
            "unfollow": RateLimiter(max_per_minute=3, max_per_hour=15),
            "bookmark": RateLimiter(max_per_minute=10, max_per_hour=50),
            "search": RateLimiter(max_per_minute=5, max_per_hour=50),
            "default": RateLimiter(max_per_minute=30, max_per_hour=300),
        }
    
    def get(self, action_type: str) -> RateLimiter:
        """Get rate limiter for specific action type."""
        return self.limiters.get(action_type, self.limiters["default"])
    
    async def acquire(self, action_type: str, weight: int = 1) -> float:
        """Acquire permission for specific action type."""
        limiter = self.get(action_type)
        return await limiter.acquire(weight)
    
    def get_all_stats(self) -> dict:
        """Get stats for all action types."""
        return {action: limiter.get_stats() for action, limiter in self.limiters.items()}
