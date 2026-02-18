# Code Crusaders: Smart Traffic & Parking Management System (SMC)

## Project Overview
Developed for the **Solapur Municipal Corporation (SMC)**, this project is an integrated mobility management platform designed to reduce congestion and improve road safety. By leveraging real-time computer vision and predictive analytics, the system identifies traffic violations, detects illegal parking in restricted zones, and forecasts congestion trends.

### Key Features
- **Comprehensive Traffic Violation Detection**: Automated identification of multiple infractions, including red-light jumps, wrong-lane entry, overspeeding, and riding without a helmet.
- **Illegal Parking Monitoring**: Real-time detection of stationary vehicles within defined "No Parking Zones" using polygon-zone mapping and DeepSORT tracking to trigger alerts after set durations.
- **Parking Congestion Analytics**: Dynamic monitoring of road occupancy to detect high-density areas and provide real-time congestion status.
- **Smart Parking Module Management**: A unified system for geo-mapping authorized vs. unauthorized zones, providing municipal officials with digital visibility into city-wide parking health.
- **Predictive Congestion Forecasting**: Utilizing historical data to predict peak-hour surges near critical junctions, markets, and stations for better urban planning.

---

## System Architecture
The platform follows a modular architecture:
1. **Ingestion:** Live CCTV streams or video file input.
2. **AI Processing Core (cv-module):** Object detection (YOLOv8) and multi-object tracking (DeepSORT).
3. **Rule Engine:** Evaluates object coordinates against predefined ROI polygons for violations.
4. **Data Layer:** Persistent storage in MongoDB for traffic history and logs.
5. **Frontend:** React-based dashboard for real-time visualization.

---

## Getting Started

### Prerequisites
- **Python 3.8+**
- **Node.js & npm**
- **MongoDB** (Local or Atlas instance)

### Installation

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/PoorvaJawale/code-crusaders-samved.git](https://github.com/PoorvaJawale/code-crusaders-samved.git)
   cd code-crusaders-samved

2. Setup AI Backend (cv-module):
   ```bash
   cd cv-module
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt

3. Setup Web Frontend:
   ```bash
   # From the project root
   npm install

Running the Project
1. Start the AI Dashboard:
   ```bash
   cd cv-module
   streamlit run dashboard_streamlit.py

2. Start the React Frontend:
   ```bash
   # From the project root
   npm run dev

3. Run the Parking & Congestion AI (Backend)
   ```bash
   cd cv-module/callibaration-lanes
   python callibirate_lanes.py --video ..\..\videos\traffic_jam.mp4 --out lane_polygons.json
   cd ..
   python runner_tc.py --video ../videos/traffic_jam.mp4 --lanes_json callibaration-lanes/lane_polygons.json --model models/yolov8m.pt

4. Run the Parking Module Management
   ```bash
   cd cv-module
   streamlit run dashboard_streamlit.py

## Tech Stack
- AI/ML: Python, Ultralytics (YOLOv8), DeepSORT, Scikit-learn, OpenCV.
- Frontend: React, Vite, Tailwind CSS, Streamlit.
- Backend/Database: FastAPI/Flask, MongoDB.
- DevOps: Git, GitHub.

## Team: Code Crusaders
- Poorva Jawale
- Kartik Halkunde
- Aditya Narkar
- Yulissaa Pathare
- Rajvi Joshi

## License
This project is developed for the SAMVED-HACK-26 hackathon. All rights reserved.
