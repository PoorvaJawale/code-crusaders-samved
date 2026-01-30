"""
Visual Demo of Parking Module
Creates a sample parking lot image with slot detection
"""
import cv2
import numpy as np
import sys
sys.path.append('/home/archie/Projects/code-crusaders-samved/cv-module')

from parking_module import ParkingManager

# Create a blank image (parking lot background)
img = np.ones((720, 1280, 3), dtype=np.uint8) * 80  # Gray background

# Add parking lot markings
cv2.putText(img, "SOLAPUR MUNICIPAL CORPORATION", (350, 50), 
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
cv2.putText(img, "Smart Parking Demo", (480, 90), 
            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 1)

# Draw parking lot boundary
cv2.rectangle(img, (50, 120), (1230, 680), (255, 255, 255), 3)

# Initialize parking manager
manager = ParkingManager(location="SMC_Demo_Parking")
manager.auto_define_grid_slots(
    frame_width=1280,
    frame_height=720,
    rows=2,
    cols=3,
    start_x=150,
    start_y=200,
    slot_width=300,
    slot_height=180,
    gap_x=40,
    gap_y=60
)

# Simulate some parked vehicles (centroids)
parked_vehicles = [
    {"track_id": 101, "centroid": (300, 290), "bbox": (250, 250, 350, 330)},  # Slot 1
    {"track_id": 102, "centroid": (690, 290), "bbox": (640, 250, 740, 330)},  # Slot 3
    {"track_id": 103, "centroid": (300, 530), "bbox": (250, 490, 350, 570)},  # Slot 4
    {"track_id": 104, "centroid": (1030, 530), "bbox": (980, 490, 1080, 570)}, # Slot 6
]

# Draw simple cars on the image
for vehicle in parked_vehicles:
    x1, y1, x2, y2 = vehicle["bbox"]
    cv2.rectangle(img, (x1, y1), (x2, y2), (50, 50, 200), -1)  # Car body
    cv2.rectangle(img, (x1, y1), (x2, y2), (30, 30, 150), 2)   # Car outline
    cx, cy = vehicle["centroid"]
    cv2.circle(img, (cx, cy), 5, (0, 255, 255), -1)  # Centroid marker

# Check occupancy
manager.check_slot_occupancy(parked_vehicles)

# Draw parking slots on the image
img = manager.draw_slots_on_frame(img)

# Add legend
cv2.rectangle(img, (50, 650), (200, 705), (255, 255, 255), -1)
cv2.rectangle(img, (60, 660), (90, 680), (0, 255, 0), -1)
cv2.putText(img, "Available", (100, 675), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
cv2.rectangle(img, (60, 685), (90, 700), (0, 0, 255), -1)
cv2.putText(img, "Occupied", (100, 697), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)

# Get summary
summary = manager.get_availability_summary()

# Add summary text
info_text = [
    f"Location: {summary['location']}",
    f"Total Slots: {summary['total_slots']}",
    f"Available: {summary['available_slots']}",
    f"Occupied: {summary['occupied_slots']}",
    f"Occupancy: {summary['occupancy_rate']:.1f}%"
]

y_pos = 160
for text in info_text:
    cv2.putText(img, text, (900, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 
                0.6, (255, 255, 0), 2)
    y_pos += 30

# Save the image
output_path = '/home/archie/Projects/code-crusaders-samved/parking_demo_output.jpg'
cv2.imwrite(output_path, img)

print("\n" + "="*60)
print("✅ PARKING VISUALIZATION CREATED!")
print("="*60)
print(f"\n📁 Saved to: {output_path}")
print(f"\n📊 Summary:")
print(f"   Total Slots:  {summary['total_slots']}")
print(f"   Available:    {summary['available_slots']} 🟢")
print(f"   Occupied:     {summary['occupied_slots']} 🔴")
print(f"   Occupancy:    {summary['occupancy_rate']:.1f}%")
print("\n💡 Open the image to see the parking slot detection!")
print("="*60 + "\n")
