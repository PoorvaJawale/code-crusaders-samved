# congestion_analyse/congestion_state.py

from collections import deque

# numeric encodings (for stability)
DENSITY_SCORE = {
    "LOW": 0,
    "MEDIUM": 1,
    "HIGH": 2
}

SPEED_SCORE = {
    "HIGH": 0,    # fast traffic = good
    "MEDIUM": 1,
    "LOW": 2      # slow traffic = bad
}


class CongestionDetector:
    """
    Lane-wise congestion detector with temporal smoothing.
    """

    def __init__(self, window_size=15):
        self.window_size = window_size
        self.density_hist = deque(maxlen=window_size)
        self.speed_hist = deque(maxlen=window_size)

    def update(self, density_level, speed_level):
        """
        density_level: LOW / MEDIUM / HIGH
        speed_level: HIGH / MEDIUM / LOW
        """
        if density_level not in DENSITY_SCORE:
            return
        if speed_level not in SPEED_SCORE:
            return

        self.density_hist.append(DENSITY_SCORE[density_level])
        self.speed_hist.append(SPEED_SCORE[speed_level])

    def get_state(self):
        """
        Returns final congestion state using averaged scores.
        """
        if not self.density_hist or not self.speed_hist:
            return "UNKNOWN"

        avg_density = sum(self.density_hist) / len(self.density_hist)
        avg_speed = sum(self.speed_hist) / len(self.speed_hist)

        # -------------------------
        # DECISION LOGIC
        # -------------------------

        # Severe congestion: high density + very low speed
        if avg_density >= 1.6 and avg_speed >= 1.6:
            return "SEVERE_CONGESTION"

        # High congestion: medium/high density + low speed
        if avg_density >= 1.0 and avg_speed >= 1.2:
            return "HIGH_CONGESTION"

        # Moderate congestion: high density but moving
        if avg_density >= 1.5 and avg_speed < 1.2:
            return "MODERATE_CONGESTION"

        # Free flow: low density regardless of speed
        if avg_density < 0.5:
            return "FREE_FLOW"

        return "NORMAL"
