# test/src/server/ecg_server.py

import asyncio
import websockets
import serial
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ECGServer:
    def __init__(self, port='COM4', baudrate=115200):
        self.serial_port = port
        self.baudrate = baudrate
        self.clients = set()
        self.running = True
        self.ser = None  # Initialize serial connection as None

    async def connect_serial(self):
        """Connect to Arduino/ESP8266 via USB"""
        try:
            # Close existing connection if any
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.serial_port, self.baudrate)
            logger.info(f"Connected to {self.serial_port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.serial_port}: {e}")
            return False

    async def handle_client(self, websocket):
        """Handle WebSocket client connection"""
        self.clients.add(websocket)
        try:
            await websocket.wait_closed()
        finally:
            self.clients.remove(websocket)
            logger.info("Client disconnected")

    async def read_and_broadcast(self):
        """Read from USB and broadcast to all clients"""
        while self.running:
            if not hasattr(self, 'ser'):
                success = await self.connect_serial()
                if not success:
                    await asyncio.sleep(5)
                    continue

            try:
                if self.ser.in_waiting:
                    line = self.ser.readline().decode('utf-8').strip()
                    
                    # Create data packet
                    data = {
                        'timestamp': datetime.now().isoformat(),
                        'value': float(line)
                    }
                    
                    # Broadcast to all clients
                    if self.clients:
                        message = json.dumps(data)
                        await asyncio.gather(
                            *[client.send(message) for client in self.clients]
                        )
                        
            except Exception as e:
                logger.error(f"Error reading/broadcasting data: {e}")
                await asyncio.sleep(1)

            await asyncio.sleep(0.001)  # Prevent CPU overload

    async def start_server(self, host='localhost', port=8765):
        """Start the WebSocket server"""
        logger.info(f"Starting server on ws://{host}:{port}")
        
        async with websockets.serve(self.handle_client, host, port):
            # Start reading from USB
            read_task = asyncio.create_task(self.read_and_broadcast())
            
            try:
                await asyncio.Future()  # run forever
            except asyncio.CancelledError:
                self.running = False
                if hasattr(self, 'ser'):
                    self.ser.close()
                await read_task

def main():
    # Update these based on your USB port
    PORT = 'COM4'  # Windows example
    # PORT = '/dev/ttyUSB0'  # Linux example
    # PORT = '/dev/tty.SLAB_USBtoUART'  # Mac example
    
    BAUDRATE = 115200
    
    server = ECGServer(port=PORT, baudrate=BAUDRATE)
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()