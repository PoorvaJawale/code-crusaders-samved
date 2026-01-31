"""
calibrate_lanes_from_video.py
-----------------------------
Lane calibration using the FIRST FRAME of the video.

Usage:
python calibrate_lanes_from_video.py --video traffic.mp4 --out lane_polygons.json

Instructions:
- Click 4 points for UPPER lane (far lane)
- Press 'n' to switch to LOWER lane (near lane)
- Click 4 points for LOWER lane
- Press 's' to save
- Press 'r' to reset
- Press 'q' to quit without saving
"""

import cv2
import json
import argparse
import numpy as np

# -------------------------------------------------
# CLI ARGUMENTS
# -------------------------------------------------
parser = argparse.ArgumentParser("Lane Calibration from Video")
parser.add_argument("--video", required=True, help="Path to traffic video")
parser.add_argument("--out", default="lane_polygons.json", help="Output JSON file")
args = parser.parse_args()

# -------------------------------------------------
# LOAD FIRST FRAME
# -------------------------------------------------
cap = cv2.VideoCapture(args.video)
ret, frame = cap.read()
cap.release()

if not ret:
    raise RuntimeError("Could not read first frame from video")

original = frame.copy()
h, w = frame.shape[:2]

# -------------------------------------------------
# STATE
# -------------------------------------------------
current_lane = "upper"   # upper -> lower
points = {"upper": [], "lower": []}

print("\n[INFO] Lane Calibration Started (from video frame)")
print("[INFO] Click 4 points for UPPER lane (far lane)")
print("[INFO] Press 'n' to switch to LOWER lane")
print("[INFO] Press 's' to save")
print("[INFO] Press 'r' to reset")
print("[INFO] Press 'q' to quit\n")

# -------------------------------------------------
# HELPERS
# -------------------------------------------------
def order_polygon(pts):
    """Ensure consistent clockwise polygon order"""
    pts = np.array(pts)
    center = np.mean(pts, axis=0)
    angles = np.arctan2(pts[:, 1] - center[1], pts[:, 0] - center[0])
    return pts[np.argsort(angles)].astype(int).tolist()

# -------------------------------------------------
# MOUSE CALLBACK
# -------------------------------------------------
def mouse_callback(event, x, y, flags, param):
    global current_lane
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points[current_lane]) < 4:
            points[current_lane].append((x, y))

# -------------------------------------------------
# WINDOW SETUP
# -------------------------------------------------
cv2.namedWindow("Lane Calibration")
cv2.setMouseCallback("Lane Calibration", mouse_callback)

# -------------------------------------------------
# MAIN LOOP
# -------------------------------------------------
while True:
    display = original.copy()

    # Draw polygons
    for lane_name, color in [("upper", (0, 255, 255)), ("lower", (255, 255, 0))]:
        if len(points[lane_name]) > 1:
            cv2.polylines(
                display,
                [np.array(points[lane_name], dtype=int)],
                False,
                color,
                2
            )
        for (x, y) in points[lane_name]:
            cv2.circle(display, (x, y), 5, (0, 0, 255), -1)

    # UI text
    cv2.putText(
        display,
        f"Current Lane: {current_lane.upper()}",
        (20, 40),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 0),
        2
    )

    cv2.imshow("Lane Calibration", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('n') and current_lane == "upper":
        if len(points["upper"]) == 4:
            current_lane = "lower"
            print("[INFO] Switched to LOWER lane")
        else:
            print("[WARN] Upper lane needs exactly 4 points")

    elif key == ord('s'):
        if len(points["upper"]) == 4 and len(points["lower"]) == 4:
            break
        else:
            print("[WARN] Both lanes must have exactly 4 points")

    elif key == ord('r'):
        points = {"upper": [], "lower": []}
        current_lane = "upper"
        print("[INFO] Reset calibration")

    elif key == ord('q'):
        print("[INFO] Exiting without saving")
        cv2.destroyAllWindows()
        exit()

# -------------------------------------------------
# ORDER & SAVE POLYGONS
# -------------------------------------------------
lane_data = {
    "lane_1": order_polygon(points["upper"]),
    "lane_2": order_polygon(points["lower"]),
    "frame_width": w,
    "frame_height": h
}

with open(args.out, "w") as f:
    json.dump(lane_data, f, indent=2)

cv2.destroyAllWindows()
print(f"\n[OK] Lane polygons saved to {args.out}")
