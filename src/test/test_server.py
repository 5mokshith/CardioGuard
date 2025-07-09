import unittest
import requests
import socketio
import time
import json
from threading import Event

class TestECGServer(unittest.TestCase):
    def setUp(self):
        """Set up test case"""
        self.base_url = 'http://localhost:5000'
        self.sio = socketio.Client()
        self.received_data = []
        self.received_alerts = []
        self.connection_status = []
        self.data_received = Event()
        self.alert_received = Event()
        
        # Set up Socket.IO event handlers
        @self.sio.on('ecg_data')
        def on_ecg_data(data):
            self.received_data.append(data)
            self.data_received.set()
            
        @self.sio.on('anomaly_detected')
        def on_anomaly(data):
            self.received_alerts.append(data)
            self.alert_received.set()
            
        @self.sio.on('connection_status')
        def on_connection_status(data):
            self.connection_status.append(data)
            
        # Connect to Socket.IO server
        try:
            self.sio.connect(self.base_url)
        except Exception as e:
            print(f"Failed to connect to Socket.IO server: {e}")
            
    def tearDown(self):
        """Clean up after test"""
        try:
            # Stop monitoring
            requests.post(f"{self.base_url}/stop")
            # Disconnect Socket.IO client
            self.sio.disconnect()
        except Exception as e:
            print(f"Error during teardown: {e}")

    def test_server_status(self):
        """Test server status endpoint"""
        response = requests.get(f"{self.base_url}/status")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('is_collecting', data)
        self.assertIn('buffer_size', data)
        self.assertIn('arduino_connected', data)
        self.assertIn('sampling_rate', data)
        self.assertIn('leads_connected', data)

    def test_start_monitoring(self):
        """Test starting the monitoring"""
        try:
            response = requests.post(f"{self.base_url}/start")
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertTrue('message' in data)
            self.assertEqual(data['message'], 'Monitoring started')
        except Exception as e:
            print(f"Error in start_monitoring: {str(e)}")
            raise

    def test_real_time_data(self):
        """Test real-time data streaming"""
        try:
            # Start monitoring
            requests.post(f"{self.base_url}/start")
            
            # Wait for data
            timeout = time.time() + 5  # 5 second timeout
            while time.time() < timeout and not self.data_received.is_set():
                time.sleep(0.1)
            
            self.assertTrue(len(self.received_data) > 0)
            
            # Validate data format
            data = self.received_data[0]
            self.assertIn('timestamp', data)
            self.assertIn('ecg_value', data)
            
        except Exception as e:
            print(f"Error in real_time_data: {str(e)}")
            raise

    def test_stop_monitoring(self):
        """Test stopping the monitoring"""
        response = requests.post(f"{self.base_url}/stop")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        
        # Verify monitoring has stopped
        status = requests.get(f"{self.base_url}/status").json()
        self.assertFalse(status['is_collecting'])

if __name__ == '__main__':
    unittest.main()