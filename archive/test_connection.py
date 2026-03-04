"""
Quick test to verify DroneKit can connect to SITL
Run this BEFORE the full Agno agent to ensure everything works
"""
from dronekit import connect
import time

print("🔍 Testing DroneKit connection to SITL...")
print("   Connecting to tcp:127.0.0.1:5763...")

try:
    # Attempt connection with timeout
    vehicle = connect('tcp:127.0.0.1:5763', wait_ready=True, timeout=10)
    
    print("\n✅ CONNECTION SUCCESSFUL!\n")
    
    # Display basic info
    print("Vehicle Information:")
    print(f"  Mode: {vehicle.mode.name}")
    print(f"  Armed: {vehicle.armed}")
    print(f"  GPS Fix: {vehicle.gps_0.fix_type}")
    print(f"  Satellites: {vehicle.gps_0.satellites_visible}")
    
    # Get location
    loc = vehicle.location.global_relative_frame
    print(f"\nCurrent Position:")
    print(f"  Latitude: {loc.lat:.6f}°")
    print(f"  Longitude: {loc.lon:.6f}°")
    print(f"  Altitude: {loc.alt:.2f}m")
    
    print(f"\nBattery:")
    print(f"  Voltage: {vehicle.battery.voltage}V")
    print(f"  Level: {vehicle.battery.level}%")
    
    print(f"\nHeading: {vehicle.heading}°")
    print(f"Ground Speed: {vehicle.groundspeed} m/s")
    
    print("\n✅ All systems nominal. Ready for Agno agent!")
    
    # Cleanup
    vehicle.close()
    print("\n🔌 Connection closed.\n")
    
except Exception as e:
    print(f"\n❌ CONNECTION FAILED!")
    print(f"   Error: {e}\n")
    print("Troubleshooting:")
    print("  1. Is Mission Planner SITL running?")
    print("  2. Is it connected to tcp:127.0.0.1:5763?")
    print("  3. Check Windows Firewall settings")
    print("  4. Try restarting SITL\n")
