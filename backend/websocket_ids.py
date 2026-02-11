"""
WebSocket Handler for Real-Time IDS Alerts
Pushes threat detections to connected clients in real-time

Features:
- Live alert streaming to dashboard
- Alert subscriptions by threat level
- Metric updates
- Model status notifications

Author: J.A.R.V.I.S. IDS WebSocket Team
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Set
import json
import asyncio
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class MessageType(str, Enum):
    """WebSocket message types"""
    ALERT = "alert"
    METRICS = "metrics"
    MODEL_STATUS = "model_status"
    DRIFT_DETECTION = "drift_detection"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    PING = "ping"
    PONG = "pong"


class AlertSubscription(str, Enum):
    """Alert subscription filters"""
    ALL = "all"
    CRITICAL = "critical"
    HIGH_AND_ABOVE = "high_and_above"
    THREAT_DETECTION_ONLY = "threat_detection"


# ============================================================================
# CONNECTION MANAGER
# ============================================================================

class IDSConnectionManager:
    """
    Manages WebSocket connections for IDS alert streaming
    
    Features:
    - Multiple concurrent connections
    - Per-connection subscription management
    - Broadcast and targeted messaging
    - Connection health monitoring
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, Set[AlertSubscription]] = {}
        self.client_ids: Dict[WebSocket, str] = {}
        self.message_history: List[Dict] = []
        self.max_history = 100

    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = {AlertSubscription.ALL}
        self.client_ids[websocket] = client_id
        
        logger.info(f"Client connected: {client_id}")
        
        # Send connection confirmation
        await websocket.send_json({
            "type": MessageType.PING,
            "message": "Connected to IDS alert stream",
            "timestamp": datetime.now().isoformat(),
            "client_id": client_id
        })

    def disconnect(self, websocket: WebSocket) -> None:
        """Unregister WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            client_id = self.client_ids.pop(websocket, "unknown")
            self.subscriptions.pop(websocket, None)
            logger.info(f"Client disconnected: {client_id}")

    async def subscribe(self, websocket: WebSocket, subscription: AlertSubscription) -> None:
        """Add subscription for a connection"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].add(subscription)
            logger.debug(f"Subscription added: {subscription}")

    async def unsubscribe(self, websocket: WebSocket, subscription: AlertSubscription) -> None:
        """Remove subscription for a connection"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(subscription)
            logger.debug(f"Subscription removed: {subscription}")

    async def broadcast_alert(self, alert: Dict) -> None:
        """Broadcast alert to subscribed clients"""
        threat_level = alert.get("threat_level", "").upper()
        
        message = {
            "type": MessageType.ALERT,
            "alert": alert,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in history
        self._add_to_history(message)
        
        # Broadcast to subscribed clients
        for websocket in self.active_connections:
            subscriptions = self.subscriptions.get(websocket, {AlertSubscription.ALL})
            
            should_send = False
            
            if AlertSubscription.ALL in subscriptions:
                should_send = True
            elif AlertSubscription.CRITICAL in subscriptions and threat_level == "CRITICAL":
                should_send = True
            elif AlertSubscription.HIGH_AND_ABOVE in subscriptions and threat_level in ["CRITICAL", "HIGH"]:
                should_send = True
            elif AlertSubscription.THREAT_DETECTION_ONLY in subscriptions:
                should_send = True
            
            if should_send:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send alert: {e}")
                    self.disconnect(websocket)

    async def broadcast_metrics(self, metrics: Dict) -> None:
        """Broadcast metrics update to all clients"""
        message = {
            "type": MessageType.METRICS,
            "metrics": metrics,
            "timestamp": datetime.now().isoformat()
        }
        
        self._add_to_history(message)
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send metrics: {e}")
                self.disconnect(websocket)

    async def broadcast_model_status(self, model_status: Dict) -> None:
        """Broadcast model status update to all clients"""
        message = {
            "type": MessageType.MODEL_STATUS,
            "model_status": model_status,
            "timestamp": datetime.now().isoformat()
        }
        
        self._add_to_history(message)
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send model status: {e}")
                self.disconnect(websocket)

    async def broadcast_drift_detection(self, drift_data: Dict) -> None:
        """Broadcast drift detection alert to all clients"""
        message = {
            "type": MessageType.DRIFT_DETECTION,
            "drift": drift_data,
            "timestamp": datetime.now().isoformat()
        }
        
        self._add_to_history(message)
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send drift notification: {e}")
                self.disconnect(websocket)

    async def send_to_client(self, websocket: WebSocket, message: Dict) -> None:
        """Send message to specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to client: {e}")
            self.disconnect(websocket)

    def _add_to_history(self, message: Dict) -> None:
        """Add message to history for late subscribers"""
        self.message_history.append(message)
        if len(self.message_history) > self.max_history:
            self.message_history.pop(0)

    def get_history(self, message_type: MessageType = None, limit: int = 10) -> List[Dict]:
        """Get message history, optionally filtered by type"""
        if message_type:
            filtered = [
                m for m in self.message_history[-limit:]
                if m.get("type") == message_type
            ]
            return filtered
        return self.message_history[-limit:]

    @property
    def connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)


# ============================================================================
# GLOBAL MANAGER INSTANCE
# ============================================================================

manager = IDSConnectionManager()


# ============================================================================
# WEBSOCKET ENDPOINT HANDLER
# ============================================================================

async def websocket_endpoint(websocket: WebSocket, client_id: str) -> None:
    """
    WebSocket endpoint for real-time IDS alerts
    
    **Connection URL:** `ws://localhost:8000/ws/ids/{client_id}`
    
    **Example JavaScript:**
    ```javascript
    const ws = new WebSocket(`ws://${window.location.host}/ws/ids/client_001`);
    
    ws.onopen = () => {
        ws.send(JSON.stringify({
            type: "subscribe",
            subscription: "high_and_above"
        }));
    };
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "alert") {
            console.log("New threat detected:", data.alert);
            updateDashboard(data.alert);
        } else if (data.type === "metrics") {
            console.log("Metrics update:", data.metrics);
        }
    };
    
    ws.onerror = (error) => console.error("WebSocket error:", error);
    ws.onclose = () => console.log("Connection closed");
    ```
    
    **Message Types:**
    - `alert`: New threat detection
    - `metrics`: System metrics update
    - `model_status`: Model performance update
    - `drift_detection`: Model drift detected
    - `subscribe`: Subscribe to alert type
    - `unsubscribe`: Unsubscribe from alert type
    - `ping`: Server heartbeat
    - `pong`: Client response to ping
    """
    
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive client message
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await manager.send_to_client(websocket, {
                    "type": "error",
                    "message": "Invalid JSON format",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            msg_type = message.get("type")
            
            # Handle subscription messages
            if msg_type == MessageType.SUBSCRIBE:
                subscription_str = message.get("subscription", "").upper()
                try:
                    subscription = AlertSubscription[subscription_str]
                    await manager.subscribe(websocket, subscription)
                    await manager.send_to_client(websocket, {
                        "type": "subscription_confirmed",
                        "subscription": subscription_str,
                        "timestamp": datetime.now().isoformat()
                    })
                    logger.info(f"Client {client_id} subscribed to {subscription_str}")
                except KeyError:
                    await manager.send_to_client(websocket, {
                        "type": "error",
                        "message": f"Invalid subscription type: {subscription_str}",
                        "valid_options": [s.value for s in AlertSubscription],
                        "timestamp": datetime.now().isoformat()
                    })

            elif msg_type == MessageType.UNSUBSCRIBE:
                subscription_str = message.get("subscription", "").upper()
                try:
                    subscription = AlertSubscription[subscription_str]
                    await manager.unsubscribe(websocket, subscription)
                    await manager.send_to_client(websocket, {
                        "type": "subscription_removed",
                        "subscription": subscription_str,
                        "timestamp": datetime.now().isoformat()
                    })
                except KeyError:
                    pass

            elif msg_type == MessageType.PING:
                await manager.send_to_client(websocket, {
                    "type": MessageType.PONG,
                    "timestamp": datetime.now().isoformat()
                })

            elif msg_type == "get_history":
                msg_type_filter = message.get("message_type")
                limit = message.get("limit", 10)
                history = manager.get_history(msg_type_filter, limit)
                await manager.send_to_client(websocket, {
                    "type": "history",
                    "messages": history,
                    "count": len(history),
                    "timestamp": datetime.now().isoformat()
                })

            elif msg_type == "get_stats":
                await manager.send_to_client(websocket, {
                    "type": "stats",
                    "connected_clients": manager.connection_count,
                    "history_size": len(manager.message_history),
                    "timestamp": datetime.now().isoformat()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(websocket)


# ============================================================================
# INTEGRATION WITH IDS ENGINE
# ============================================================================

async def emit_alert(alert: Dict) -> None:
    """
    Emit alert to all connected WebSocket clients
    
    Call this from the IDS engine when a threat is detected:
    
    ```python
    threat_detected, alert, info = ids_engine.detect_threats(flow)
    if threat_detected:
        await emit_alert({
            "alert_id": alert.alert_id,
            "threat_level": alert.threat_level.value,
            "threat_score": alert.threat_score,
            "threat_name": alert.threat_name,
            "flow_info": {...},
            ...
        })
    ```
    """
    await manager.broadcast_alert(alert)


async def emit_metrics(metrics: Dict) -> None:
    """Emit metrics update to all clients"""
    await manager.broadcast_metrics(metrics)


async def emit_model_status(model_status: Dict) -> None:
    """Emit model status update to all clients"""
    await manager.broadcast_model_status(model_status)


async def emit_drift_detection(drift_data: Dict) -> None:
    """Emit drift detection alert to all clients"""
    await manager.broadcast_drift_detection(drift_data)


# ============================================================================
# FASTAPI SETUP
# ============================================================================

def setup_websocket_routes(app) -> None:
    """Register WebSocket endpoint with FastAPI app"""
    from fastapi import WebSocketRoute
    
    @app.websocket("/ws/ids/{client_id}")
    async def websocket_ids_endpoint(websocket: WebSocket, client_id: str):
        await websocket_endpoint(websocket, client_id)


# ============================================================================
# EXAMPLE USAGE IN MAIN.PY
# ============================================================================

"""
from fastapi import FastAPI
from websocket_ids import setup_websocket_routes, emit_alert, manager

app = FastAPI()

# Setup WebSocket routes
setup_websocket_routes(app)

# In your IDS detection handler:
@app.post("/ids/detect")
async def detect_threats(request: FlowAnalysisRequest):
    flow = create_network_flow(...)
    threat_detected, alert, info = ids_engine.detect_threats(flow)
    
    if threat_detected:
        # Emit to WebSocket clients
        await emit_alert({
            "alert_id": alert.alert_id,
            "threat_level": alert.threat_level.value,
            "threat_score": alert.threat_score,
            ...
        })
    
    return {...}
"""
