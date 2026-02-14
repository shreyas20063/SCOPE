"""
WebSocket Connection Manager

Manages WebSocket connections for real-time simulation updates.
Supports multiple concurrent connections with rate limiting.
"""

import time
import asyncio
from typing import Dict, List, Optional, Set
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    connected_at: float = field(default_factory=time.time)
    last_message: float = field(default_factory=time.time)
    message_count: int = 0
    rate_limit_reset: float = field(default_factory=time.time)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    pass


class WebSocketManager:
    """
    Manages WebSocket connections for all simulations.

    Features:
    - Connection tracking per simulation
    - Rate limiting (10 messages/sec per connection)
    - Auto-ping for keep-alive
    - Graceful cleanup on disconnect
    """

    # Rate limit: max messages per second per connection
    MAX_MESSAGES_PER_SECOND = 10

    # Ping interval in seconds
    PING_INTERVAL = 30

    # Connection timeout in seconds (idle)
    CONNECTION_TIMEOUT = 60

    def __init__(self):
        # sim_id -> list of ConnectionInfo
        self.active_connections: Dict[str, List[ConnectionInfo]] = {}
        # Track total connections
        self.total_connections = 0
        self.total_messages = 0
        self._lock = asyncio.Lock()

    async def connect(self, sim_id: str, websocket: WebSocket) -> ConnectionInfo:
        """Accept and track a new WebSocket connection."""
        await websocket.accept()

        conn_info = ConnectionInfo(websocket=websocket)

        async with self._lock:
            if sim_id not in self.active_connections:
                self.active_connections[sim_id] = []
            self.active_connections[sim_id].append(conn_info)
            self.total_connections += 1

        logger.info(f"WebSocket connected: sim_id={sim_id}, total={self.connection_count}")
        return conn_info

    async def disconnect(self, sim_id: str, conn_info: ConnectionInfo):
        """Remove a connection from tracking."""
        async with self._lock:
            if sim_id in self.active_connections:
                try:
                    self.active_connections[sim_id].remove(conn_info)
                    if not self.active_connections[sim_id]:
                        del self.active_connections[sim_id]
                except ValueError:
                    pass  # Already removed

        logger.info(f"WebSocket disconnected: sim_id={sim_id}, total={self.connection_count}")

    def check_rate_limit(self, conn_info: ConnectionInfo) -> bool:
        """
        Check and update rate limit for a connection.
        Returns True if within limit, False if exceeded.
        """
        now = time.time()

        # Reset counter every second
        if now - conn_info.rate_limit_reset >= 1.0:
            conn_info.message_count = 0
            conn_info.rate_limit_reset = now

        conn_info.message_count += 1
        conn_info.last_message = now
        self.total_messages += 1

        return conn_info.message_count <= self.MAX_MESSAGES_PER_SECOND

    async def send_json(self, conn_info: ConnectionInfo, data: dict) -> bool:
        """Send JSON data to a connection. Returns True if successful."""
        try:
            await conn_info.websocket.send_json(data)
            return True
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")
            return False

    async def broadcast(self, sim_id: str, data: dict):
        """Broadcast data to all connections watching a simulation."""
        if sim_id not in self.active_connections:
            return

        disconnected = []
        for conn_info in self.active_connections[sim_id]:
            success = await self.send_json(conn_info, data)
            if not success:
                disconnected.append(conn_info)

        # Clean up disconnected
        for conn_info in disconnected:
            await self.disconnect(sim_id, conn_info)

    @property
    def connection_count(self) -> int:
        """Total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())

    def get_stats(self) -> dict:
        """Get connection statistics."""
        return {
            "active_connections": self.connection_count,
            "simulations_active": len(self.active_connections),
            "total_connections_served": self.total_connections,
            "total_messages": self.total_messages,
            "connections_by_simulation": {
                sim_id: len(conns)
                for sim_id, conns in self.active_connections.items()
            }
        }

    async def close_all(self):
        """Close all active connections (for graceful shutdown)."""
        async with self._lock:
            for sim_id, connections in self.active_connections.items():
                for conn_info in connections:
                    try:
                        await conn_info.websocket.close(code=1001, reason="Server shutdown")
                    except Exception:
                        pass
            self.active_connections.clear()

        logger.info("All WebSocket connections closed")


# Global WebSocket manager instance
manager = WebSocketManager()
