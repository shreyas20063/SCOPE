"""
Performance Monitoring and Analytics

Tracks request times, cache performance, and system health.
Provides data for research papers and debugging.
"""

import time
import json
import logging
import statistics
from typing import Dict, List, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import threading
import os

logger = logging.getLogger(__name__)

# Start time for uptime tracking
START_TIME = time.time()


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    endpoint: str
    method: str
    status_code: int
    duration_ms: float
    client_ip: str
    timestamp: float = field(default_factory=time.time)
    cache_hit: bool = False
    simulation_id: Optional[str] = None


class PerformanceMonitor:
    """
    Comprehensive performance monitoring.

    Features:
    - Request timing (p50, p95, p99)
    - Cache hit rate tracking
    - WebSocket connection monitoring
    - Error rate tracking
    - JSON logging for analysis
    """

    # Keep last N metrics per endpoint for percentile calculation
    MAX_METRICS_PER_ENDPOINT = 1000

    def __init__(self, log_dir: str = "logs"):
        self._lock = threading.RLock()

        # Response times by endpoint
        self._response_times: Dict[str, List[float]] = defaultdict(list)

        # Request counts
        self._request_counts: Dict[str, int] = defaultdict(int)

        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)

        # Total counters
        self.total_requests = 0
        self.total_errors = 0
        self.cache_hits = 0
        self.cache_misses = 0

        # WebSocket connections (updated by websocket_manager)
        self.ws_connections = 0

        # Logging
        self.log_dir = log_dir
        self._ensure_log_dir()
        self._log_file = self._open_log_file()

    def _ensure_log_dir(self):
        """Create log directory if it doesn't exist."""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

    def _open_log_file(self):
        """Open the request log file."""
        log_path = os.path.join(self.log_dir, "requests.log")
        return open(log_path, "a", buffering=1)  # Line buffered

    def record_request(self, metrics: RequestMetrics):
        """Record metrics for a completed request."""
        with self._lock:
            self.total_requests += 1
            self._request_counts[metrics.endpoint] += 1

            # Track response time
            times = self._response_times[metrics.endpoint]
            times.append(metrics.duration_ms)

            # Trim to max size
            if len(times) > self.MAX_METRICS_PER_ENDPOINT:
                self._response_times[metrics.endpoint] = times[-self.MAX_METRICS_PER_ENDPOINT:]

            # Track errors
            if metrics.status_code >= 400:
                self.total_errors += 1
                self._error_counts[metrics.endpoint] += 1

            # Track cache
            if metrics.cache_hit:
                self.cache_hits += 1
            else:
                self.cache_misses += 1

        # Log to file
        self._log_request(metrics)

    def _log_request(self, metrics: RequestMetrics):
        """Write request to log file."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(metrics.timestamp).isoformat(),
            "endpoint": metrics.endpoint,
            "method": metrics.method,
            "status": metrics.status_code,
            "duration_ms": round(metrics.duration_ms, 2),
            "client_ip": metrics.client_ip,
            "cache_hit": metrics.cache_hit,
            "simulation_id": metrics.simulation_id,
        }

        try:
            self._log_file.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning(f"Failed to write log: {e}")

    def _calculate_percentiles(self, times: List[float]) -> Dict[str, float]:
        """Calculate p50, p95, p99 percentiles."""
        if not times:
            return {"p50": 0, "p95": 0, "p99": 0}

        sorted_times = sorted(times)
        n = len(sorted_times)

        return {
            "p50": sorted_times[int(n * 0.50)] if n > 0 else 0,
            "p95": sorted_times[int(n * 0.95)] if n > 1 else sorted_times[-1],
            "p99": sorted_times[int(n * 0.99)] if n > 2 else sorted_times[-1],
        }

    def get_response_times(self) -> Dict[str, Dict[str, float]]:
        """Get response time percentiles by endpoint."""
        with self._lock:
            return {
                endpoint: self._calculate_percentiles(times)
                for endpoint, times in self._response_times.items()
            }

    @property
    def cache_hit_rate(self) -> float:
        """Cache hit rate (0.0 to 1.0)."""
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    @property
    def error_rate(self) -> float:
        """Error rate (0.0 to 1.0)."""
        if self.total_requests == 0:
            return 0.0
        return self.total_errors / self.total_requests

    @property
    def uptime_seconds(self) -> float:
        """Server uptime in seconds."""
        return time.time() - START_TIME

    def get_stats(self) -> dict:
        """Get comprehensive performance statistics."""
        with self._lock:
            return {
                "uptime_seconds": round(self.uptime_seconds, 2),
                "total_requests": self.total_requests,
                "total_errors": self.total_errors,
                "error_rate_percent": round(self.error_rate * 100, 3),
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_rate_percent": round(self.cache_hit_rate * 100, 2),
                "ws_connections": self.ws_connections,
                "response_times": self.get_response_times(),
                "requests_by_endpoint": dict(self._request_counts),
                "errors_by_endpoint": dict(self._error_counts),
            }

    def close(self):
        """Close log file on shutdown."""
        try:
            self._log_file.close()
        except Exception:
            pass


# Global monitor instance
monitor = PerformanceMonitor()


def log_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration_ms: float,
    client_ip: str,
    cache_hit: bool = False,
    simulation_id: Optional[str] = None,
):
    """Convenience function to log a request."""
    metrics = RequestMetrics(
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms,
        client_ip=client_ip,
        cache_hit=cache_hit,
        simulation_id=simulation_id,
    )
    monitor.record_request(metrics)
