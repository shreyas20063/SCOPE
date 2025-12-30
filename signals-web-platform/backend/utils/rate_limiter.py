"""
Rate Limiting for API Protection

Implements per-IP and global rate limiting to prevent abuse.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict
import threading
import logging

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: float = 30):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.

    Features:
    - Per-IP rate limiting
    - Global rate limiting
    - Burst allowance
    - Automatic cleanup of old entries
    """

    def __init__(
        self,
        requests_per_minute: int = 100,
        burst_size: int = 20,
        global_limit_per_minute: int = 10000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_minute: Max requests per IP per minute
            burst_size: Allowed burst in first 10 seconds
            global_limit_per_minute: Max global requests per minute
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.global_limit = global_limit_per_minute

        # Per-IP tracking: ip -> list of timestamps
        self._ip_requests: Dict[str, list] = defaultdict(list)

        # Global tracking
        self._global_requests: list = []
        self._global_minute_start: float = time.time()
        self._global_count: int = 0

        self._lock = threading.RLock()

        # Statistics
        self.total_requests = 0
        self.blocked_requests = 0

    def _cleanup_old_requests(self, requests: list, window_seconds: float = 60) -> list:
        """Remove requests older than the window."""
        cutoff = time.time() - window_seconds
        return [ts for ts in requests if ts > cutoff]

    def check_rate_limit(self, client_ip: str) -> Tuple[bool, float]:
        """
        Check if request is allowed for given IP.

        Returns:
            Tuple of (allowed: bool, retry_after: float)
        """
        now = time.time()

        with self._lock:
            self.total_requests += 1

            # Check global limit first
            if now - self._global_minute_start >= 60:
                self._global_count = 0
                self._global_minute_start = now

            self._global_count += 1

            if self._global_count > self.global_limit:
                self.blocked_requests += 1
                retry_after = 60 - (now - self._global_minute_start)
                logger.warning(f"Global rate limit exceeded: {self._global_count} requests")
                return False, max(retry_after, 1)

            # Clean up old requests for this IP
            self._ip_requests[client_ip] = self._cleanup_old_requests(
                self._ip_requests[client_ip]
            )

            requests = self._ip_requests[client_ip]

            # Check per-IP limit
            if len(requests) >= self.requests_per_minute:
                self.blocked_requests += 1
                # Calculate retry time
                oldest = min(requests) if requests else now
                retry_after = 60 - (now - oldest)
                logger.warning(f"Rate limit exceeded for IP {client_ip}: {len(requests)} requests")
                return False, max(retry_after, 1)

            # Check burst (first 10 seconds)
            recent_requests = [ts for ts in requests if now - ts < 10]
            if len(recent_requests) >= self.burst_size:
                self.blocked_requests += 1
                oldest_recent = min(recent_requests) if recent_requests else now
                retry_after = 10 - (now - oldest_recent)
                return False, max(retry_after, 1)

            # Request allowed
            self._ip_requests[client_ip].append(now)
            return True, 0

    def cleanup(self):
        """Clean up old entries to free memory."""
        with self._lock:
            # Remove IPs with no recent requests
            cutoff = time.time() - 120  # 2 minutes
            ips_to_remove = []

            for ip, requests in self._ip_requests.items():
                if not requests or max(requests) < cutoff:
                    ips_to_remove.append(ip)

            for ip in ips_to_remove:
                del self._ip_requests[ip]

            if ips_to_remove:
                logger.debug(f"Cleaned up {len(ips_to_remove)} inactive IP entries")

    def get_stats(self) -> dict:
        """Get rate limiter statistics."""
        with self._lock:
            return {
                "total_requests": self.total_requests,
                "blocked_requests": self.blocked_requests,
                "block_rate": round(
                    (self.blocked_requests / max(self.total_requests, 1)) * 100, 2
                ),
                "unique_ips": len(self._ip_requests),
                "global_count_current_minute": self._global_count,
                "limits": {
                    "per_ip_per_minute": self.requests_per_minute,
                    "burst_size": self.burst_size,
                    "global_per_minute": self.global_limit,
                }
            }


# Global rate limiter instance
# High limits for interactive simulations (sliders generate many requests)
rate_limiter = RateLimiter(
    requests_per_minute=1000,  # 1000 requests/min per IP (plenty for sliders)
    burst_size=100,            # Allow 100 requests in 10 seconds (rapid slider movement)
    global_limit_per_minute=50000,  # 50k global requests/min
)
