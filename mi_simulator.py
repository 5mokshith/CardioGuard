import numpy as np
import time
import random
import math
import requests
import websocket
import json
import threading

class MISimulator:
    def __init__(self, sampling_rate=250):
        """
        Simulate ECG data with myocardial infarction patterns
        
        Parameters:
        sampling_rate (int): Samples per second (Hz)
        """
        self.sampling_rate = sampling_rate
        self.time = 0
        self.baseline = 0
        
        # Normal ECG parameters
        self.normal_params = {
            'heart_rate': 70,
            'p_amplitude': 0.25,
            'qrs_amplitude': 1.5,
            't_amplitude': 0.3,
            'st_level': 0,
            'noise_level': 0.05
        }
        
        # MI pattern parameters
        self.mi_patterns = {
            'anterior': {
                'st_elevation': 0.3,  # ST elevation in leads V2-V4
                't_wave_inversion': -0.2,
                'q_wave_depth': -0.4
            },
            'inferior': {
                'st_elevation': 0.25,  # ST elevation in leads II, III, aVF
                't_wave_inversion': -0.15,
                'q_wave_depth': -0.3
            },
            'lateral': {
                'st_elevation': 0.2,  # ST elevation in leads I, aVL, V5-V6
                't_wave_inversion': -0.2,
                'q_wave_depth': -0.25
            }
        }
        
        self.current_pattern = None
        self.is_mi_active = False
        
    def generate_wave(self, t, amplitude, duration, phase, wave_type='gaussian'):
        """Generate different types of ECG waves"""
        if wave_type == 'gaussian':
            return amplitude * np.exp(-(t - phase)**2 / (2 * duration**2))
        elif wave_type == 'triangular':
            # For Q and S waves
            return amplitude * max(0, 1 - abs(t - phase) / duration)
        return 0
        
    def generate_ecg_sample(self):
        """Generate a single ECG sample"""
        # Calculate time within the current cardiac cycle
        beat_duration = 60.0 / self.normal_params['heart_rate']
        t = self.time % beat_duration
        
        # Initialize the sample
        sample = 0
        
        # P wave
        p_duration = 0.08
        p_phase = 0.1 * beat_duration
        sample += self.generate_wave(t, self.normal_params['p_amplitude'], p_duration, p_phase)
        
        # QRS complex
        qrs_duration = 0.03
        r_phase = 0.3 * beat_duration
        
        # Q wave
        q_depth = self.mi_patterns[self.current_pattern]['q_wave_depth'] if self.is_mi_active else -0.1
        sample += self.generate_wave(t, q_depth, qrs_duration/2, r_phase-qrs_duration, 'triangular')
        
        # R wave
        sample += self.generate_wave(t, self.normal_params['qrs_amplitude'], qrs_duration, r_phase)
        
        # S wave
        sample += self.generate_wave(t, -0.2, qrs_duration/2, r_phase+qrs_duration, 'triangular')
        
        # ST segment
        st_start = r_phase + 0.1
        st_duration = 0.1
        if self.is_mi_active:
            st_elevation = self.mi_patterns[self.current_pattern]['st_elevation']
            sample += st_elevation * (1 if st_start <= t <= st_start + st_duration else 0)
        
        # T wave
        t_duration = 0.1
        t_phase = st_start + st_duration + t_duration
        t_amplitude = (self.mi_patterns[self.current_pattern]['t_wave_inversion'] 
                      if self.is_mi_active else self.normal_params['t_amplitude'])
        sample += self.generate_wave(t, t_amplitude, t_duration, t_phase)
        
        # Add noise
        noise = np.random.normal(0, self.normal_params['noise_level'])
        sample += noise
        
        # Update time
        self.time += 1.0 / self.sampling_rate
        
        return sample
        
    def start_mi_episode(self, mi_type=None):
        """Start a myocardial infarction episode"""
        if mi_type is None:
            mi_type = random.choice(list(self.mi_patterns.keys()))
        self.current_pattern = mi_type
        self.is_mi_active = True
        return f"Starting {mi_type} MI pattern"
        
    def stop_mi_episode(self):
        """Stop the MI episode and return to normal rhythm"""
        self.is_mi_active = False
        return "Returning to normal rhythm"

def test_mi_detection():
    """Test the ECG server with MI simulation"""
    # Server configuration
    SERVER_URL = "http://localhost:5000"
    WS_URL = "ws://localhost:5000/socket.io/?EIO=4&transport=websocket"
    
    def on_message(ws, message):
        """Handle websocket messages"""
        try:
            if "ecg_data" in message:
                data = json.loads(message.split("42")[1])
                print(f"Received ECG data: {len(data[1]['ecg_data'])} samples")
            elif "anomaly_detected" in message:
                data = json.loads(message.split("42")[1])
                print(f"⚠️ MI Pattern Detected! Confidence: {data[1]['confidence']:.2f}")
        except Exception as e:
            pass

    # Set up WebSocket
    ws = websocket.WebSocketApp(
        WS_URL,
        on_message=on_message,
        on_error=lambda ws, error: print(f"Error: {error}"),
        on_close=lambda ws, status, msg: print("WebSocket closed"),
        on_open=lambda ws: print("WebSocket connected")
    )
    
    # Start WebSocket in background thread
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.daemon = True
    ws_thread.start()
    
    # Start the server
    response = requests.post(f"{SERVER_URL}/start")
    print(f"Server start response: {response.json()}")
    
    # Create simulator
    simulator = MISimulator()
    
    try:
        print("\nStarting MI simulation...")
        print("Normal rhythm baseline for 10 seconds...")
        
        samples_count = 0
        mi_duration = 2500  # 10 seconds of MI pattern
        normal_duration = 2500  # 10 seconds of normal rhythm
        current_duration = 0
        mi_active = False
        
        while True:
            # Generate and send sample
            sample = simulator.generate_ecg_sample()
            print(f"Sample: {sample:.2f} | {'MI Active' if mi_active else 'Normal'}", end='\r')
            
            current_duration += 1
            
            # Toggle between normal and MI patterns
            if not mi_active and current_duration >= normal_duration:
                mi_type = random.choice(['anterior', 'inferior', 'lateral'])
                print(f"\nSimulating {mi_type} MI pattern...")
                simulator.start_mi_episode(mi_type)
                mi_active = True
                current_duration = 0
            elif mi_active and current_duration >= mi_duration:
                print("\nReturning to normal rhythm...")
                simulator.stop_mi_episode()
                mi_active = False
                current_duration = 0
            
            time.sleep(1/simulator.sampling_rate)
            
    except KeyboardInterrupt:
        print("\nStopping simulation...")
        requests.post(f"{SERVER_URL}/stop")
        ws.close()

if __name__ == "__main__":
    test_mi_detection()