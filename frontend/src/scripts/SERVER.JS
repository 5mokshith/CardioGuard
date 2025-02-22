// src/scripts/main.js

const ECGMonitor = {
    ws: null,
    dataPoints: [],
    maxDataPoints: 200, // Number of points to show on chart
    
    init() {
        this.connectWebSocket();
        this.setupChart();
    },

    connectWebSocket() {
        this.ws = new WebSocket('ws://localhost:8765');
        
        this.ws.onopen = () => {
            console.log('Connected to ECG server');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleNewData(data);
        };

        this.ws.onclose = () => {
            console.log('Disconnected from ECG server');
            // Attempt to reconnect after 5 seconds
            setTimeout(() => this.connectWebSocket(), 5000);
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    },

    setupChart() {
        // Initialize your chart here
        // You can use any charting library of your choice
        // Example using Chart.js:
        const ctx = document.getElementById('ecgChart').getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'ECG Data',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        beginAtZero: true
                    }
                },
                animation: {
                    duration: 0
                }
            }
        });
    },

    handleNewData(data) {
        // Add new data point
        this.dataPoints.push(data.ecg_value);
        
        // Keep only last maxDataPoints
        if (this.dataPoints.length > this.maxDataPoints) {
            this.dataPoints.shift();
        }

        // Update chart
        this.chart.data.labels = Array(this.dataPoints.length).fill('');
        this.chart.data.datasets[0].data = this.dataPoints;
        this.chart.update('none'); // Update without animation

        // Handle anomaly
        if (data.is_anomaly) {
            this.handleAnomaly(data);
        }
    },

    handleAnomaly(data) {
        // Create alert element
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert';
        alertDiv.textContent = `Anomaly detected at ${new Date(data.timestamp).toLocaleString()}`;
        
        // Add to DOM
        document.getElementById('alerts').prepend(alertDiv);
        
        // Remove alert after 5 seconds
        setTimeout(() => alertDiv.remove(), 5000);
    }
};

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    ECGMonitor.init();
});