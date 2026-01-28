"""
Parking Module for Smart Parking Management
Detects parking slot occupancy using YOLO detections and predefined slot regions.
"""
import cv2
import numpy as np
from datetime import datetime
from db import insert_parking_status


class ParkingManager:
    """
    Manages parking slot detection and availability tracking.
    """
    
    def __init__(self, location="SMC_Parking_Lot_1"):
        self.location = location
        self.parking_slots = []  # List of slot definitions
        self.slot_status = {}  # Track status of each slot
        self.last_update_time = None
        
    def define_parking_slots(self, slots):
        """
        Define parking slot regions.
        
        Args:
            slots: List of dicts with slot info:
                   [{"id": 1, "polygon": [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]}, ...]
        """
        self.parking_slots = slots
        for slot in slots:
            self.slot_status[slot["id"]] = {
                "status": "available",
                "vehicle_id": None,
                "occupied_since": None
            }
    
    def auto_define_grid_slots(self, frame_width, frame_height, rows=2, cols=3, 
                               start_x=50, start_y=100, slot_width=150, slot_height=80, 
                               gap_x=20, gap_y=20):
        """
        Automatically create a grid of parking slots.
        Useful for quick setup on parking lot videos.
        
        Args:
            frame_width, frame_height: Video dimensions
            rows, cols: Grid dimensions
            start_x, start_y: Top-left corner of first slot
            slot_width, slot_height: Dimensions of each slot
            gap_x, gap_y: Spacing between slots
        """
        slots = []
        slot_id = 1
        
        for row in range(rows):
            for col in range(cols):
                x1 = start_x + col * (slot_width + gap_x)
                y1 = start_y + row * (slot_height + gap_y)
                x2 = x1 + slot_width
                y2 = y1 + slot_height
                
                # Define as polygon (rectangle)
                polygon = [
                    (x1, y1),  # Top-left
                    (x2, y1),  # Top-right
                    (x2, y2),  # Bottom-right
                    (x1, y2)   # Bottom-left
                ]
                
                slots.append({
                    "id": slot_id,
                    "polygon": polygon,
                    "row": row,
                    "col": col
                })
                slot_id += 1
        
        self.define_parking_slots(slots)
        print(f"[PARKING] Auto-defined {len(slots)} parking slots in {rows}x{cols} grid")
    
    def check_slot_occupancy(self, tracked_objects):
        """
        Check which parking slots are occupied based on tracked vehicles.
        
        Args:
            tracked_objects: List of tracked vehicles from detector
            
        Returns:
            dict: Updated slot status
        """
        # Reset all slots to available first
        for slot_id in self.slot_status:
            self.slot_status[slot_id]["status"] = "available"
            self.slot_status[slot_id]["vehicle_id"] = None
        
        # Check each slot for vehicle presence
        for slot in self.parking_slots:
            slot_id = slot["id"]
            polygon = np.array(slot["polygon"], np.int32)
            
            # Check if any vehicle centroid is inside this slot
            for obj in tracked_objects:
                centroid = obj.get("centroid")
                if centroid:
                    point = (float(centroid[0]), float(centroid[1]))
                    
                    # Check if point is inside polygon
                    if cv2.pointPolygonTest(polygon, point, False) >= 0:
                        # Mark slot as occupied
                        if self.slot_status[slot_id]["status"] == "available":
                            self.slot_status[slot_id]["occupied_since"] = datetime.now()
                        
                        self.slot_status[slot_id]["status"] = "occupied"
                        self.slot_status[slot_id]["vehicle_id"] = obj.get("track_id")
                        break  # One vehicle per slot
        
        return self.slot_status
    
    def get_availability_summary(self):
        """
        Get summary of parking availability.
        
        Returns:
            dict: Summary with total, available, and occupied counts
        """
        total_slots = len(self.parking_slots)
        occupied_slots = sum(1 for s in self.slot_status.values() if s["status"] == "occupied")
        available_slots = total_slots - occupied_slots
        
        return {
            "location": self.location,
            "total_slots": total_slots,
            "available_slots": available_slots,
            "occupied_slots": occupied_slots,
            "occupancy_rate": (occupied_slots / total_slots * 100) if total_slots > 0 else 0,
            "timestamp": datetime.now()
        }
    
    def save_to_database(self):
        """
        Save current parking status to database.
        """
        summary = self.get_availability_summary()
        
        # Prepare detailed slot information
        slots_detail = []
        for slot in self.parking_slots:
            slot_id = slot["id"]
            status = self.slot_status[slot_id]
            slots_detail.append({
                "slot_id": slot_id,
                "status": status["status"],
                "vehicle_id": status.get("vehicle_id"),
                "occupied_since": status.get("occupied_since")
            })
        
        record = {
            "location": self.location,
            "timestamp": datetime.now(),
            "total_slots": summary["total_slots"],
            "available_slots": summary["available_slots"],
            "occupied_slots": summary["occupied_slots"],
            "occupancy_rate": summary["occupancy_rate"],
            "slots": slots_detail
        }
        
        insert_parking_status(record)
        self.last_update_time = datetime.now()
    
    def draw_slots_on_frame(self, frame):
        """
        Draw parking slots on frame with color-coded status.
        
        Args:
            frame: OpenCV image
            
        Returns:
            frame: Image with slots drawn
        """
        for slot in self.parking_slots:
            slot_id = slot["id"]
            polygon = np.array(slot["polygon"], np.int32)
            status = self.slot_status[slot_id]["status"]
            
            # Color: Green for available, Red for occupied
            color = (0, 255, 0) if status == "available" else (0, 0, 255)
            
            # Draw polygon
            cv2.polylines(frame, [polygon], isClosed=True, color=color, thickness=2)
            
            # Fill with semi-transparent color
            overlay = frame.copy()
            cv2.fillPoly(overlay, [polygon], color)
            cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
            
            # Add slot ID text
            centroid_x = int(np.mean([p[0] for p in slot["polygon"]]))
            centroid_y = int(np.mean([p[1] for p in slot["polygon"]]))
            
            text = f"#{slot_id}"
            cv2.putText(frame, text, (centroid_x - 15, centroid_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Add summary text
        summary = self.get_availability_summary()
        summary_text = f"Available: {summary['available_slots']}/{summary['total_slots']}"
        cv2.putText(frame, summary_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
        
        return frame


# Example usage configuration for Solapur SMC
def create_smc_parking_config():
    """
    Create a sample parking configuration for SMC demonstration.
    Adjust coordinates based on actual camera feed.
    """
    manager = ParkingManager(location="Solapur_Bus_Stand_Parking")
    
    # Option 1: Auto-generate grid (easier for demo)
    # manager.auto_define_grid_slots(
    #     frame_width=1920, frame_height=1080,
    #     rows=2, cols=3,
    #     start_x=100, start_y=200,
    #     slot_width=200, slot_height=120,
    #     gap_x=30, gap_y=30
    # )
    
    # Option 2: Manual slot definition (for real deployment)
    custom_slots = [
        {"id": 1, "polygon": [(100, 200), (300, 200), (300, 320), (100, 320)]},
        {"id": 2, "polygon": [(330, 200), (530, 200), (530, 320), (330, 320)]},
        {"id": 3, "polygon": [(560, 200), (760, 200), (760, 320), (560, 320)]},
    ]
    manager.define_parking_slots(custom_slots)
    
    return manager
