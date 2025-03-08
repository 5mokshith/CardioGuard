# CardioGuard

**CardioGuard** is an AI-powered cardiac arrest prediction and alert system designed to provide real-time monitoring and timely notifications to help prevent cardiac emergencies.

## Table of Contents

- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

## Features

- **Real-Time Monitoring:** Continuously tracks ECG and SpO₂ levels using AD8232 sensors integrated with an ESP32 microcontroller.
- **Machine Learning Integration:** Utilizes a Random Forest model with K-Fold validation for accurate anomaly detection.
- **Automated Alerts:** Leverages Supabase Edge Functions and Firebase Cloud Messaging to send instant notifications to healthcare providers and emergency contacts.
- **Progressive Web App (PWA):** Provides a user-friendly interface accessible on various devices.
- **Scalability:** Designed with future enhancements in mind, including deep learning integration, multi-sensor fusion, and edge AI processing.

## System Architecture

CardioGuard is built on a multi-layered architecture:

1. **Wearable Sensor Module:**  
   - Captures ECG and SpO₂ data via AD8232 sensors and ESP32.
   - Transmits data in real time to the cloud via Wi-Fi/Bluetooth.

2. **Cloud Server:**  
   - Processes incoming sensor data using a Node.js/Python backend.
   - Performs machine learning inference using a pre-trained Random Forest classifier.

3. **Notification Service:**  
   - Uses Supabase Edge Functions and Firebase Cloud Messaging (FCM) to trigger alerts when anomalies are detected.

4. **User Interface:**  
   - React-based Progressive Web App (PWA) for real-time data visualization and alert management.

## Installation

### Prerequisites

- Node.js v16+ and npm
- Python 3.8+ (for ML model training)
- Arduino IDE (for ESP32 firmware)
- Firebase and Supabase accounts

### Frontend Setup

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/CardioGuard.git
   cd CardioGuard/frontend




   Install Dependencies:

bash
Copy
npm install
Configure Environment Variables:
Create a .env file with your Firebase and Supabase credentials:

env
Copy
VITE_FIREBASE_API_KEY=your_key
VITE_SUPABASE_URL=your_url
VITE_SUPABASE_KEY=your_key
Start the Development Server:

bash
Copy
npm run dev
Access the app at http://localhost:3000.

Hardware Setup (ESP32)
Upload Firmware:

Open CardioGuard/firmware/sensor_module.ino in Arduino IDE.

Install required libraries (AD8232, ESP32 BLE).

Set Wi-Fi credentials in the code.

Upload to ESP32.

Backend & ML Setup
Navigate to the Backend Directory:

bash
Copy
cd ../backend
Install Python Dependencies:

bash
Copy
pip install -r requirements.txt
Train the ML Model:

bash
Copy
python train_model.py
Start the Server:

bash
Copy
node server.js
Usage
Pair the Sensor Module:

Power on the ESP32 device.

Open the CardioGuard PWA and navigate to Devices > Pair New Device.

Monitor Real-Time Data:

View live ECG and SpO₂ graphs on the dashboard.

Configure Alerts:

Go to Settings > Notifications to add emergency contacts and providers.

Historical Analysis:

Access Reports to review past data and anomaly logs.

Contributing
Fork the Repository.

Create a Feature Branch:

bash
Copy
git checkout -b feature/amazing-feature
Commit Your Changes:

bash
Copy
git commit -m "Add amazing feature"
Push to the Branch:

bash
Copy
git push origin feature/amazing-feature
Open a Pull Request.

License
Distributed under the MIT License. See LICENSE for details.

Acknowledgements
The AD8232 library maintainers.

Firebase and Supabase for backend services.

Scikit-learn for ML tooling.
