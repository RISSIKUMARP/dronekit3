"""
Agno Agent DroneKit Demo
Converted from basic_demo.py to use Agno framework

This demonstrates:
1. Converting DroneKit commands into Agno tools
2. Using Agno's agent loop instead of manual OpenAI calls
3. Natural language drone control with multi-turn conversation
"""
import os
import time
from typing import Literal, Optional

import agno
from dronekit import connect, VehicleMode, LocationGlobal, LocationGlobalRelative
from pymavlink import mavutil

# ============================================================================
# DRONEKIT CONNECTION SETUP
# ============================================================================

# Get API key (using OpenRouter for cost optimization)
if not os.environ.get("OPENROUTER_API_KEY"):
    os.environ["OPENROUTER_API_KEY"] = input("OpenRouter API key: ")

# Connect to vehicle - default Mission Planner SITL
connection_string = 'tcp:127.0.0.1:5763'
vehicle = connect(connection_string, wait_ready=True, baud=57600, rate=60)
vehicle.mode = "GUIDED"
print("✓ Vehicle Connected")
print(f"  Mode: {vehicle.mode.name}")
print(f"  Armed: {vehicle.armed}")
print(f"  Location: {vehicle.location.global_relative_frame}\n")


# ============================================================================
# AGNO TOOLS - DroneKit Commands as Functions
# ============================================================================

def get_telemetry() -> dict:
    """
    Get current vehicle telemetry data.
    
    Returns comprehensive status including position, altitude, battery,
    armed status, flight mode, and GPS info.
    
    Returns:
        dict: Current vehicle status
    """
    loc = vehicle.location.global_relative_frame
    return {
        "mode": vehicle.mode.name,
        "armed": vehicle.armed,
        "latitude": loc.lat,
        "longitude": loc.lon,
        "altitude_m": loc.alt,
        "heading_deg": vehicle.heading,
        "groundspeed_m_s": vehicle.groundspeed,
        "airspeed_m_s": vehicle.airspeed,
        "battery_voltage": vehicle.battery.voltage,
        "battery_level": vehicle.battery.level,
        "gps_fix": vehicle.gps_0.fix_type,
        "satellites": vehicle.gps_0.satellites_visible
    }


def arm_vehicle(arm: bool = True) -> dict:
    """
    Arm or disarm the vehicle.
    
    Args:
        arm: True to arm, False to disarm
        
    Returns:
        dict: Status with armed state
    """
    vehicle.armed = arm
    time.sleep(1)  # Wait for arm to take effect
    
    status = "armed" if vehicle.armed else "disarmed"
    return {
        "success": True,
        "armed": vehicle.armed,
        "message": f"Vehicle {status}"
    }


def set_mode(mode: Literal["GUIDED", "ALT_HOLD", "RTL", "AUTO", "STABILIZE", "LOITER"]) -> dict:
    """
    Set the vehicle flight mode.
    
    Args:
        mode: Target flight mode
        
    Returns:
        dict: Status with current mode
    """
    vehicle.mode = VehicleMode(mode)
    time.sleep(1)  # Wait for mode change
    
    return {
        "success": True,
        "mode": vehicle.mode.name,
        "message": f"Mode set to {vehicle.mode.name}"
    }


def takeoff(altitude_m: float = 10.0) -> dict:
    """
    Arm and takeoff to specified altitude.
    Vehicle must be in GUIDED mode.
    
    Args:
        altitude_m: Target altitude in meters (default 10m)
        
    Returns:
        dict: Status with target altitude
    """
    # Ensure vehicle is in GUIDED mode
    if vehicle.mode.name != "GUIDED":
        vehicle.mode = VehicleMode("GUIDED")
        time.sleep(1)
    
    # Arm if not already armed
    if not vehicle.armed:
        vehicle.armed = True
        # Wait for arming
        while not vehicle.armed:
            time.sleep(0.5)
    
    # Takeoff
    vehicle.simple_takeoff(altitude_m)
    
    return {
        "success": True,
        "target_altitude_m": altitude_m,
        "armed": vehicle.armed,
        "mode": vehicle.mode.name,
        "message": f"Taking off to {altitude_m}m"
    }


def goto_coordinates(
    latitude: float, 
    longitude: float, 
    altitude_m: Optional[float] = None,
    frame: Literal["Relative", "Global"] = "Relative"
) -> dict:
    """
    Navigate to GPS coordinates.
    
    Args:
        latitude: Target latitude in decimal degrees
        longitude: Target longitude in decimal degrees
        altitude_m: Target altitude in meters (optional, maintains current if None)
        frame: "Relative" for altitude above home, "Global" for MSL altitude
        
    Returns:
        dict: Navigation status with target coordinates
    """
    # Use current altitude if not specified
    if altitude_m is None:
        altitude_m = vehicle.location.global_relative_frame.alt
    
    # Create location based on frame
    if frame == "Relative":
        target = LocationGlobalRelative(latitude, longitude, altitude_m)
    else:
        target = LocationGlobal(latitude, longitude, altitude_m)
    
    vehicle.simple_goto(target)
    
    return {
        "success": True,
        "target_lat": latitude,
        "target_lon": longitude,
        "target_alt_m": altitude_m,
        "frame": frame,
        "message": f"Navigating to ({latitude:.6f}, {longitude:.6f}) at {altitude_m}m"
    }


def goto_local(
    forward_m: float = 0.0,
    right_m: float = 0.0,
    up_m: float = 0.0
) -> dict:
    """
    Move relative to current position in body frame.
    Forward/Right/Up are positive, Back/Left/Down are negative.
    Limited to 10 meters per axis for safety.
    
    Args:
        forward_m: Distance forward (negative for backward) in meters
        right_m: Distance right (negative for left) in meters  
        up_m: Distance up (negative for down) in meters
        
    Returns:
        dict: Movement status
    """
    # Safety limits
    max_distance = 10.0
    forward_m = max(-max_distance, min(max_distance, forward_m))
    right_m = max(-max_distance, min(max_distance, right_m))
    up_m = max(-max_distance, min(max_distance, up_m))
    
    # Create MAVLink message for body-frame movement
    msg = vehicle.message_factory.set_position_target_local_ned_encode(
        0, 0, 0, 
        mavutil.mavlink.MAV_FRAME_BODY_OFFSET_NED,
        0b0000111111000111,  # Position only
        0, 0, 0,  # x, y, z positions (not used in offset mode)
        forward_m, right_m, -up_m,  # velocities used as offsets, z is down
        0, 0, 0,  # accelerations
        0, 0  # yaw, yaw_rate
    )
    vehicle.send_mavlink(msg)
    
    return {
        "success": True,
        "forward_m": forward_m,
        "right_m": right_m,
        "up_m": up_m,
        "message": f"Moving: forward={forward_m}m, right={right_m}m, up={up_m}m"
    }


def set_heading(
    yaw_degrees: float,
    frame: Literal["Relative", "Global"] = "Relative"
) -> dict:
    """
    Set vehicle heading/yaw.
    
    Args:
        yaw_degrees: Target heading
            - Relative: -180 to 180 degrees from current heading
            - Global: 0 to 360 degrees absolute (North=0, East=90)
        frame: "Relative" for heading change, "Global" for absolute heading
        
    Returns:
        dict: Heading command status
    """
    is_relative = 1 if frame == "Relative" else 0
    
    # Create MAVLink yaw command
    msg = vehicle.message_factory.command_long_encode(
        0, 0,  # target system, target component
        mavutil.mavlink.MAV_CMD_CONDITION_YAW,  # command
        0,  # confirmation
        yaw_degrees,  # param 1: target angle
        0,  # param 2: yaw speed (0 = max)
        1,  # param 3: direction (1=CW, -1=CCW)
        is_relative,  # param 4: 0=absolute, 1=relative
        0, 0, 0  # params 5-7 (unused)
    )
    vehicle.send_mavlink(msg)
    
    return {
        "success": True,
        "yaw_degrees": yaw_degrees,
        "frame": frame,
        "message": f"Setting heading to {yaw_degrees}° ({frame})"
    }


def land() -> dict:
    """
    Land the vehicle at current position.
    
    Returns:
        dict: Landing status
    """
    vehicle.mode = VehicleMode("LAND")
    
    return {
        "success": True,
        "mode": vehicle.mode.name,
        "message": "Landing initiated"
    }


def return_to_launch() -> dict:
    """
    Return to launch point and land.
    
    Returns:
        dict: RTL status
    """
    vehicle.mode = VehicleMode("RTL")
    
    return {
        "success": True,
        "mode": vehicle.mode.name,
        "message": "Returning to launch"
    }


# ============================================================================
# AGNO AGENT CONFIGURATION
# ============================================================================

agent = agno.Agent(
    name="DroneAgent",
    model=agno.OpenRouterModel(id="anthropic/claude-3.5-sonnet"),
    
    # All DroneKit commands as tools
    tools=[
        get_telemetry,
        arm_vehicle,
        set_mode,
        takeoff,
        goto_coordinates,
        goto_local,
        set_heading,
        land,
        return_to_launch
    ],
    
    instructions="""You are an autonomous drone pilot agent controlling a real drone via DroneKit.

Your capabilities:
- Check telemetry (position, altitude, battery, GPS, mode)
- Arm/disarm the vehicle
- Change flight modes (GUIDED, RTL, LAND, etc.)
- Takeoff to specified altitude
- Navigate to GPS coordinates (lat/lon)
- Move relative to current position (forward/back, left/right, up/down)
- Change heading/yaw
- Land or return to launch

Safety protocol:
1. ALWAYS check telemetry before major operations
2. Ensure vehicle is armed before takeoff
3. Confirm GUIDED mode before autonomous commands
4. Monitor altitude and position during flight
5. Check battery level periodically
6. Use relative movements cautiously (max 10m per axis)

Communication style:
- Be concise and operational (like a pilot)
- Acknowledge commands clearly
- Report status after actions
- Alert on any issues or anomalies

When user gives a command:
1. Acknowledge the command
2. Check current status if needed
3. Execute the command(s)
4. Report the result
5. Provide next steps if appropriate
""",
    
    markdown=False,  # Plain text for console
    show_tool_calls=True,  # Show what the agent is doing
)


# ============================================================================
# MAIN INTERACTION LOOP
# ============================================================================

def main():
    """Main interaction loop with the Agno agent."""
    
    print("\n" + "="*70)
    print("AGNO DRONE AGENT - Interactive DroneKit Control")
    print("="*70)
    print("\nCommands you can try:")
    print("  - 'check status' or 'get telemetry'")
    print("  - 'arm the drone'")
    print("  - 'takeoff to 15 meters'")
    print("  - 'fly forward 5 meters'")
    print("  - 'turn left 90 degrees'")
    print("  - 'go to coordinates 38.9605, -77.3118 at 20 meters'")
    print("  - 'land' or 'return to launch'")
    print("\nType 'exit' to quit\n")
    print("="*70 + "\n")
    
    # Agent maintains conversation history automatically
    while True:
        try:
            user_input = input("\n🎮 Command: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Shutting down agent...")
                break
            
            if not user_input:
                continue
            
            # Get agent response
            print()  # Blank line for readability
            start_time = time.time()
            
            # Agno handles the entire conversation flow
            response = agent.run(user_input)
            
            latency = time.time() - start_time
            
            # Print response
            print(f"\n🤖 Agent: {response.content}")
            print(f"\n⏱️  Latency: {latency:.2f}s")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Shutting down...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            continue
    
    # Cleanup
    print("\n🔌 Closing vehicle connection...")
    vehicle.close()
    print("✓ Done!\n")


if __name__ == "__main__":
    main()
