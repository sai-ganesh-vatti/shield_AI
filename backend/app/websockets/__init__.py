import asyncio
import json
import logging
from typing import Set, Optional
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import District, Warehouse, Hospital, Truck, HealthStorm, SimulationEvent, NetworkMetrics
from app.services.simulation import HealthStormSimulator, NetworkMonitor

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.district_subscribers: Dict[int, Set[WebSocket]] = {}  # district_id -> connections
        self.truck_subscribers: Dict[int, Set[WebSocket]] = {}  # truck_id -> connections
    
    async def connect(self, websocket: WebSocket) -> None:
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self.active_connections.discard(websocket)
        # Remove from all district/track subscriptions
        for district_id in list(self.district_subscribers.keys()):
            self.district_subscribers[district_id].discard(websocket)
        for truck_id in list(self.truck_subscribers.keys()):
            self.truck_subscribers[truck_id].discard(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    def subscribe_district(self, websocket: WebSocket, district_id: int) -> None:
        """Subscribe a connection to district updates."""
        if district_id not in self.district_subscribers:
            self.district_subscribers[district_id] = set()
        self.district_subscribers[district_id].add(websocket)
    
    def unsubscribe_district(self, websocket: WebSocket, district_id: int) -> None:
        """Unsubscribe a connection from district updates."""
        if district_id in self.district_subscribers:
            self.district_subscribers[district_id].discard(websocket)
    
    def subscribe_truck(self, websocket: WebSocket, truck_id: int) -> None:
        """Subscribe a connection to truck updates."""
        if truck_id not in self.truck_subscribers:
            self.truck_subscribers[truck_id] = set()
        self.truck_subscribers[truck_id].add(websocket)
    
    async def broadcast_to_district(self, district_id: int, message: dict) -> None:
        """Broadcast a message to all subscribers of a district."""
        if district_id in self.district_subscribers:
            disconnected = set()
            for ws in self.district_subscribers[district_id]:
                try:
                    await ws.send_text(json.dumps(message))
                except Exception as e:
                    logger.error(f"Failed to send WS message: {e}")
                    disconnected.add(ws)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.district_subscribers[district_id].discard(ws)
    
    async def broadcast_to_all(self, message: dict) -> None:
        """Broadcast a message to all connected clients."""
        disconnected = set()
        for ws in self.active_connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WS message: {e}")
                disconnected.add(ws)
        
        for ws in disconnected:
            self.active_connections.discard(ws)
    
    async def broadcast_simulation_event(self, event: dict) -> None:
        """Broadcast a simulation event to all connected clients."""
        message = {
            "type": "simulation_event",
            "data": event,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_all(message)
    
    async def broadcast_health_storm(self, storm_data: dict) -> None:
        """Broadcast health storm update."""
        message = {
            "type": "health_storm_update",
            "data": storm_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_all(message)
    
    async def broadcast_truck_update(self, truck_data: dict) -> None:
        """Broadcast truck position update."""
        message = {
            "type": "truck_update",
            "data": truck_data,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_all(message)
    
    async def broadcast_network_metrics(self, metrics: dict) -> None:
        """Broadcast network metrics update."""
        message = {
            "type": "network_metrics",
            "data": metrics,
            "timestamp": datetime.utcnow().isoformat(),
        }
        await self.broadcast_to_all(message)


# Global manager instance
ws_manager = WebSocketManager()


async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Endpoint for WebSocket connections."""
    await ws_manager.connect(websocket)
    try:
        # Handle client messages/subscriptions
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            
            if msg_type == "subscribe_district":
                district_id = message.get("district_id")
                if district_id is not None:
                    ws_manager.subscribe_district(websocket, int(district_id))
                    
            elif msg_type == "subscribe_truck":
                truck_id = message.get("truck_id")
                if truck_id is not None:
                    ws_manager.subscribe_truck(websocket, int(truck_id))
                    
            elif msg_type == "get_network_metrics":
                # Send current metrics
                from app.services.simulation import NetworkMonitor
                # metrics = await NetworkMonitor(...).update_metrics()
                # await ws_manager.broadcast_network_metrics(metrics_data)
                pass
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)