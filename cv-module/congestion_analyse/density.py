# congestion_analyse/density.py

import cv2
import numpy as np

from .roi import is_inside_roi
from .config import VEHICLE_WEIGHTS


# -------------------------------------------------
# RECTANGULAR ROI DENSITY (KEEP AS-IS)
# -------------------------------------------------
def compute_density(tracked_objects, roi, road_capacity=60):
    """
    Computes weighted density inside a rectangular ROI.
    """
    occupancy = 0.0

    for obj in tracked_objects:
        if not is_inside_roi(obj["bbox"], roi):
            continue

        cls = obj["cls"].lower()
        if cls in VEHICLE_WEIGHTS:
            occupancy += VEHICLE_WEIGHTS[cls]

    density_ratio = occupancy / road_capacity if road_capacity > 0 else 0

    if density_ratio < 0.4:
        density_level = "LOW"
    elif density_ratio < 0.7:
        density_level = "MEDIUM"
    else:
        density_level = "HIGH"

    return {
        "occupancy": occupancy,
        "density_ratio": density_ratio,
        "density_level": density_level
    }


# -------------------------------------------------
# POLYGON LANE DENSITY (NEW – REQUIRED)
# -------------------------------------------------
def compute_density_polygon(tracked_objects, lane_polygon, road_capacity=60):
    """
    Computes weighted density inside a polygonal lane.
    """

    occupancy = 0.0
    poly = np.array(lane_polygon, dtype=np.int32)

    for obj in tracked_objects:
        cx = (obj["bbox"][0] + obj["bbox"][2]) // 2
        cy = (obj["bbox"][1] + obj["bbox"][3]) // 2

        inside = cv2.pointPolygonTest(poly, (cx, cy), False)

        if inside >= 0:
            cls = obj["cls"].lower()
            if cls in VEHICLE_WEIGHTS:
                occupancy += VEHICLE_WEIGHTS[cls]

    density_ratio = occupancy / road_capacity if road_capacity > 0 else 0

    if density_ratio < 0.4:
        density_level = "LOW"
    elif density_ratio < 0.7:
        density_level = "MEDIUM"
    else:
        density_level = "HIGH"

    return {
        "occupancy": occupancy,
        "density_ratio": density_ratio,
        "density_level": density_level
    }
