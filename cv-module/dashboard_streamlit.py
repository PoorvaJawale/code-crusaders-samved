import streamlit as st
import cv2, time, tempfile, os, sys
import numpy as np
import pandas as pd

# Local imports
try:
    from detector import TrafficDetector
    DETECTOR_AVAILABLE = True
except ImportError:
    DETECTOR_AVAILABLE = False
    st.warning("⚠️ Detector module not available. Install ultralytics: `pip install ultralytics`")

from db import insert_violation, insert_report, get_density_history, get_latest_parking
from predictive_layer import predict_traffic_trend
import plotly.express as px
import pydeck as pdk

# Path fix for cv-module
sys.path.append(os.path.abspath("cv-module"))
try:
    from audit import generate_report
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

# ---------------------------
# Traffic classes whitelist
# ---------------------------
TRAFFIC_CLASSES = {
    "car", "motorbike", "bus", "truck", "bicycle",
    "person", "traffic light", "stop sign", "train"
}

def classify_content(detected_classes):
    """Classify frame content"""
    if not detected_classes:
        return "unclear"
    if any(cls in TRAFFIC_CLASSES for cls in detected_classes):
        return "traffic"
    return "invalid"

# ---------------------------
# Initialize Session State
# ---------------------------
if "running" not in st.session_state:
    st.session_state.running = False
if "violations_log" not in st.session_state:
    st.session_state.violations_log = []

# ---------------------------
# Streamlit UI
# ---------------------------
st.set_page_config(page_title="SMC Smart Traffic & Parking", layout="wide")
st.title("🏛 Solapur Municipal Corporation (SMC) Command Center")

tab1, tab2, tab3 = st.tabs(["🔴 Live Monitoring", "📊 City Overview", "🅿️ Parking Module"])

with tab2:
    st.header("📈 City-Wide Congestion Analytics")
    col1, col2, col3 = st.columns(3)
    
    # Mock Data/Live Data from DB
    density_data = get_density_history(limit=50)
    prediction = predict_traffic_trend()

    if density_data:
        df_density = pd.DataFrame(density_data)
        latest_count = df_density.iloc[0]['vehicle_count']
        prev_count = df_density.iloc[1]['vehicle_count'] if len(df_density) > 1 else latest_count
        
        col1.metric("Current Traffic Density", f"{latest_count} veh/min", f"{latest_count-prev_count}")
        col2.metric("Predicted (Next 15m)", f"{prediction} veh/min")
        col3.metric("Avg. Travel Delay", "2.5 min", "+0.4")
        
        # Line Chart
        st.subheader("Traffic Flow Trend")
        fig = px.line(df_density, x="timestamp", y="vehicle_count", title="Vehicles per Minute")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No historical density data found. Start the live feed to gather data.")

    # Map of Solapur
    st.subheader("📍 Real-time Congestion Heatmap")
    # Simulation: Points around Solapur Bus Stand, Railway Station, etc.
    solapur_coords = [
        {"name": "Solapur Bus Stand", "lat": 17.6715, "lon": 75.9064, "level": 80},
        {"name": "Solapur Railway Station", "lat": 17.6599, "lon": 75.9064, "level": 40},
        {"name": "Siddheshwar Temple", "lat": 17.6756, "lon": 75.9103, "level": 20},
        {"name": "Saat Rasta", "lat": 17.6684, "lon": 75.9181, "level": 95}, # High congestion
    ]
    df_map = pd.DataFrame(solapur_coords)
    
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=pdk.ViewState(
            latitude=17.668,
            longitude=75.91,
            zoom=13,
            pitch=50,
        ),
        layers=[
            pdk.Layer(
                'HexagonLayer',
                data=df_map,
                get_position='[lon, lat]',
                radius=200,
                elevation_scale=4,
                elevation_range=[0, 1000],
                pickable=True,
                extruded=True,
            ),
            pdk.Layer(
                'ScatterplotLayer',
                data=df_map,
                get_position='[lon, lat]',
                get_color='[200, 30, 0, 160]',
                get_radius=200,
            ),
        ],
    ))

with tab3:
    st.header("🅿️ Smart Parking Management")
    parking_data = get_latest_parking()
    
    # Use mock data if database is empty
    if not parking_data:
        parking_data = [{
            'location': 'SMC Demo Parking Lot',
            'total_slots': 6,
            'available_slots': 2,
            'occupied_slots': 4,
            'occupancy_rate': 66.7,
            'slots': [
                {'slot_id': 1, 'status': 'occupied'},
                {'slot_id': 2, 'status': 'occupied'},
                {'slot_id': 3, 'status': 'available'},
                {'slot_id': 4, 'status': 'occupied'},
                {'slot_id': 5, 'status': 'available'},
                {'slot_id': 6, 'status': 'occupied'},
            ]
        }]
        st.info("📊 Showing demo data (MongoDB not connected)")
    
    if parking_data:
        pk = parking_data[0]
        c1, c2 = st.columns(2)
        c1.metric("Available Slots", f"{pk['available_slots']}/{pk['total_slots']}", "+1")
        c2.metric("Occupancy Rate", f"{pk['occupancy_rate']:.1f}%")
        
        # Display slot status
        st.subheader("Slot Status")
        cols = st.columns(3)
        for i, s in enumerate(pk['slots']):
            color = "🔴" if s['status'] == "occupied" else "🟢"
            slot_num = s.get('slot_id', i+1)
            cols[i % 3].markdown(f"### Slot {slot_num}\n{color} {s['status'].upper()}")
        
        # Additional parking info
        st.markdown("---")
        st.subheader("📍 Location")
        st.write(pk.get('location', 'SMC Parking Lot'))
        
        st.subheader("💡 Quick Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Peak Hour", "9:00 AM - 11:00 AM")
        col2.metric("Avg. Duration", "45 min")
        col3.metric("Today's Revenue", "₹2,450")

with tab1:
    if not DETECTOR_AVAILABLE:
        st.error("🚫 Live Monitoring requires YOLO detector")
        st.info("📦 Install with: `pip install ultralytics`")
        st.markdown("---")
        st.success("✅ **City Overview** and **Parking Module** tabs are working!")
        st.markdown("Check them out for parking analytics and congestion visualization.")
    else:
        @st.cache_resource
        def get_detector():
            # ✅ Main traffic + plate detector
            return TrafficDetector("models/yolov8n.pt", plate_model_path="models/plate_best.pt")

        detector = get_detector()

        # Sidebar controls
        st.sidebar.header("⚙️ Controls")
        source = st.sidebar.radio("Select Source", ["Webcam", "Video File", "Image File"])

        if source == "Video File":
            video_file = st.sidebar.file_uploader("Upload a video", type=["mp4", "avi", "mov"])
        elif source == "Image File":
            image_file = st.sidebar.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

        start = st.sidebar.button("▶ Start Detection")
        stop = st.sidebar.button("⏹ Stop Detection")

        if "running" not in st.session_state:
            st.session_state.running = False
        if "violations_log" not in st.session_state:
            st.session_state.violations_log = []

        if start:
            st.session_state.running = True
        if stop:
            st.session_state.running = False

        violation_container = st.sidebar.container()
        violation_container.header("⚠ Detected Violations")

        filter_type = st.sidebar.selectbox(
            "Filter Violations",
            ["All", "no_helmet", "signal_break", "overspeed", "wrong_way", "triple_riding", "track_crossing", "illegal_parking", "congestion"]
        )

        # Placeholders
        stframe = st.empty()
        table_placeholder = st.empty()

        cap, tmp_file = None, None
        try:
            if st.session_state.running:
                if source == "Webcam":
                    cap = cv2.VideoCapture(0)
                    if not cap.isOpened():
                        st.error("Couldn't open webcam.")
                        st.session_state.running = False

                elif source == "Video File":
                    if video_file is None:
                        st.error("Please upload a video file to start detection.")
                        st.session_state.running = False
                    else:
                        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4").name
                        with open(tmp_file, "wb") as f:
                            f.write(video_file.read())
                        cap = cv2.VideoCapture(tmp_file)
                        if not cap.isOpened():
                            st.error("Couldn't open uploaded video.")
                            st.session_state.running = False

                elif source == "Image File":
                    if image_file is None:
                        st.error("Please upload an image file to start detection.")
                        st.session_state.running = False
                    else:
                        # Process single image
                        file_bytes = np.asarray(bytearray(image_file.read()), dtype=np.uint8)
                        frame = cv2.imdecode(file_bytes, 1)
                        annotated, dets, tracked_list, violations, tl_state = detector.detect_frame(frame)
                        annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                        stframe.image(annotated_rgb, channels="RGB", use_container_width=True)

                        if violations:
                            for v in violations:
                                plate = v.get("plate", "NOT_DETECTED")
                                violation_container.markdown(f"**{v['type'].upper()}** — Plate: {plate}")

                        st.session_state.running = False  # run once for image

            # Detection Loop for webcam/video
            while st.session_state.running and cap and cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    st.warning("Video finished or invalid frame.")
                    st.session_state.running = False
                    break

                # Run detector
                annotated, dets, tracked_list, violations, tl_state = detector.detect_frame(frame)

                # Content filter
                detected_classes = {d.get("cls_name", "unknown") for d in dets}
                content_type = classify_content(detected_classes)
                if content_type in ["invalid", "unclear"]:
                    continue

                # Show video
                annotated_rgb = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
                stframe.image(annotated_rgb, channels="RGB", use_container_width=True)

                # ---------------------------
                # Process Violations
                # ---------------------------
                if violations:
                    for v in violations:
                        vtype = v.get("type", "unknown")
                        plate = v.get("plate", "NOT_DETECTED")
                        tid = v.get("track_id", -1)

                        # 🔹 Snapshot save
                        os.makedirs("snapshots", exist_ok=True)
                        snapshot_name = f"snapshots/{time.strftime('%Y%m%d_%H%M%S')}_tid{tid}_{vtype}.jpg"
                        cv2.imwrite(snapshot_name, annotated)  # save annotated frame

                        # Save to MongoDB with snapshot_path
                        record = {
                            "vehicle_no": plate,
                            "violation_type": vtype,
                            "track_id": tid,
                            "cls": v.get("cls_name", "unknown"),
                            "conf": float(v.get("conf", 0.0)),
                            "speed_kmph": v.get("speed_kmph"),
                            "reason": v.get("reason", ""),
                            "tl_state": v.get("tl_state", tl_state),
                            "snapshot_path": snapshot_name,
                            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        }
                        try:
                            insert_violation(record)
                        except Exception as e:
                            st.sidebar.error(f"DB Insert Error: {e}")

                        # Append to session log
                        st.session_state.violations_log.append({
                            "Time": record["timestamp"],
                            "Violation": vtype,
                            "Plate": plate,
                            "Track ID": tid,
                            "Confidence": round(record["conf"], 2),
                            "Speed": record["speed_kmph"],
                            "Snapshot": snapshot_name,
                        })

                        violation_container.markdown(
                            f"**{vtype.UPPER()}** — {v.get('cls_name','?')} (plate {plate})"
                        )
                        violation_container.image(
                            cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB),
                            caption=f"Violation: {vtype} | Plate: {plate}",
                            use_container_width=True
                        )

                    # Table update
                    if st.session_state.violations_log:
                        df = pd.DataFrame(st.session_state.violations_log)
                        if filter_type != "All":
                            df = df[df["Violation"] == filter_type]
                        table_placeholder.dataframe(df, use_container_width=True)

                time.sleep(0.1)

        finally:
            if cap:
                cap.release()
            if tmp_file and os.path.exists(tmp_file):
                os.remove(tmp_file)

# ---------------------------
# 📊 Audit Report Button
# ---------------------------
st.sidebar.markdown("---")
if st.sidebar.button("📊 Generate Audit Report"):
    if not AUDIT_AVAILABLE:
        st.sidebar.error("Audit module not available")
    else:
        df_metrics = pd.DataFrame([
            {"class": "car", "precision": 0.91, "recall": 0.87, "f1": 0.89},
            {"class": "truck", "precision": 0.85, "recall": 0.81, "f1": 0.83},
        ])

        df_violations = pd.DataFrame(st.session_state.violations_log)

        examples = [
            {"title": "Violation Example 1", "img": "snapshots/example1.png"},
            {"title": "Violation Example 2", "img": "snapshots/example2.png"},
        ]

        try:
            generate_report.generate(
                model_name="yolov8-traffic",
                metrics_df=df_metrics,
                violations_df=df_violations,
                adv_json=None,
                examples=examples,
                out_html="audit_report.html"
            )
            insert_report({
                "model": "yolov8-traffic",
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "metrics": df_metrics.to_dict(orient="records"),
                "violations": df_violations.to_dict(orient="records"),
                "examples": examples
            })
            st.sidebar.success("Audit report generated & saved in MongoDB ✅")
        except Exception as e:
            st.sidebar.error(f"Report save error: {e}")
