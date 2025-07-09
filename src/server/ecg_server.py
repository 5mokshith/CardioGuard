import asyncio
import websockets
import json
import numpy as np
from datetime import datetime
import logging
from pathlib import Path
import joblib
from typing import Optional, Dict, Any, Set
from dataclasses import dataclass
import dataclasses
from websockets.legacy.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ECGDataPoint:
    """Data class for ECG readings."""
    timestamp: str
    value: float
    is_anomaly: bool = False

class ECGServer:
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.model = self._load_model()
        self.clients: Set[WebSocketServerProtocol] = set()
        self.esp_client: Optional[WebSocketServerProtocol] = None
        self.data_buffer: list[float] = []
        self.BUFFER_SIZE = 95  # Expect 95 consecutive ADC readings per sample
        self.last_esp_heartbeat: Optional[float] = None
        self.ESP_TIMEOUT = 10.0
        self.MIN_VALID_SIGNALS = 10
        self.consecutive_anomalies = 0
        self.ANOMALY_THRESHOLD = 3  # Number of consecutive anomalies before alerting

    def _load_model(self):
        try:
            logger.info(f"Loading model from: {self.model_path}")
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            return joblib.load(self.model_path)
        except Exception as e:
            logger.error(f"Critical error loading model: {e}")
            raise SystemExit(1)

    def validate_ecg_data(self, value: Any) -> Optional[float]:
        try:
            value = float(value)
            # Ensure the raw value is in the ADC range (0-1023)
            if not 0 <= value <= 1023:
                logger.warning(f"ECG value out of range: {value}")
                return None
            return value
        except (ValueError, TypeError) as e:
            logger.warning(f"Invalid ECG value: {e}")
            return None

    async def detect_anomaly(self) -> bool:
        try:
            # Ensure we have exactly BUFFER_SIZE values; pad with zeros if necessary
            if len(self.data_buffer) < self.BUFFER_SIZE:
                padded_buffer = self.data_buffer + [0] * (self.BUFFER_SIZE - len(self.data_buffer))
            else:
                padded_buffer = self.data_buffer[-self.BUFFER_SIZE:]
            
            # Convert the list to a numpy array of shape (1, BUFFER_SIZE)
            X = np.array(padded_buffer).reshape(1, -1)
            # Normalize the data (assuming your model was trained on normalized values)
            X = X / 1023.0
            
            # Check for a sufficient number of non-zero values
            non_zero_count = np.count_nonzero(X)
            if non_zero_count < self.MIN_VALID_SIGNALS:
                logger.warning(f"Insufficient valid signals: {non_zero_count}/{self.BUFFER_SIZE}")
                return False
            
            # Run prediction asynchronously
            prediction = await asyncio.get_event_loop().run_in_executor(None, self.model.predict, X)
            proba = await asyncio.get_event_loop().run_in_executor(None, self.model.predict_proba, X)
            
            logger.info(f"Anomaly detection input: {X} -> Prediction: {prediction} with probability: {proba[0][1]:.3f}")
            return bool(prediction[0])
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return False

    async def send_anomaly_alert(self):
        """Send an anomaly alert to all frontend clients."""
        alert_message = {
            'type': 'alert',
            'message': 'ECG Anomaly Detected!',
            'severity': 'high',
            'timestamp': datetime.now().isoformat()
        }
        await self.broadcast_to_frontend(alert_message)
        logger.warning("Anomaly alert sent to frontend clients")

    async def process_esp_data(self, message: str):
        try:
            logger.debug(f"Raw message received: {message}")
            data = json.loads(message)
            message_type = data.get('type')

            if message_type == 'ping':
                self.last_esp_heartbeat = datetime.now().timestamp()
                return

            if message_type == 'error':
                await self.broadcast_to_frontend({
                    'type': 'warning',
                    'message': data.get('message', 'ECG leads disconnected')
                })
                return

            if message_type == 'data':
                raw_value = data.get('value')
                logger.debug(f"Raw value before validation: {raw_value}")
                ecg_value = self.validate_ecg_data(raw_value)
                if ecg_value is None:
                    return

                logger.info(f"Processed ECG data: {ecg_value}")
                self.data_buffer.append(ecg_value)
                while len(self.data_buffer) > self.BUFFER_SIZE:
                    self.data_buffer.pop(0)

                is_anomaly = False
                if len(self.data_buffer) == self.BUFFER_SIZE:
                    is_anomaly = await self.detect_anomaly()
                    
                    # Handle consecutive anomalies
                    if is_anomaly:
                        self.consecutive_anomalies += 1
                        if self.consecutive_anomalies >= self.ANOMALY_THRESHOLD:
                            await self.send_anomaly_alert()
                    else:
                        self.consecutive_anomalies = 0

                data_point = ECGDataPoint(
                    timestamp=datetime.now().isoformat(),
                    value=ecg_value,
                    is_anomaly=is_anomaly
                )
                await self.broadcast_to_frontend(dataclasses.asdict(data_point))
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
        except Exception as e:
            logger.error(f"Error processing ESP data: {e}")

    async def handle_esp_connection(self, websocket: WebSocketServerProtocol):
        if self.esp_client:
            logger.warning("Rejecting duplicate ESP connection")
            await websocket.close(1008, "Another ESP device already connected")
            return

        logger.info("ESP8266 connected")
        self.esp_client = websocket
        self.last_esp_heartbeat = datetime.now().timestamp()
        
        try:
            await self.broadcast_to_frontend({
                'type': 'status',
                'message': 'ESP8266 connected'
            })
            async for message in websocket:
                await self.process_esp_data(message)
        except ConnectionClosed:
            logger.info("ESP8266 disconnected normally")
        except Exception as e:
            logger.error(f"ESP connection error: {e}")
        finally:
            self.esp_client = None
            self.last_esp_heartbeat = None
            await self.broadcast_to_frontend({
                'type': 'status',
                'message': 'ESP8266 disconnected'
            })

    async def handle_frontend_connection(self, websocket: WebSocketServerProtocol):
        logger.info("Frontend client connected")
        self.clients.add(websocket)
        await websocket.send(json.dumps({
            'type': 'status',
            'message': 'Connected to server',
            'esp_connected': bool(self.esp_client)
        }))
        try:
            await websocket.wait_closed()
        except Exception as e:
            logger.error(f"Frontend client error: {e}")
        finally:
            self.clients.remove(websocket)
            logger.info("Frontend client disconnected")

    async def broadcast_to_frontend(self, data: Dict[str, Any]):
        if not self.clients:
            return
        message = json.dumps(data)
        dead_clients = set()
        for client in self.clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                dead_clients.add(client)
        self.clients -= dead_clients

    async def monitor_esp_connection(self):
        while True:
            await asyncio.sleep(1)
            if (self.esp_client and self.last_esp_heartbeat and 
                (datetime.now().timestamp() - self.last_esp_heartbeat > self.ESP_TIMEOUT)):
                logger.warning("ESP8266 heartbeat timeout")
                await self.broadcast_to_frontend({
                    'type': 'status',
                    'message': 'ESP8266 connection timeout'
                })
                self.esp_client = None
                self.last_esp_heartbeat = None

    async def start_server(self, host: str = '0.0.0.0', port: int = 8765):
        async def handler(websocket):
            protocol = websocket.subprotocol
            logger.info(f"New connection with protocol: {protocol}")
            try:
                if protocol == 'esp':
                    await self.handle_esp_connection(websocket)
                elif protocol == 'frontend':
                    await self.handle_frontend_connection(websocket)
                else:
                    # Default to frontend connection if no protocol specified
                    logger.info("No protocol specified, handling as frontend connection")
                    await self.handle_frontend_connection(websocket)
            except Exception as e:
                logger.error(f"Error handling connection: {e}")
                await websocket.close(1011, "Internal server error")

        # Update server to accept both 'esp' and 'frontend' protocols
        server = await websockets.serve(
            handler, 
            host, 
            port, 
            subprotocols=['esp', 'frontend']  # Now accepting both protocols
        )
        logger.info(f"Server running on ws://{host}:{port}")
        monitor_task = asyncio.create_task(self.monitor_esp_connection())
        try:
            await asyncio.Future()  # run forever
        except asyncio.CancelledError:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
        finally:
            server.close()
            await server.wait_closed()

def main():
    model_path = Path(r"C:\Users\moksh\classroom\test_ML_deepalert\test\models\gradientboosting_combined_model.joblib")
    server = ECGServer(model_path)
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise

if __name__ == "__main__":
    main()