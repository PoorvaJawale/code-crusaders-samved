import sys
import os

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)
from rule_engine import RuleEngine
import time

engine = RuleEngine()
engine.congestion_roi = (80, 180, 600, 320)

tracked_objects = []
track_history = {}

for i in range(25):
    x, y = 110+i*5, 215
    tracked_objects.append({
        "track_id": i,
        "bbox": [x-10, y-15, x+10, y+15],
        "cls_name": "car",
        "centroid": (x, y)
    })

for f in range(30):

    # 🚦 Phase 1: Free flow
    if f < 10:
        track_history = {
            i: [(x, y), (x+2, y)] for i, (x, y) in enumerate(
                [(110+i*5, 215) for i in range(25)]
            )
        }

    # 🚦 Phase 2: Slow traffic
    elif f < 20:
        track_history = {
            i: [(x, y), (x+0.3, y)] for i, (x, y) in enumerate(
                [(110+i*5, 215) for i in range(25)]
            )
        }

    # 🚦 Phase 3: Jam
    else:
        track_history = {
            i: [(x, y), (x, y)] for i, (x, y) in enumerate(
                [(110+i*5, 215) for i in range(25)]
            )
        }

    out = engine.check_congestion(tracked_objects, track_history)
    print(f"Frame {f}: {out['state']}")
    time.sleep(0.1)
