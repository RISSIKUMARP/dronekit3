import time
from dronekit import connect, VehicleMode, LocationGlobalRelative

# Mission Planner SITL default address
connection_string = "tcp:127.0.0.1:5763"

vehicle = connect(connection_string, wait_ready=True)
print("Connected to vehicle:", vehicle)

time.sleep(1)
print('\nBegin DroneKit flight test.\n')

# Ensure GUIDED mode
if not vehicle.mode == VehicleMode("GUIDED"):
    print("Switching to GUIDED for takeoff")
    vehicle.mode = VehicleMode("GUIDED")
    time.sleep(1)

# Takeoff if not already airborne
if vehicle.location.global_relative_frame.alt < 1:
    print("Vehicle not airborne. Starting takeoff sequence.")
    vehicle.armed = True

    while not vehicle.armed:
        print("Arming vehicle...")
        time.sleep(1)
    print("Vehicle is armed.")
    time.sleep(1)

    print("Taking off to 10 meters...")
    vehicle.simple_takeoff(10)

    while vehicle.location.global_relative_frame.alt < 9:
        print(f'Taking off. Alt={round(vehicle.location.global_relative_frame.alt)}')
        time.sleep(1)
    print("Takeoff Complete")
    time.sleep(1)

# Cycle through modes
for m in ['AUTO', 'BRAKE', 'GUIDED']:
    vehicle.mode = VehicleMode(m)
    print("Vehicle mode changed to:", m)
    time.sleep(2)

# Move to a nearby coordinate
destination = LocationGlobalRelative(
    lat=vehicle.location.global_relative_frame.lat + 0.0002,
    lon=vehicle.location.global_relative_frame.lon + 0.0002,
    alt=vehicle.location.global_relative_frame.alt
)
print("New GUIDED destination:", destination)
vehicle.simple_goto(destination)
time.sleep(2)

while vehicle.airspeed > 0.2:
    print('Moving to destination...')
    time.sleep(2)

print('GoTo coordinate test complete')
time.sleep(1)

# Change altitude
print("New altitude target: 30 meters")
destination = LocationGlobalRelative(
    lat=vehicle.location.global_relative_frame.lat,
    lon=vehicle.location.global_relative_frame.lon,
    alt=30
)
vehicle.simple_goto(destination)

while abs(vehicle.location.global_relative_frame.alt - destination.alt) > 1:
    print("Moving to 30m Rel Alt. Current:", vehicle.location.global_relative_frame.alt)
    time.sleep(2)

print('Altitude test complete')
time.sleep(1)

# Return to launch
print('Returning to launch...')
vehicle.mode = VehicleMode('RTL')
time.sleep(1)

while vehicle.mode.name == 'RTL':
    if vehicle.location.global_relative_frame.alt < 1.0:
        break
    print('Returning to Launch...')
    time.sleep(2)

print('Vehicle landed.')
print('Connection test complete')
vehicle.close()
exit()