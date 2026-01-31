def is_inside_roi(bbox, roi):
    """
    Check if bbox center lies inside ROI.

    bbox: [x1, y1, x2, y2]
    roi:  (x1, y1, x2, y2)
    """
    bx1, by1, bx2, by2 = bbox
    rx1, ry1, rx2, ry2 = roi

    cx = (bx1 + bx2) / 2
    cy = (by1 + by2) / 2

    return rx1 <= cx <= rx2 and ry1 <= cy <= ry2
