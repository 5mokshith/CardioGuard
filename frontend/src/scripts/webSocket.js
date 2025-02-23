// Create a new file: src/scripts/websocket.js

import { supabase } from './auth.js';

let ws = null;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;
let ecgChart = null;
let spo2Chart = null;
const MAX_DATA_POINTS = 100;

let ecgData = Array(MAX_DATA_POINTS).fill(0);
let spo2Data = Array(MAX_DATA_POINTS).fill(95);
let timeLabels = Array(MAX_DATA_POINTS).fill('');

export function initializeWebSocket() {
    // Changed protocol to 'frontend' instead of 'esp'
    ws = new WebSocket('ws://localhost:8765', ['frontend']);
    
    ws.onopen = () => {
        console.log('Connected to WebSocket server');
        reconnectAttempts = 0;
        updateStatus('Connected', 'normal');
    };
    
    ws.onclose = () => {
        console.log('Disconnected from WebSocket server');
        updateStatus('Disconnected', 'warning');
        
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
            reconnectAttempts++;
            setTimeout(initializeWebSocket, 5000);
        }
    };
    
    ws.onmessage = handleWebSocketMessage;
}

function updateStatus(message, statusType) {
    const heartRateStatus = document.querySelector('.metric-card:nth-child(1) .status');
    const spo2Status = document.querySelector('.metric-card:nth-child(2) .status');
    
    if (heartRateStatus && spo2Status) {
        heartRateStatus.className = `status ${statusType}`;
        spo2Status.className = `status ${statusType}`;
        heartRateStatus.textContent = message;
        spo2Status.textContent = message;
    }
}

export function initializeCharts() {
    // Initialize ECG Chart
    ecgChart = echarts.init(document.getElementById('ecgChart'));
    const ecgOption = {
        title: {
            text: 'ECG Waveform',
            textStyle: {
                color: '#333',
                fontSize: 16
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeLabels,
            axisLabel: {
                color: '#666'
            }
        },
        yAxis: {
            type: 'value',
            scale: true,
            axisLabel: {
                color: '#666'
            }
        },
        series: [{
            name: 'ECG',
            type: 'line',
            data: ecgData,
            smooth: true,
            lineStyle: {
                color: '#FF4560',
                width: 2
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(255, 69, 96, 0.2)'
                }, {
                    offset: 1,
                    color: 'rgba(255, 69, 96, 0.01)'
                }])
            }
        }]
    };
    ecgChart.setOption(ecgOption);

    // Initialize SpO2 Chart
    spo2Chart = echarts.init(document.getElementById('spo2Chart'));
    const spo2Option = {
        title: {
            text: 'SpO2 Levels',
            textStyle: {
                color: '#333',
                fontSize: 16
            }
        },
        tooltip: {
            trigger: 'axis'
        },
        grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
        },
        xAxis: {
            type: 'category',
            data: timeLabels,
            axisLabel: {
                color: '#666'
            }
        },
        yAxis: {
            type: 'value',
            min: 90,
            max: 100,
            axisLabel: {
                color: '#666'
            }
        },
        series: [{
            name: 'SpO2',
            type: 'line',
            data: spo2Data,
            smooth: true,
            lineStyle: {
                color: '#00E396',
                width: 2
            },
            areaStyle: {
                color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{
                    offset: 0,
                    color: 'rgba(0, 227, 150, 0.2)'
                }, {
                    offset: 1,
                    color: 'rgba(0, 227, 150, 0.01)'
                }])
            }
        }]
    };
    spo2Chart.setOption(spo2Option);
}

function handleWebSocketMessage(event) {
    try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'alert') {
            handleAlert(data);
        } else if (data.type === 'error') {
            updateStatus(data.message, 'warning');
        } else if (data.value !== undefined) {
            updateECGData(data);
        }
    } catch (error) {
        console.error('Error processing message:', error);
    }
}

function updateECGData(data) {
    // Update ECG data
    ecgData.shift();
    ecgData.push(data.value);
    
    // Update heart rate display
    const heartRateDisplay = document.getElementById('heartRate');
    if (heartRateDisplay) {
        // Simulate heart rate calculation (this should be replaced with actual calculation)
        const simulatedHeartRate = Math.round(70 + Math.random() * 10);
        heartRateDisplay.textContent = simulatedHeartRate;
    }

    // Update chart
    ecgChart?.setOption({
        series: [{
            data: ecgData
        }]
    });

    console.log('ECG Data:', data);

    // Handle anomaly detection
    if (data.is_anomaly) {
        handleAlert({
            type: 'alert',
            message: 'Anomaly detected in ECG reading',
            severity: 'high',
            timestamp: data.timestamp
        });
        updateStatus('Anomaly Detected', 'warning');
    } else {
        updateStatus('Normal', 'normal');
    }
}

function handleAlert(alert) {
    // Create a temporary alert div
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert-popup ${alert.severity}`;
    alertDiv.textContent = alert.message;
    
    // Add to body
    document.body.appendChild(alertDiv);
    
    // Remove after 5 seconds
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);

    // If it's a high severity alert, also trigger the emergency section highlight
    if (alert.severity === 'high') {
        const emergencySection = document.querySelector('.emergency-btn.emergency-services');
        if (emergencySection) {
            emergencySection.classList.add('highlight');
            setTimeout(() => {
                emergencySection.classList.remove('highlight');
            }, 2000);
        }
    }
}

// Handle window resize
window.addEventListener('resize', () => {
    ecgChart?.resize();
    spo2Chart?.resize();
});