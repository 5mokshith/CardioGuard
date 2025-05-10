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

// Anomaly tracking variables
let consecutiveAnomalies = 0;
const ANOMALY_THRESHOLD = 5;
let lastAlertTime = 0;
const MIN_ALERT_INTERVAL = 300000; // 5 minutes in milliseconds

export function initializeWebSocket() {
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

async function createAlert(severity, description, latitude, longitude) {
    console.log('Starting alert creation with:', {
        severity,
        description,
        latitude,
        longitude,
        consecutiveAnomalies
    });

    try {
        const { data: { session }, error: sessionError } = await supabase.auth.getSession();
        
        if (sessionError || !session) {
            console.error('Session error:', sessionError);
            return;
        }

        console.log('Current session user:', session.user.id);

        const currentTime = Date.now();
        if (currentTime - lastAlertTime < MIN_ALERT_INTERVAL) {
            console.log(`Alert skipped - Last alert was ${(currentTime - lastAlertTime)/1000} seconds ago`);
            return;
        }

        // Get emergency contact for notification (specifically doctor)
        const { data: contacts, error: contactError } = await supabase
            .from('emergency_contacts')
            .select('*')
            .eq('user_id', session.user.id)
            .eq('relationship', 'Doctor')
            .single();

        if (contactError) {
            console.log('Error fetching emergency contacts:', contactError);
        } else {
            console.log('Found emergency contact:', contacts);
        }

        const alertDescription = contacts 
            ? `${description}. Doctor contact: ${contacts.name} (${contacts.phone})`
            : description;

        console.log('Preparing to insert alert with description:', alertDescription);

        // Create the alert object with simplified structure
        const alertData = {
            user_id: session.user.id,
            alert_type: 'ECG_ANOMALY',
            severity: severity,
            description: alertDescription,
            gps_latitude: latitude,
            gps_longitude: longitude,
            is_resolved: false
        };

        console.log('Inserting alert data:', alertData);

        const { data: insertedAlert, error: insertError } = await supabase
            .from('alerts')
            .insert([alertData])
            .select();

        if (insertError) {
            console.error('Error inserting alert:', insertError);
            throw insertError;
        }

        console.log('Alert inserted successfully:', insertedAlert);
        lastAlertTime = currentTime;
        consecutiveAnomalies = 0;

        // Trigger visual alert
        handleAlert({
            type: 'alert',
            message: `Medical alert created: ${description}`,
            severity: severity,
            timestamp: new Date().toISOString()
        });

    } catch (error) {
        console.error('Error in createAlert:', error);
        console.error('Full error object:', {
            message: error.message,
            details: error.details,
            hint: error.hint,
            code: error.code
        });
    }
}

async function handleAnomalyDetection() {
    consecutiveAnomalies++;
    console.log(`Consecutive anomalies: ${consecutiveAnomalies}`);
    
    if (consecutiveAnomalies >= ANOMALY_THRESHOLD) {
        if ("geolocation" in navigator) {
            try {
                const position = await new Promise((resolve, reject) => {
                    navigator.geolocation.getCurrentPosition(resolve, reject, {
                        enableHighAccuracy: true,
                        timeout: 5000,
                        maximumAge: 0
                    });
                });

                const severity = consecutiveAnomalies >= 10 ? 'high' : 'medium';
                const description = `ECG anomaly detected ${consecutiveAnomalies} times consecutively. Immediate medical attention may be required.`;
                
                await createAlert(
                    severity,
                    description,
                    position.coords.latitude,
                    position.coords.longitude
                );

            } catch (error) {
                console.error('Error getting location:', error);
                // Create alert without location data
                await createAlert(
                    'high',
                    `ECG anomaly detected ${consecutiveAnomalies} times consecutively (location unavailable). Immediate medical attention may be required.`,
                    null,
                    null
                );
            }
        } else {
            // Create alert without location if geolocation is not supported
            await createAlert(
                'high',
                `ECG anomaly detected ${consecutiveAnomalies} times consecutively (location unavailable). Immediate medical attention may be required.`,
                null,
                null
            );
        }
    }
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
    
    // Update time labels
    timeLabels.shift();
    timeLabels.push(new Date().toLocaleTimeString());
    
    // Update heart rate display
    const heartRateDisplay = document.getElementById('heartRate');
    if (heartRateDisplay) {
        const simulatedHeartRate = Math.round(70 + Math.random() * 10);
        heartRateDisplay.textContent = simulatedHeartRate;
    }

    // Update chart
    ecgChart?.setOption({
        xAxis: {
            data: timeLabels
        },
        series: [{
            data: ecgData
        }]
    });

    // Handle anomaly detection
    if (data.is_anomaly) {
        handleAnomalyDetection();
        updateStatus('Anomaly Detected', 'warning');
    } else {
        consecutiveAnomalies = 0; // Reset counter when normal reading
        updateStatus('Normal', 'normal');
    }
}


// Handle window resize
window.addEventListener('resize', () => {
    ecgChart?.resize();
    spo2Chart?.resize();
});