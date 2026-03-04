import time
from dronekit import connect

# Mission Planner SITL default address
connection_string = "tcp:127.0.0.1:5763"

vehicle = connect(connection_string, wait_ready=True)
print("Connected to vehicle:", vehicle)

time.sleep(1)

for i in range(20):
    print('\nTime:', round(time.time()))
    print('Mode:', vehicle.mode)
    print('Battery:', vehicle.battery)
    print('Location:', vehicle.location)
    print('Attitude:', vehicle.attitude)
    print('Velocity:', vehicle.velocity)
    print('Groundspeed:', vehicle.groundspeed)
    time.sleep(1)

print('Connection test complete')
vehicle.close()
exit()