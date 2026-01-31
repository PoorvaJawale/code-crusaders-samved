# congestion_analyse/speed.py

from .config import SPEED_THRESHOLDS

def compute_average_speed(track_history, fps):
    """
    Returns average speed and speed level.

    Speed is relative (pixel/sec) unless calibrated.
    """
    total_speed = 0
    count = 0

    for positions in track_history.values():
        if len(positions) < 2:
            continue

        (x1, y1) = positions[-2]
        (x2, y2) = positions[-1]

        pixel_dist = ((x2-x1)**2 + (y2-y1)**2) ** 0.5
        speed = pixel_dist * fps

        total_speed += speed
        count += 1

    avg_speed = total_speed / count if count > 0 else 0

    # speed classification (conceptual m/s thresholds)
    if avg_speed < 10:
        speed_level = "LOW"
    elif avg_speed < 20:
        speed_level = "MEDIUM"
    else:
        speed_level = "HIGH"

    return {
        "avg_speed": avg_speed,
        "speed_level": speed_level
    }
