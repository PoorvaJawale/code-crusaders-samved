import cv2
import numpy as np

def point_in_polygon(point, polygon):
    """
    point: (x, y)
    polygon: [(x,y), (x,y), ...]
    """
    return cv2.pointPolygonTest(
        np.array(polygon, dtype=np.int32),
        point,
        False
    ) >= 0


def build_lane_polygons(road_roi, divider_x):
    """
    Build trapezoidal lane polygons from divider
    """
    x1, y1, x2, y2 = road_roi

    lane1 = [
        (x1, y2),
        (divider_x, y2),
        (divider_x - 40, y1),
        (x1 + 40, y1),
    ]

    lane2 = [
        (divider_x, y2),
        (x2, y2),
        (x2 - 40, y1),
        (divider_x + 40, y1),
    ]

    return lane1, lane2
