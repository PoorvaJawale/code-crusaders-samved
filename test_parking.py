"""
Quick Test Script for Parking Module
Run this to verify parking detection is working
"""
import cv2
import sys
sys.path.append('/home/archie/Projects/code-crusaders-samved/cv-module')

from parking_module import ParkingManager
from datetime import datetime

def test_parking_module():
    """Test parking module with simulated data"""
    
    print("=" * 60)
    print("🅿️  PARKING MODULE TEST")
    print("=" * 60)
    
    # Create parking manager
    manager = ParkingManager(location="Test_Parking_Lot")
    
    # Auto-generate parking slots (2x3 grid = 6 slots)
    print("\n1️⃣  Creating parking grid (2 rows x 3 cols = 6 slots)...")
    manager.auto_define_grid_slots(
        frame_width=1280,
        frame_height=720,
        rows=2,
        cols=3,
        start_x=100,
        start_y=150,
        slot_width=180,
        slot_height=100,
        gap_x=20,
        gap_y=20
    )
    
    print(f"   ✅ Created {len(manager.parking_slots)} parking slots")
    
    # Simulate tracked vehicles
    print("\n2️⃣  Simulating 3 parked vehicles...")
    simulated_vehicles = [
        {"track_id": 1, "centroid": (190, 200), "bbox": (150, 170, 230, 230)},  # Slot 1
        {"track_id": 2, "centroid": (410, 200), "bbox": (370, 170, 450, 230)},  # Slot 2
        {"track_id": 3, "centroid": (630, 280), "bbox": (590, 250, 670, 310)},  # Slot 6
    ]
    
    # Check occupancy
    status = manager.check_slot_occupancy(simulated_vehicles)
    
    # Print results
    print("\n3️⃣  Parking Slot Status:")
    print("   " + "-" * 50)
    for slot in manager.parking_slots:
        slot_id = slot["id"]
        slot_status = status[slot_id]["status"]
        icon = "🔴" if slot_status == "occupied" else "🟢"
        vehicle_id = status[slot_id].get("vehicle_id", "N/A")
        print(f"   Slot #{slot_id}: {icon} {slot_status.upper():<10} | Vehicle: {vehicle_id}")
    
    # Get summary
    summary = manager.get_availability_summary()
    print("\n4️⃣  Summary:")
    print("   " + "-" * 50)
    print(f"   Total Slots:     {summary['total_slots']}")
    print(f"   Available:       {summary['available_slots']} 🟢")
    print(f"   Occupied:        {summary['occupied_slots']} 🔴")
    print(f"   Occupancy Rate:  {summary['occupancy_rate']:.1f}%")
    
    # Test database save (will fail if MongoDB not running, that's OK)
    print("\n5️⃣  Testing database save...")
    try:
        manager.save_to_database()
        print("   ✅ Successfully saved to MongoDB!")
    except Exception as e:
        print(f"   ⚠️  MongoDB not running (expected): {type(e).__name__}")
        print("   💡 Start MongoDB to enable database features")
    
    print("\n" + "=" * 60)
    print("✅ PARKING MODULE TEST COMPLETE!")
    print("=" * 60)
    print("\n📝 Next Steps:")
    print("   1. Start MongoDB: sudo systemctl start mongodb")
    print("   2. Run detector with parking module integrated")
    print("   3. Open Streamlit dashboard: streamlit run dashboard_streamlit.py")
    print("\n")

if __name__ == "__main__":
    test_parking_module()
