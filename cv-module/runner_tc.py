import cv2
import argparse
import json
from ultralytics import YOLO
from collections import defaultdict
from datetime import datetime
import numpy as np

from congestion_analyse.speed import compute_average_speed
from congestion_analyse.congestion_state import CongestionDetector
from congestion_analyse.lane_geometry import point_in_polygon
from congestion_analyse.density import compute_density_polygon


# -------------------------------------------------
# CONFIG
# -------------------------------------------------
FRAME_SKIP = 15


# -------------------------------------------------
# CLI ARGUMENTS
# -------------------------------------------------
parser = argparse.ArgumentParser("Adaptive Lane-wise Traffic Congestion")
parser.add_argument("--video", required=True, help="Path to traffic video")
parser.add_argument("--model", default="models/yolov8n.pt", help="YOLO model path")
parser.add_argument(
    "--lanes_json",
    default="lane_polygons.json",
    help="Path to calibrated lane polygons JSON"
)
args = parser.parse_args()


# -------------------------------------------------
# LOAD CALIBRATED LANES
# -------------------------------------------------
with open(args.lanes_json, "r") as f:
    lane_data = json.load(f)

lane1_poly = lane_data["lane_1"]
lane2_poly = lane_data["lane_2"]

print("[INFO] Loaded calibrated lane polygons")


# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------
model = YOLO(args.model)
cap = cv2.VideoCapture(args.video)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0

track_history = defaultdict(list)

ROAD_CAPACITY = 20

lane_detectors = {
    0: CongestionDetector(window_size=15),
    1: CongestionDetector(window_size=15)
}

print("\n[INFO] Adaptive Lane-wise Traffic Congestion Runner Started")
print(f"[INFO] Video: {args.video}")
print(f"[INFO] FPS: {fps}")
print(f"[INFO] Frame skip: {FRAME_SKIP}\n")


# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def compute_lane_speed(lane_objects, track_history, fps):
    lane_tracks = {}
    for obj in lane_objects:
        tid = obj["id"]
        if tid in track_history:
            lane_tracks[tid] = track_history[tid]
    return compute_average_speed(lane_tracks, fps / FRAME_SKIP)


def compute_vehicle_speed(track, fps):
    if len(track) < 2:
        return 0.0

    (x1, y1) = track[-2]
    (x2, y2) = track[-1]

    pixel_dist = ((x2 - x1)**2 + (y2 - y1)**2) ** 0.5
    return pixel_dist * (fps / FRAME_SKIP)


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret or frame is None:
        break

    frame_count += 1

    # -------- FRAME SKIP --------
    if frame_count % FRAME_SKIP != 0:
        continue

    timestamp = datetime.now().strftime("%H:%M:%S")

    # -------- YOLO TRACK --------
    results = model.track(
        frame,
        persist=True,
        conf=0.10,
        iou=0.5,
        verbose=False
    )[0]

    tracked_objects = []

    if results.boxes is not None:
        for box in results.boxes:
            if box.id is None:
                continue

            cls = results.names[int(box.cls[0])].lower()
            if cls not in ["car", "truck", "bus", "motorbike", "bicycle"]:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            tid = int(box.id[0])
            track_history[tid].append((cx, cy))

            tracked_objects.append({
                "id": tid,
                "bbox": [x1, y1, x2, y2],
                "cls": cls
            })

    # -------- LANE ASSIGNMENT --------
    lane1_objects, lane2_objects = [], []

    for obj in tracked_objects:
        cx = (obj["bbox"][0] + obj["bbox"][2]) // 2
        cy = (obj["bbox"][1] + obj["bbox"][3]) // 2

        if point_in_polygon((cx, cy), lane1_poly):
            lane1_objects.append(obj)
        elif point_in_polygon((cx, cy), lane2_poly):
            lane2_objects.append(obj)

    count_lane1 = len(lane1_objects)
    count_lane2 = len(lane2_objects)

    # -------- ANALYSIS --------
    d1 = compute_density_polygon(lane1_objects, lane1_poly, ROAD_CAPACITY)
    s1 = compute_lane_speed(lane1_objects, track_history, fps)
    lane_detectors[0].update(d1["density_level"], s1["speed_level"])
    state1 = lane_detectors[0].get_state()

    d2 = compute_density_polygon(lane2_objects, lane2_poly, ROAD_CAPACITY)
    s2 = compute_lane_speed(lane2_objects, track_history, fps)
    lane_detectors[1].update(d2["density_level"], s2["speed_level"])
    state2 = lane_detectors[1].get_state()

    # -------- LOG --------
    print(
        f"[{timestamp}] Frame {frame_count} | "
        f"Lane1: {count_lane1} | {d1['density_level']} / {s1['speed_level']} → {state1} | "
        f"Lane2: {count_lane2} | {d2['density_level']} / {s2['speed_level']} → {state2}"
    )

    # -------- DRAW VEHICLES --------
    for obj in lane1_objects:
        x1, y1, x2, y2 = obj["bbox"]
        speed = compute_vehicle_speed(track_history[obj["id"]], fps)
        cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,255), 2)
        cv2.putText(frame, f"{obj['cls']} | {speed:.1f}",
                    (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,255), 1)

    for obj in lane2_objects:
        x1, y1, x2, y2 = obj["bbox"]
        speed = compute_vehicle_speed(track_history[obj["id"]], fps)
        cv2.rectangle(frame, (x1,y1), (x2,y2), (255,255,0), 2)
        cv2.putText(frame, f"{obj['cls']} | {speed:.1f}",
                    (x1, y1-8), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,255,0), 1)

    # -------- DRAW LANES --------
    cv2.polylines(frame, [np.array(lane1_poly)], True, (0,255,255), 3)
    cv2.polylines(frame, [np.array(lane2_poly)], True, (255,255,0), 3)

    cv2.imshow("Adaptive Lane-wise Traffic Congestion", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# -------------------------------------------------
# CLEANUP
# -------------------------------------------------
cap.release()
cv2.destroyAllWindows()
print("\n[INFO] Runner finished")
