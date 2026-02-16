"""Event broadcasting for registry monitoring."""

import asyncio
import json
from typing import Set, Dict, Any
from datetime import datetime
from fastapi import WebSocket


class EventBroadcaster:
    """Broadcast registry events to connected WebSocket clients."""

    def __init__(self):
        """Initialize broadcaster."""
        self.active_connections: Set[WebSocket] = set()
        self.event_history: list = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket):
        """Connect a new client."""
        await websocket.accept()
        self.active_connections.add(websocket)

        # Send current state
        await self.send_to_client(websocket, {
            "event_type": "connected",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": {
                "message": "Connected to registry event stream",
                "history_count": len(self.event_history)
            }
        })

        # Send recent history
        for event in self.event_history[-20:]:
            await self.send_to_client(websocket, event)

    def disconnect(self, websocket: WebSocket):
        """Disconnect a client."""
        self.active_connections.discard(websocket)

    async def send_to_client(self, websocket: WebSocket, event: Dict[str, Any]):
        """Send event to a specific client."""
        try:
            await websocket.send_json(event)
        except:
            self.disconnect(websocket)

    async def broadcast(self, event_type: str, data: Dict[str, Any]):
        """Broadcast event to all connected clients."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "data": data
        }

        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(event)
            except:
                disconnected.add(connection)

        # Clean up disconnected clients
        self.active_connections -= disconnected
