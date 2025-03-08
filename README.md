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
   - Transmits data in real time to the cloud.

2. **Cloud Server:**  
   - Processes incoming sensor data.
   - Performs machine learning inference using a Random Forest classifier.

3. **Notification Service:**  
   - Uses Supabase Edge Functions and Firebase Cloud Messaging to trigger automated alerts when anomalies are detected.

4. **User Interface:**  
   - Developed as a Progressive Web App (PWA) for real-time data visualization and interaction.

## Installation

Follow these steps to set up the project locally:

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/5mokshith/frontend-expo.git
   cd frontend-expo
Navigate to the Frontend Directory:
cd frontend
Install Dependencies:

Make sure you have Node.js installed, then run:
   ```bash
   npm install
Start the Development Server:
   ```bash
   npm run dev
The application will be available at http://localhost:3000.

Usage
Access the Application:
Open the Progressive Web App in your web browser.

Monitor Health Data:
View real-time ECG and SpO₂ readings on the dashboard.

Receive Alerts:
Configure your alert settings to receive notifications via your preferred channels (email, SMS, push notifications).

Review Historical Data:
Access system logs and historical data for detailed analysis.

Contributing
Contributions to enhance CardioGuard are welcome! To contribute:

Fork the Repository:
Click the "Fork" button on the GitHub repository page.

Create a Feature Branch:
   ```bash
   git checkout -b feature/YourFeatureName
Commit Your Changes:
   ```bash
   git commit -m "Add Your Feature Description"
Push to Your Fork:
   ```bash
   git push origin feature/YourFeatureName
Submit a Pull Request:
Navigate to the original repository and click "New Pull Request."

License
This project is licensed under the MIT License. See the LICENSE file for details.

Acknowledgements
Special thanks to the open-source community for providing the tools and libraries that made CardioGuard possible.
Gratitude to our beta testers for their invaluable feedback and support.

This markdown README file outlines your project's purpose, features, and instructions clearly, making it accessible for both users and contributors.
