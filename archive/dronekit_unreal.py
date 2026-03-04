"""
SITL Dronekit to Unreal Engine - Basic Example
This script connects to a SITL instance using Dronekit and sends vehicle data to Unreal Engine using a TCP relay.
The basic example is configured to match the bp_pythonPawn example in the Unreal Engine project: 
    https://github.com/igsxf22/python_unreal_relay
"""
# Fix for the error: AttributeError: module 'collections' has no attribute 'MutableMapping'
try:
  from dronekit import connect, VehicleMode, Vehicle, LocationGlobalRelative
except Exception as e:
  print("Applying run-time fix for Dronekit collections deprecation")
  from collections import abc
  import collections
  collections.MutableMapping = abc.MutableMapping

import time
import math

from dronekit import connect, VehicleMode, Vehicle, LocationGlobalRelative

import tcp_relay

def vehicle_to_unreal(vehicle, z_invert=True, scale=100):
    """
    Converts vehicle data to a dictionary and formats it for Unreal Engine.
    :param vehicle: The vehicle object from dronekit.
    :param z_invert: Invert the Z axis for local frame (default is True because Ardupilot uses NED).
    :param scale: The scale of the Unreal Engine world (default is 100, UE uses cm).
    """
    d = {}
    d["lat"] = vehicle.location.global_frame.lat
    d["lon"] = vehicle.location.global_frame.lon
    d["alt"] = vehicle.location.global_frame.alt
    d["n"] = vehicle.location.local_frame.north * scale
    d["e"] = vehicle.location.local_frame.east * scale
    d["d"] = vehicle.location.local_frame.down * scale
    if z_invert:
        d["d"] *= -1
    d["roll"] = vehicle.attitude.roll
    d["pitch"] = vehicle.attitude.pitch
    d["yaw"] = vehicle.attitude.yaw

    # Round based on required precision
    for k,v in d.items():
        if type(v) == float:
            if k in ["lat", "lon", "alt"]:
                d[k] = round(v, 8)
            elif k in ["n", "e", "d"]:
                d[k] = round(v, 3)
            elif k in ["roll", "pitch", "yaw"]:
                d[k] = round(math.degrees(v), 3)

    return d

# def create_servo_listener(self, name, message):
#     # Create DroneKit listener for SERVO_OUTPUT_RAW messages
#     for i in range(1, 9):
#         key = f'servo{i}_raw'
#         channel = getattr(message, key)
#         self.channels_out[i] = channel

if __name__ == "__main__":
    # Connect to the vehicle
    connection_string = 'tcp:127.0.0.1:5763'
    vehicle = connect(connection_string, wait_ready=True, baud=57600, rate=60)
    print("Vehicle Connected.")

    
    while not vehicle.location.local_frame.north:
        time.sleep(1)
        print("Waiting for location local_frame to be available...")
    print("Location local_frame is now available.")

    relay = tcp_relay.TCP_Relay()

    while True:

        # Send vehicle data to Unreal Engine
        data = vehicle_to_unreal(vehicle)

        # Create a blank list of fields
        fields = [0.] * relay.num_fields

        # Set location and rotation fields with vehicle local frame and attitude data
        fields[0] = data["n"]
        fields[1] = data["e"]
        fields[2] = data["d"]
        fields[3] = data["roll"]
        fields[4] = data["pitch"]
        fields[5] = data["yaw"]

        fields[6] = 0.0 # Mount0 roll
        fields[7] = 0.0 # Mount0 pitch
        fields[8] = 0.0 # Mount0 yaw

        fields[9] = 0.0 # Mount1 roll
        fields[10] = 0.0 # Mount1 pitch
        fields[11] = 0.0 # Mount1 yaw

        fields[12] = 0 # Camera index (0=Mount0, 1=Mount1)
        fields[13] = 80.0 # Camera FOV

        # Update the relay message with from the fields, relay will send this to Unreal Engine in its thread
        relay.message = tcp_relay.create_fields_string(fields)
        
        time.sleep(1/60)