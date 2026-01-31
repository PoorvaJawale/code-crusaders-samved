"""
calibrate_lanes.py
------------------
Lane calibration using an empty road image.

Usage:
python calibrate_lanes.py --image empty_road.jpg --out lane_polygons.json

Instructions:
- Click 4 points for Lane 1 (clockwise or anticlockwise)
- Press 'n' to move to Lane 2
- Click 4 points for Lane 2
- Press 's' to save and exit
"""

import cv2
import json
import argparse

import numpy as np

# ------------------------
# CLI ARGUMENTS
# ------------------------
parser = argparse.ArgumentParser("Lane Calibration Tool")
parser.add_argument("--image", required=True, help="Path to empty road image")
parser.add_argument("--out", default="lane_polygons.json", help="Output JSON file")
args = parser.parse_args()

# ------------------------
# LOAD IMAGE
# ------------------------
img = cv2.imread(args.image)
if img is None:
    raise FileNotFoundError("Could not load image")

clone = img.copy()
current_lane = 1
points = {1: [], 2: []}

print("\n[INFO] Lane Calibration Started")
print("[INFO] Click 4 points for Lane 1")
print("[INFO] Press 'n' to switch lane")
print("[INFO] Press 's' to save & exit\n")

# ------------------------
# MOUSE CALLBACK
# ------------------------
def mouse_callback(event, x, y, flags, param):
    global current_lane, img

    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points[current_lane]) < 4:
            points[current_lane].append((x, y))
            cv2.circle(img, (x, y), 5, (0, 255, 255), -1)
            cv2.putText(
                img,
                f"{current_lane}-{len(points[current_lane])}",
                (x + 5, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 255),
                1
            )

# ------------------------
# WINDOW SETUP
# ------------------------
cv2.namedWindow("Lane Calibration")
cv2.setMouseCallback("Lane Calibration", mouse_callback)

# ------------------------
# MAIN LOOP
# ------------------------
while True:
    display = img.copy()

    # Draw Lane 1
    if len(points[1]) > 1:
        cv2.polylines(display, [cv2.convexHull(
            cv2.UMat(np.array(points[1], dtype=int))
        )], False, (0, 255, 255), 2)

    # Draw Lane 2
    if len(points[2]) > 1:
        cv2.polylines(display, [cv2.convexHull(
            cv2.UMat(np.array(points[2], dtype=int))
        )], False, (255, 255, 0), 2)

    cv2.putText(
        display,
        f"Current Lane: {current_lane}",
        (20, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (0, 255, 255),
        2
    )

    cv2.imshow("Lane Calibration", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('n'):
        if current_lane == 1:
            if len(points[1]) != 4:
                print("[WARN] Lane 1 needs exactly 4 points")
            else:
                current_lane = 2
                print("[INFO] Switched to Lane 2")

    elif key == ord('s'):
        if len(points[1]) == 4 and len(points[2]) == 4:
            break
        else:
            print("[WARN] Both lanes must have exactly 4 points")

    elif key == ord('r'):
        img = clone.copy()
        points = {1: [], 2: []}
        current_lane = 1
        print("[INFO] Reset calibration")

    elif key == ord('q'):
        print("[INFO] Exiting without saving")
        cv2.destroyAllWindows()
        exit()

# ------------------------
# SAVE POLYGONS
# ------------------------
lane_data = {
    "lane_1": points[1],
    "lane_2": points[2]
}

with open(args.out, "w") as f:
    json.dump(lane_data, f, indent=2)

print(f"\n[OK] Lane polygons saved to {args.out}")

cv2.destroyAllWindows()
