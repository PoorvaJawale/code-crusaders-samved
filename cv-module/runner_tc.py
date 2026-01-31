import cv2
import argparse
from ultralytics import YOLO
from collections import defaultdict, deque
from datetime import datetime
import numpy as np


from congestion_analyse.speed import compute_average_speed
from congestion_analyse.congestion_state import CongestionDetector
from congestion_analyse.lane_geometry import point_in_polygon

from congestion_analyse.density import compute_density_polygon


# -------------------------------------------------
# CLI ARGUMENTS
# -------------------------------------------------
parser = argparse.ArgumentParser("Adaptive Lane-wise Traffic Congestion")
parser.add_argument("--video", required=True, help="Path to traffic video")
parser.add_argument("--model", default="models/yolov8n.pt", help="YOLO model")
args = parser.parse_args()

# -------------------------------------------------
# INITIALIZATION
# -------------------------------------------------
model = YOLO(args.model)
cap = cv2.VideoCapture(args.video)

fps = cap.get(cv2.CAP_PROP_FPS)
frame_count = 0

track_history = defaultdict(list)
vehicle_points = deque(maxlen=500)

ROAD_ROI = None
ROAD_CAPACITY = 60

lane_detectors = {
    0: CongestionDetector(window_size=15),
    1: CongestionDetector(window_size=15)
}

print("\n[INFO] Adaptive Lane-wise Traffic Congestion Runner Started")
print(f"[INFO] Video: {args.video}")
print(f"[INFO] FPS: {fps}\n")

# -------------------------------------------------
# HELPERS
# -------------------------------------------------

def compute_lane_speed(lane_objects, track_history, fps):
    lane_tracks = {}
    for obj in lane_objects:
        tid = obj["id"]
        if tid in track_history:
            lane_tracks[tid] = track_history[tid]
    return compute_average_speed(lane_tracks, fps)


def estimate_road_roi(points, margin=40):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    if not xs or not ys:
        return None
    return (
        max(min(xs) - margin, 0),
        max(min(ys) - margin, 0),
        max(xs) + margin,
        max(ys) + margin
    )


def estimate_lane_divider(points):
    xs = [p[0] for p in points]
    hist, bins = np.histogram(xs, bins=50)
    divider_bin = np.argmin(hist)
    return int((bins[divider_bin] + bins[divider_bin + 1]) / 2)


def build_lane_polygons(road_roi, divider_x):
    x1, y1, x2, y2 = road_roi

    lane1 = [
        (x1, y2),
        (divider_x, y2),
        (divider_x - 40, y1),
        (x1 + 40, y1)
    ]

    lane2 = [
        (divider_x, y2),
        (x2, y2),
        (x2 - 40, y1),
        (divider_x + 40, y1)
    ]

    return lane1, lane2


# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    timestamp = datetime.now().strftime("%H:%M:%S")

    results = model.track(
        frame,
        persist=True,
        conf=0.25,
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

            vehicle_points.append((cx, cy))
            track_history[int(box.id[0])].append((cx, cy))

            tracked_objects.append({
                "id": int(box.id[0]),
                "bbox": [x1, y1, x2, y2],
                "cls": cls
            })

    # -------- ROAD ROI --------
    if ROAD_ROI is None and len(vehicle_points) > 80:
        ROAD_ROI = estimate_road_roi(vehicle_points)
        print(f"[INFO] Road ROI detected: {ROAD_ROI}")

    if ROAD_ROI is None:
        continue

    # -------- LANE POLYGONS --------
    divider_x = estimate_lane_divider(vehicle_points)
    lane1_poly, lane2_poly = build_lane_polygons(ROAD_ROI, divider_x)

    lane1_objects, lane2_objects = [], []

    for obj in tracked_objects:
        cx = (obj["bbox"][0] + obj["bbox"][2]) // 2
        cy = (obj["bbox"][1] + obj["bbox"][3]) // 2

        if point_in_polygon((cx, cy), lane1_poly):
            lane1_objects.append(obj)
        elif point_in_polygon((cx, cy), lane2_poly):
            lane2_objects.append(obj)

    # -------- LANE 1 --------
    d1 = compute_density_polygon(lane1_objects, lane1_poly, ROAD_CAPACITY)

    s1 = compute_lane_speed(lane1_objects, track_history, fps)
    lane_detectors[0].update(d1["density_level"], s1["speed_level"])
    state1 = lane_detectors[0].get_state()

    # -------- LANE 2 --------
    d2 = compute_density_polygon(lane2_objects, lane2_poly, ROAD_CAPACITY)

    s2 = compute_lane_speed(lane2_objects, track_history, fps)
    lane_detectors[1].update(d2["density_level"], s2["speed_level"])
    state2 = lane_detectors[1].get_state()

    # -------- CONSOLE LOG --------
    print(
        f"[{timestamp}] Frame {frame_count} | "
        f"Lane1: {d1['density_level']} / {s1['speed_level']} → {state1} | "
        f"Lane2: {d2['density_level']} / {s2['speed_level']} → {state2}"
    )

    # -------- DRAW LANES --------
    cv2.polylines(frame, [np.array(lane1_poly)], True, (0, 255, 255), 3)
    cv2.polylines(frame, [np.array(lane2_poly)], True, (0, 255, 255), 3)

    cv2.putText(frame, f"Lane 1 | {state1}", lane1_poly[3],
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

    cv2.putText(frame, f"Lane 2 | {state2}", lane2_poly[3],
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

    cv2.imshow("Adaptive Lane-wise Traffic Congestion", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# -------------------------------------------------
# CLEANUP
# -------------------------------------------------
cap.release()
cv2.destroyAllWindows()
print("\n[INFO] Runner finished")
